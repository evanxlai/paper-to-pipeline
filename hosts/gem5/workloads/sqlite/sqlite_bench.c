/*
 * sqlite_bench: run a bundled SQL script against an in-memory database.
 *
 *     sqlite_bench SCRIPT N
 *
 * SCRIPT is a file name relative to the working directory, which the
 * manifest sets to data/sqlite. N is the size knob. The driver stores it
 * in a one-row table, p2p_param(n), before the script runs, and the script
 * sizes its generated tables from it.
 *
 * The driver runs the script one statement at a time and prints every
 * result row, with columns joined by '|' as the sqlite3 shell does. A row
 * whose first column is the text 'FAIL' marks a failed check. Exit 0 only
 * when every statement succeeded and no check failed.
 *
 * Why a driver and not the sqlite3 shell: the shell reads ~/.sqliterc and
 * several environment variables. This driver reads one file and nothing
 * else. The build also compiles SQLite so that it cannot read the clock or
 * /dev/urandom behind the script's back:
 *   SQLITE_OMIT_RANDOMNESS  the PRNG seed is all zeros, not /dev/urandom
 *   SQLITE_TEMP_STORE=3     temporary tables and sorts stay in memory, so
 *                           SQLite never creates a temp file
 *   SQLITE_THREADSAFE=0     no mutexes and no threads
 * The script itself never calls random(), randomblob() or the date and
 * time functions with 'now'.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "sqlite3.h"

/* Read the whole script. SQL files here are a few KiB, so one buffer is
 * simpler than streaming. */
static char *read_file(const char *path) {
    FILE *f = fopen(path, "rb");
    if (f == NULL)
        return NULL;
    size_t cap = 4096, len = 0;
    char *buf = malloc(cap);
    size_t got;
    while (buf && (got = fread(buf + len, 1, cap - len - 1, f)) > 0) {
        len += got;
        if (cap - len - 1 == 0) {
            char *bigger = realloc(buf, cap * 2);
            if (bigger == NULL) {
                free(buf);
                buf = NULL;
                break;
            }
            buf = bigger;
            cap *= 2;
        }
    }
    fclose(f);
    if (buf)
        buf[len] = '\0';
    return buf;
}

int main(int argc, char **argv) {
    char *end = NULL;
    long n = argc == 3 ? strtol(argv[2], &end, 10) : 0;
    if (argc != 3 || *end != '\0' || n <= 0) {
        fprintf(stderr, "usage: sqlite_bench SCRIPT N\n");
        return 2;
    }
    char *sql = read_file(argv[1]);
    if (sql == NULL) {
        printf("sqlite_bench: cannot read %s\nFAIL\n", argv[1]);
        return 2;
    }

    sqlite3 *db = NULL;
    if (sqlite3_open(":memory:", &db) != SQLITE_OK) {
        printf("sqlite_bench: cannot open a database\nFAIL\n");
        return 2;
    }
    char param[96];
    snprintf(param, sizeof param,
             "CREATE TABLE p2p_param(n INTEGER); "
             "INSERT INTO p2p_param VALUES(%ld);", n);
    if (sqlite3_exec(db, param, NULL, NULL, NULL) != SQLITE_OK) {
        printf("sqlite_bench: %s\nFAIL\n", sqlite3_errmsg(db));
        return 2;
    }

    int ok = 1;
    const char *next = sql;
    while (ok && *next) {
        sqlite3_stmt *stmt = NULL;
        const char *tail = NULL;
        if (sqlite3_prepare_v2(db, next, -1, &stmt, &tail) != SQLITE_OK) {
            printf("sqlite_bench: %s\n", sqlite3_errmsg(db));
            ok = 0;
            break;
        }
        next = tail;
        if (stmt == NULL)  /* only whitespace or a comment was left */
            continue;
        int rc;
        while ((rc = sqlite3_step(stmt)) == SQLITE_ROW) {
            int cols = sqlite3_column_count(stmt);
            for (int i = 0; i < cols; i++) {
                const unsigned char *v = sqlite3_column_text(stmt, i);
                printf("%s%s", i ? "|" : "", v ? (const char *)v : "NULL");
            }
            printf("\n");
            const unsigned char *first = sqlite3_column_text(stmt, 0);
            if (first && strcmp((const char *)first, "FAIL") == 0)
                ok = 0;
        }
        if (rc != SQLITE_DONE) {
            printf("sqlite_bench: %s\n", sqlite3_errmsg(db));
            ok = 0;
        }
        sqlite3_finalize(stmt);
    }

    sqlite3_close(db);
    free(sql);
    printf("%s\n", ok ? "PASS" : "FAIL");
    return ok ? 0 : 1;
}
