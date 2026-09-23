/*
 * zstd_roundtrip: compress generated text with libzstd, decompress it, and
 * check that the bytes came back.
 *
 *     zstd_roundtrip KIB LEVEL
 *
 * KIB is the input size in KiB, the size knob in workloads.json. LEVEL is
 * the zstd compression level (1 to 19), the -1 to -19 of the zstd command.
 *
 * Why the level matters here: at the default level 3 zstd is so fast that
 * generating the input is over a third of the run (measured under qemu:
 * 36 instructions per byte for the generator and its hash, 94 per byte for
 * the whole run). At higher levels zstd searches for matches with lazy and
 * binary-tree match finders. Those are branch-heavy loops over the input.
 * At level 12 the whole run costs about 480 instructions per byte, so the
 * generator falls under a tenth of it.
 *
 * zstd picks its parameters from the level and from the input size, in
 * tiers: up to 16 KiB, up to 128 KiB, up to 256 KiB, and larger (see
 * lib/compress/clevels.h). Level 12 means the btlazy2 match finder in the
 * 128 KiB tier but btopt in the 16 KiB tier. So the manifest keeps both
 * zstd sizes above 16 KiB and at most 128 KiB, and the two sizes then run
 * the same code. This file only refuses levels zstd rejects.
 *
 * Why a driver and not the zstd program: the same reasons as
 * bzip2_roundtrip.c. It needs no input file, and its exit code carries the
 * check. The library is built without ZSTD_MULTITHREAD, so it never
 * starts a thread.
 *
 * Output: one summary line and then PASS or FAIL. Exit 0 only on PASS.
 */
#include <stdio.h>
#include <stdlib.h>

#include "textgen.h"
#include "zstd.h"

/* Any fixed value works. Changing it changes every checksum in
 * expected.json, so it stays put. */
#define P2P_SEED 0x5eed25d1u

int main(int argc, char **argv) {
    unsigned long kib = argc == 3 ? p2p_parse_positive(argv[1]) : 0;
    unsigned long level = argc == 3 ? p2p_parse_positive(argv[2]) : 0;
    if (kib == 0 || level < 1 || level > 19) {
        fprintf(stderr, "usage: zstd_roundtrip KIB LEVEL(1-19)\n");
        return 2;
    }

    size_t n = kib * 1024;
    size_t cap = ZSTD_compressBound(n);
    unsigned char *src = malloc(n);
    unsigned char *comp = malloc(cap);
    unsigned char *back = malloc(n);
    ZSTD_CCtx *cctx = ZSTD_createCCtx();
    ZSTD_DCtx *dctx = ZSTD_createDCtx();
    if (!src || !comp || !back || !cctx || !dctx) {
        fprintf(stderr, "zstd_roundtrip: out of memory\n");
        return 2;
    }
    p2p_gen_text(src, n, P2P_SEED);

    size_t clen = ZSTD_compressCCtx(cctx, comp, cap, src, n, (int)level);
    if (ZSTD_isError(clen)) {
        printf("zstd_roundtrip compress failed: %s\nFAIL\n",
               ZSTD_getErrorName(clen));
        return 1;
    }

    size_t blen = ZSTD_decompressDCtx(dctx, back, n, comp, clen);
    int ok = !ZSTD_isError(blen) && blen == n && memcmp(src, back, n) == 0;

    printf("zstd_roundtrip bytes=%zu level=%lu compressed=%zu "
           "input_fnv=%016llx compressed_fnv=%016llx\n",
           n, level, clen, (unsigned long long)p2p_fnv1a(src, n),
           (unsigned long long)p2p_fnv1a(comp, clen));
    printf("%s\n", ok ? "PASS" : "FAIL");
    ZSTD_freeCCtx(cctx);
    ZSTD_freeDCtx(dctx);
    free(src);
    free(comp);
    free(back);
    return ok ? 0 : 1;
}
