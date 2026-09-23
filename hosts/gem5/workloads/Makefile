# Compiles the gem5 workload programs as static aarch64 Linux binaries.
#
# Do not run this directly. scripts/build_gem5_workloads.sh downloads and
# checks the sources, extracts and patches them into SRC, and then runs
#
#     make -f hosts/gem5/workloads/Makefile -j4 SRC=... OBJ=... BIN=...
#
# SRC  extracted, patched sources: bzip2/ zstd/ lua/ sqlite/ gapbs/
# OBJ  scratch space for objects and archives
# BIN  where the finished programs go
#
# CROSS=aarch64-linux-gnu- by default. The build script sets CROSS= (empty)
# for its optional native x86-64 build. That build compiles the same
# sources for the head, which gives an independent answer to compare the
# aarch64 output with.
#
# Every program is single-threaded. No file here passes -fopenmp or
# -pthread, zstd is built without ZSTD_MULTITHREAD, and SQLite is built
# with SQLITE_THREADSAFE=0.

HERE := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
CROSS ?= aarch64-linux-gnu-
CC := $(CROSS)gcc
CXX := $(CROSS)g++
AR := $(CROSS)ar

# -O2 everywhere, as the brief asks, even where upstream defaults to -O3
# (GAPBS, zstd). One optimisation level keeps the code shape comparable
# across the set.
OPT := -O2
LDFLAGS := -static

ifeq ($(strip $(SRC)),)
$(error SRC is not set; run scripts/build_gem5_workloads.sh)
endif

GAPBS_KERNELS := bfs cc pr sssp bc tc
PROGRAMS := bzip2_roundtrip zstd_roundtrip lua_bench sqlite_bench \
            $(addprefix gapbs_,$(GAPBS_KERNELS))

.PHONY: all
all: $(addprefix $(BIN)/,$(PROGRAMS)) $(OBJ)/gapbs_converter

$(BIN) $(OBJ):
	mkdir -p $@

# ------------------------------------------------------------------ bzip2
# The library files of the upstream Makefile's libbz2.a, and nothing from
# the bzip2 program itself.
BZ2_NAMES := blocksort huffman crctable randtable compress decompress bzlib
BZ2_OBJS := $(patsubst %,$(OBJ)/bzip2/%.o,$(BZ2_NAMES))

$(OBJ)/bzip2/%.o: $(SRC)/bzip2/%.c
	@mkdir -p $(@D)
	$(CC) $(OPT) -Wall -D_FILE_OFFSET_BITS=64 -c $< -o $@

$(OBJ)/libbz2.a: $(BZ2_OBJS)
	$(AR) rcs $@ $^

$(BIN)/bzip2_roundtrip: $(HERE)bzip2/bzip2_roundtrip.c \
                        $(HERE)common/textgen.h $(OBJ)/libbz2.a | $(BIN)
	$(CC) $(OPT) -Wall -I$(SRC)/bzip2 -I$(HERE)common $< \
	    $(OBJ)/libbz2.a $(LDFLAGS) -o $@

