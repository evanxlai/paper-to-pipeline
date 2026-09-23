#!/usr/bin/env bash
# Build the gem5 host's workloads on the head: static aarch64 Linux
# programs, their input files, and a check of each one under qemu.
#
#   scripts/build_gem5_workloads.sh [--jobs N] [--no-validate]
#       [--update-expected] [--count-insts] [--native-check]
#       [--only NAME ...]
#
# What it makes: third_party/gem5_workloads/{bin,data}/ (or
# $P2P_GEM5_WORKLOADS_DIR, as in loop/constants.py). bin/ holds the
# programs. data/ holds the Lua and SQL scripts and the GAPBS graph files,
# which this script generates (see "GAPBS graphs" below). The adapter packs
# that directory, the run scripts and hosts/gem5/workloads.json into one
# payload and unpacks it into GEM5_RUN_DIR/workloads/ on the gem5 node. Git
# ignores third_party/, so the binaries are never committed. This script is
# how anyone gets them back.
#
# Why build on the head and ship binaries: the head has the aarch64 cross
# toolchain and qemu to check the result, and one build shipped to the node
# means every run sees the same bytes. Why static: gem5's SE mode loads a
# dynamic binary only if the guest's loader and libraries are on the node,
# and they are not.
#
# Re-runnable: downloads are cached in third_party/gem5_workloads_src/ and
# checked against pinned checksums (or a pinned git commit) every time.
# The sources are extracted fresh into _build/ on every run, so a patch is
# never applied twice and a stale object never survives.
#
# Options:
#   --jobs N           parallel compile and check jobs (default 4, the
#                      head's vCPU count)
#   --no-validate      build and install only
#   --update-expected  record each workload's output as the expected output
#                      in hosts/gem5/workloads/expected.json. Use it after a
#                      deliberate change to a size or a program.
#   --count-insts      count each workload's guest instructions exactly under
#                      qemu (slow, about 0.4 M instructions per second per
#                      job) and write them to approx_insts in the manifest
#   --native-check     also build the programs for x86-64 and compare their
#                      output with the aarch64 output
#   --only NAME        check only these workloads (repeatable)
set -euo pipefail

START_S=$(date +%s)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
W="$ROOT/hosts/gem5/workloads"
MANIFEST="$ROOT/hosts/gem5/workloads.json"
EXPECTED="$W/expected.json"
CACHE="$ROOT/third_party/gem5_workloads_src"
BUILD="$CACHE/_build"
OUT="${P2P_GEM5_WORKLOADS_DIR:-$ROOT/third_party/gem5_workloads}"

JOBS=4
VALIDATE=1
CHECK_ARGS=()
NATIVE=0
ONLY=()
while [ $# -gt 0 ]; do
  case "$1" in
    --jobs) JOBS="$2"; shift 2 ;;
    --no-validate) VALIDATE=0; shift ;;
    --update-expected) CHECK_ARGS+=(--update-expected); shift ;;
    --count-insts) CHECK_ARGS+=(--count-insts); shift ;;
    --native-check) NATIVE=1; shift ;;
    --only) ONLY+=("$2"); shift 2 ;;
    -h|--help) sed -n '2,/^set -euo/p' "$0" | sed '$d; s/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $1 (see --help)" >&2; exit 2 ;;
  esac
done

# ------------------------------------------------------------ pinned sources
# Each version is the newest release of its line as of 2026-09-23. Each
# checksum is the one the project itself publishes, in the algorithm it
# publishes, so anyone can check a pin against the project's own page.
# GAPBS publishes no checksums, so it is pinned to a git commit instead.
# sourceware lists SHA-512 sums in https://sourceware.org/pub/bzip2/sha512.sum.
BZIP2_URL=https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz
BZIP2_SHA512=083f5e675d73f3233c7930ebe20425a533feedeaaa9d8cc86831312a6581cefbe6ed0d08d2fa89be81082f2a5abdabca8b3c080bf97218a1bd59dc118a30b9f3
# zstd publishes zstd-1.5.7.tar.gz.sha256 next to the release tarball.
ZSTD_URL=https://github.com/facebook/zstd/releases/download/v1.5.7/zstd-1.5.7.tar.gz
ZSTD_SHA256=eb33e51f49a15e023950cd7825ca74a4a2b43db8354825ac24fc1b7ee09e6fa3
# lua.org lists the SHA-256 of each tarball on https://www.lua.org/ftp/.
LUA_URL=https://www.lua.org/ftp/lua-5.4.9.tar.gz
LUA_SHA256=2335b6c582a52654f94612bf10d2f4672805d05329aa6568b1d8cd9e5c6fb8e6
# sqlite.org publishes SHA3-256, not SHA-256, on its download page.
SQLITE_URL=https://www.sqlite.org/2026/sqlite-amalgamation-3530400.zip
SQLITE_SHA3=628a44cfe82c66aed1ccbbe85a562d2e33ebe64b3288981ed76285612227934e
# GAPBS publishes no tarballs with checksums. Tag v1.5 is this commit.
GAPBS_REPO=https://github.com/sbeamer/gapbs
GAPBS_COMMIT=b5e3e19c2845f22fb338f4a4bc4b1ccee861d026

