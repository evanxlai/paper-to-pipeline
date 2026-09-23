/*
 * lua_bench: run one bundled Lua benchmark script at a given size.
 *
 *     lua_bench SCRIPT N [M]
 *
 * SCRIPT is a file name relative to the working directory, which the
 * manifest sets to data/lua. N is the script's size knob, and the script
 * sees it as the global integer N. M is an optional second knob (global M,
 * default 1) for scripts whose work jumps too far between one N and the
 * next. fannkuch_redux.lua is one: its work grows as N!, so it repeats
 * the run M times instead. The script returns true when its own check
 * passed. Exit 0 only when it returned true.
 *
 * Why a driver and not the stock lua interpreter: lua.c reads LUA_INIT and
 * LUA_PATH from the environment, and the package library does the same.
 * This driver opens only the libraries the scripts need (base, coroutine,
 * table, string, math and utf8) and none of io, os, package or debug. So
 * nothing the script does can depend on the environment, the clock or the
 * file system beyond the one script file. The interpreter loop, the
 * garbage collector and the string and table code are the real Lua 5.4.
 *
 * Output: whatever the script prints, then PASS or FAIL.
 */
#include <stdio.h>
#include <stdlib.h>

#include "lauxlib.h"
#include "lua.h"
#include "lualib.h"

static const luaL_Reg p2p_libs[] = {
    {LUA_GNAME, luaopen_base},
    {LUA_COLIBNAME, luaopen_coroutine},
    {LUA_TABLIBNAME, luaopen_table},
    {LUA_STRLIBNAME, luaopen_string},
    {LUA_MATHLIBNAME, luaopen_math},
    {LUA_UTF8LIBNAME, luaopen_utf8},
    {NULL, NULL},
};

int main(int argc, char **argv) {
    char *end_n = NULL, *end_m = NULL;
    long n = argc >= 3 ? strtol(argv[2], &end_n, 10) : 0;
    long m = argc == 4 ? strtol(argv[3], &end_m, 10) : 1;
    if (argc < 3 || argc > 4 || *end_n != '\0' || n <= 0 ||
        (end_m && *end_m != '\0') || m <= 0) {
        fprintf(stderr, "usage: lua_bench SCRIPT N [M]\n");
        return 2;
    }

    lua_State *L = luaL_newstate();
    if (L == NULL) {
        fprintf(stderr, "lua_bench: cannot create a Lua state\n");
        return 2;
    }
    for (const luaL_Reg *lib = p2p_libs; lib->func; lib++) {
        luaL_requiref(L, lib->name, lib->func, 1);
        lua_pop(L, 1);
    }
    lua_pushinteger(L, (lua_Integer)n);
    lua_setglobal(L, "N");
    lua_pushinteger(L, (lua_Integer)m);
    lua_setglobal(L, "M");

    int ok = 0;
    if (luaL_loadfile(L, argv[1]) != LUA_OK ||
        lua_pcall(L, 0, 1, 0) != LUA_OK) {
        /* A syntax error, a missing file or a runtime error all land here,
         * with Lua's own message on the stack. */
        printf("lua_bench error: %s\n", lua_tostring(L, -1));
    } else {
        ok = lua_toboolean(L, -1);
    }
    lua_close(L);
    printf("%s\n", ok ? "PASS" : "FAIL");
    return ok ? 0 : 1;
}