# ------------------------------------------------------------------- zstd
# lib/common, lib/compress and lib/decompress: the single-threaded core.
# The dictionary builder and the legacy decoders stay out.
# ZSTD_DISABLE_ASM only matters for the native x86-64 build, where zstd
# would otherwise want its hand-written decoder (a .S file this build does
# not assemble). There is no aarch64 assembly to disable.
ZSTD_SRCS := $(wildcard $(SRC)/zstd/lib/common/*.c \
                        $(SRC)/zstd/lib/compress/*.c \
                        $(SRC)/zstd/lib/decompress/*.c)
ZSTD_OBJS := $(patsubst $(SRC)/zstd/lib/%.c,$(OBJ)/zstd/%.o,$(ZSTD_SRCS))
ZSTD_DEFS := -DXXH_NAMESPACE=ZSTD_ -DZSTD_LEGACY_SUPPORT=0 -DZSTD_DISABLE_ASM

$(OBJ)/zstd/%.o: $(SRC)/zstd/lib/%.c
	@mkdir -p $(@D)
	$(CC) $(OPT) -Wall $(ZSTD_DEFS) -I$(SRC)/zstd/lib \
	    -I$(SRC)/zstd/lib/common -c $< -o $@

$(OBJ)/libzstd.a: $(ZSTD_OBJS)
	$(AR) rcs $@ $^

$(BIN)/zstd_roundtrip: $(HERE)zstd/zstd_roundtrip.c \
                       $(HERE)common/textgen.h $(OBJ)/libzstd.a | $(BIN)
	$(CC) $(OPT) -Wall -I$(SRC)/zstd/lib -I$(HERE)common $< \
	    $(OBJ)/libzstd.a $(LDFLAGS) -o $@

# -------------------------------------------------------------------- Lua
# Every file of liblua.a, built with the upstream "generic" flags plus two
# hooks that Lua lets a build override. Both default to reading the clock:
#   luai_makeseed(L)    the string hash seed. A fixed seed gives every
#                       run the same table layout.
#   l_randomizePivot()  the table.sort pivot salt. The ~0 comes from the
#                       comment on that hook in ltablib.c.
# p2p.patch fixes the third clock read, math's startup seed.
# The archive lets the link pull in only what lua_bench calls, so the io,
# os, package and debug libraries never reach the binary.
LUA_NAMES := lapi lcode lctype ldebug ldo ldump lfunc lgc llex lmem \
             lobject lopcodes lparser lstate lstring ltable ltm lundump \
             lvm lzio lauxlib lbaselib lcorolib ldblib liolib lmathlib \
             loadlib loslib lstrlib ltablib lutf8lib linit
LUA_OBJS := $(patsubst %,$(OBJ)/lua/%.o,$(LUA_NAMES))
LUA_DEFS := -DLUA_COMPAT_5_3 '-Dluai_makeseed(L)=0x2545F491u' \
            '-Dl_randomizePivot()=(~0u)'

$(OBJ)/lua/%.o: $(SRC)/lua/src/%.c
	@mkdir -p $(@D)
	$(CC) $(OPT) -Wall -Wextra $(LUA_DEFS) -c $< -o $@

$(OBJ)/liblua.a: $(LUA_OBJS)
	$(AR) rcs $@ $^

$(BIN)/lua_bench: $(HERE)lua/lua_bench.c $(OBJ)/liblua.a | $(BIN)
	$(CC) $(OPT) -Wall -I$(SRC)/lua/src $< $(OBJ)/liblua.a -lm \
	    $(LDFLAGS) -o $@

# ----------------------------------------------------------------- SQLite
# The amalgamation, one 9 MB file and the longest compile here. The
# options remove every path by which SQLite could read the clock,
# /dev/urandom or a temp directory. sqlite_bench.c explains each one.
SQLITE_DEFS := -DSQLITE_THREADSAFE=0 -DSQLITE_OMIT_LOAD_EXTENSION \
               -DSQLITE_OMIT_RANDOMNESS -DSQLITE_TEMP_STORE=3 \
               -DSQLITE_DEFAULT_MEMSTATUS=0 -DSQLITE_DQS=0

$(OBJ)/sqlite3.o: $(SRC)/sqlite/sqlite3.c | $(OBJ)
	$(CC) $(OPT) $(SQLITE_DEFS) -c $< -o $@

$(BIN)/sqlite_bench: $(HERE)sqlite/sqlite_bench.c $(OBJ)/sqlite3.o | $(BIN)
	$(CC) $(OPT) -Wall $(SQLITE_DEFS) -I$(SRC)/sqlite $< $(OBJ)/sqlite3.o \
	    -lm $(LDFLAGS) -o $@

# ------------------------------------------------------------------ GAPBS
# The upstream rule (Makefile: "% : src/%.cc src/*.h") with SERIAL=1, so
# no -fopenmp. The kernels then run their "#pragma omp" loops serially,
# and -Wno-unknown-pragmas keeps that from filling the log.
GAPBS_HDRS := $(wildcard $(SRC)/gapbs/src/*.h)

$(BIN)/gapbs_%: $(SRC)/gapbs/src/%.cc $(GAPBS_HDRS) | $(BIN)
	$(CXX) -std=c++11 $(OPT) -Wall -Wno-unknown-pragmas $< $(LDFLAGS) \
	    -o $@

# GAPBS's own converter. It is a build tool, not a workload, so it goes to
# OBJ and never into the payload. The build script runs it under qemu to
# write the graph files in data/gapbs/. Running the aarch64 build means the
# same code writes a graph file and reads it back on gem5.
$(OBJ)/gapbs_converter: $(SRC)/gapbs/src/converter.cc $(GAPBS_HDRS) | $(OBJ)
	$(CXX) -std=c++11 $(OPT) -Wall -Wno-unknown-pragmas $< $(LDFLAGS) \
	    -o $@