for tool in aarch64-linux-gnu-gcc aarch64-linux-gnu-g++ aarch64-linux-gnu-ar \
            qemu-aarch64-static file curl git patch python3 make; do
  command -v "$tool" >/dev/null || { echo "missing tool: $tool" >&2; exit 1; }
done

digest() {  # digest ALGO FILE -> hex digest
  python3 - "$1" "$2" <<'PY'
import hashlib, sys
h = hashlib.new(sys.argv[1])
with open(sys.argv[2], "rb") as f:
    for block in iter(lambda: f.read(1 << 20), b""):
        h.update(block)
print(h.hexdigest())
PY
}

fetch() {  # fetch URL ALGO DIGEST: download once, verify every time
  local url="$1" algo="$2" want="$3" file
  file="$CACHE/$(basename "$url")"
  if [ -f "$file" ] && [ "$(digest "$algo" "$file")" = "$want" ]; then
    return 0
  fi
  echo "fetch: $url"
  curl -fsSL --retry 3 -o "$file.part" "$url"
  local got
  got="$(digest "$algo" "$file.part")"
  if [ "$got" != "$want" ]; then
    rm -f "$file.part"
    echo "checksum mismatch for $url: $algo $got, pinned $want" >&2
    exit 1
  fi
  mv "$file.part" "$file"
}

mkdir -p "$CACHE"
fetch "$BZIP2_URL" sha512 "$BZIP2_SHA512"
fetch "$ZSTD_URL" sha256 "$ZSTD_SHA256"
fetch "$LUA_URL" sha256 "$LUA_SHA256"
fetch "$SQLITE_URL" sha3_256 "$SQLITE_SHA3"
if [ ! -d "$CACHE/gapbs/.git" ]; then
  echo "fetch: $GAPBS_REPO"
  git clone -q "$GAPBS_REPO" "$CACHE/gapbs"
fi
if ! git -C "$CACHE/gapbs" cat-file -e "$GAPBS_COMMIT^{commit}" 2>/dev/null; then
  git -C "$CACHE/gapbs" fetch -q origin
fi

# -------------------------------------------------- extract and patch, fresh
rm -rf "$BUILD"
mkdir -p "$BUILD/src"
S="$BUILD/src"
tar xzf "$CACHE/bzip2-1.0.8.tar.gz" -C "$S" && mv "$S/bzip2-1.0.8" "$S/bzip2"
tar xzf "$CACHE/zstd-1.5.7.tar.gz" -C "$S" && mv "$S/zstd-1.5.7" "$S/zstd"
tar xzf "$CACHE/lua-5.4.9.tar.gz" -C "$S" && mv "$S/lua-5.4.9" "$S/lua"
# The head has no unzip, and python3 is already required.
python3 -m zipfile -e "$CACHE/sqlite-amalgamation-3530400.zip" "$S"
mv "$S/sqlite-amalgamation-3530400" "$S/sqlite"
mkdir "$S/gapbs"
git -C "$CACHE/gapbs" archive "$GAPBS_COMMIT" | tar x -C "$S/gapbs"
# --fuzz=0: a patch that no longer fits exactly must stop the build, not
# land somewhere nearby.
patch -d "$S/gapbs" -p1 --forward --fuzz=0 --quiet < "$W/gapbs/p2p.patch"
patch -d "$S/lua" -p1 --forward --fuzz=0 --quiet < "$W/lua/p2p.patch"

# ------------------------------------------------------------------- build
BUILD_START_S=$(date +%s)
make -s -f "$W/Makefile" -j"$JOBS" SRC="$S" OBJ="$BUILD/obj-aarch64" \
  BIN="$BUILD/bin-aarch64"
if [ "$NATIVE" = 1 ]; then
  make -s -f "$W/Makefile" -j"$JOBS" CROSS= SRC="$S" OBJ="$BUILD/obj-native" \
    BIN="$BUILD/bin-native"
fi
BUILD_END_S=$(date +%s)

# ----------------------------------------------------------------- install
# Replace bin/ and data/ whole, so a program or input file that left the
# set does not linger in the payload.
rm -rf "$OUT/bin" "$OUT/data"
mkdir -p "$OUT/bin" "$OUT/data/lua" "$OUT/data/sqlite" "$OUT/data/gapbs"
cp "$BUILD"/bin-aarch64/* "$OUT/bin/"
cp "$W"/lua/*.lua "$OUT/data/lua/"
cp "$W/sqlite/bench.sql" "$OUT/data/sqlite/"

# ------------------------------------------------------------ GAPBS graphs
# The GAPBS entries read a graph file (-f) instead of generating one (-g).
# Measured under qemu at scale 10: generating and building the graph cost
# 9.2 M instructions, and one bfs trial cost 75 K. With -g, every GAPBS
# entry would mostly measure the same generator. So the build runs GAPBS's
# own converter once, with the same Kronecker generator and fixed seed that
# -g uses, and ships the graph. The manifest names each file
# kron_g<scale>.sg, or kron_g<scale>.wsg for a weighted graph (sssp). This
# step writes exactly the files the manifest names, so retuning a scale in
# workloads.json needs no edit here.
GRAPHS=$(python3 - "$MANIFEST" <<'PY'
import json, re, sys
doc = json.load(open(sys.argv[1]))
names = set()
for name, entry in doc["workloads"].items():
    if not entry["binary"].startswith("bin/gapbs_"):
        continue
    args = [str(a) for a in entry.get("args") or []]
    for i, arg in enumerate(args[:-1]):
        if arg == "-f":
            if not re.fullmatch(r"kron_g[0-9]+\.w?sg", args[i + 1]):
                sys.exit(f"{name}: graph {args[i + 1]!r} is not named "
                         "kron_g<scale>.sg or kron_g<scale>.wsg")
            names.add(args[i + 1])
print(" ".join(sorted(names)))
PY
)
for g in $GRAPHS; do
  scale="${g#kron_g}"
  scale="${scale%%.*}"
  weighted=()
  if [ "${g##*.}" = wsg ]; then weighted=(-w); fi
  env -i qemu-aarch64-static "$BUILD/obj-aarch64/gapbs_converter" \
    -g "$scale" "${weighted[@]}" -b "$OUT/data/gapbs/$g" \
    > "$BUILD/converter-$g.log"
done

# ------------------------------------------------------------------ validate
STATUS=0
if [ "$VALIDATE" = 1 ]; then
  if [ "$NATIVE" = 1 ]; then
    CHECK_ARGS+=(--native "$BUILD/bin-native")
  fi
  python3 "$W/check_workloads.py" --manifest "$MANIFEST" --payload "$OUT" \
    --expected "$EXPECTED" --jobs "$JOBS" "${CHECK_ARGS[@]}" "${ONLY[@]}" \
    || STATUS=$?
fi

# ------------------------------------------------------------------- summary
END_S=$(date +%s)
echo
echo "payload: $OUT"
# The SHA-256 prefix lets two heads compare their payloads file by file.
( cd "$OUT" && find bin data -type f | sort | while read -r f; do
    printf '  %-28s %9d bytes  sha256 %.16s\n' "$f" "$(stat -c %s "$f")" \
      "$(digest sha256 "$f")"
  done )
echo "compile: $((BUILD_END_S - BUILD_START_S)) s with -j$JOBS"
echo "total:   $((END_S - START_S)) s"
if [ "$VALIDATE" = 0 ]; then
  echo "validation skipped (--no-validate)"
elif [ "$STATUS" = 0 ]; then
  echo "validation: every workload passed under $(qemu-aarch64-static --version | head -1)"
else
  echo "validation FAILED; see the problems above" >&2
fi
exit "$STATUS"
