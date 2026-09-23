/*
 * bzip2_roundtrip: compress generated text with libbz2, decompress it, and
 * check that the bytes came back.
 *
 *     bzip2_roundtrip KIB BLOCK
 *
 * KIB is the input size in KiB, the size knob in workloads.json. BLOCK is
 * bzip2's block size in units of 100 kB (1 to 9, the -1 to -9 of the
 * bzip2 command). With BLOCK=1 an input over 100 kB spans several blocks,
 * so the run covers the block boundary code too.
 *
 * Why a driver and not the bzip2 program: the program reads a file and
 * writes a file, which puts input on the node and makes "did it work"
 * a second step. This driver makes its own input, checks its own output,
 * and says so in its exit code, which is the only signal the gem5 run
 * scripts read. The work in between is the real libbz2: the block sort,
 * the MTF and Huffman stages on the way in, and the inverse on the way out.
 *
 * Output: one summary line and then PASS or FAIL. Exit 0 only on PASS.
 */
#include <stdio.h>
#include <stdlib.h>

#include "bzlib.h"
#include "textgen.h"

/* Any fixed value works. Changing it changes every checksum in
 * expected.json, so it stays put. */
#define P2P_SEED 0x5eed0b21u

int main(int argc, char **argv) {
    unsigned long kib = argc == 3 ? p2p_parse_positive(argv[1]) : 0;
    unsigned long block = argc == 3 ? p2p_parse_positive(argv[2]) : 0;
    if (kib == 0 || block < 1 || block > 9) {
        fprintf(stderr, "usage: bzip2_roundtrip KIB BLOCK(1-9)\n");
        return 2;
    }

    size_t n = kib * 1024;
    /* bzlib.h's documented worst case: 1% larger plus 600 bytes. */
    unsigned int cap = (unsigned int)(n + n / 100 + 600);
    unsigned char *src = malloc(n);
    unsigned char *comp = malloc(cap);
    unsigned char *back = malloc(n);
    if (!src || !comp || !back) {
        fprintf(stderr, "bzip2_roundtrip: out of memory\n");
        return 2;
    }
    p2p_gen_text(src, n, P2P_SEED);

    /* verbosity 0: no stderr chatter. workFactor 30 is the library
     * default, so the fallback sort triggers on the same inputs it would
     * for a real user. */
    unsigned int clen = cap;
    int rc = BZ2_bzBuffToBuffCompress((char *)comp, &clen, (char *)src,
                                      (unsigned int)n, (int)block, 0, 30);
    if (rc != BZ_OK) {
        printf("bzip2_roundtrip compress failed rc=%d\nFAIL\n", rc);
        return 1;
    }

    /* small=0: the fast decompressor, as the bzip2 program uses. */
    unsigned int blen = (unsigned int)n;
    rc = BZ2_bzBuffToBuffDecompress((char *)back, &blen, (char *)comp, clen,
                                    0, 0);
    int ok = rc == BZ_OK && blen == n && memcmp(src, back, n) == 0;

    printf("bzip2_roundtrip bytes=%zu block=%lu compressed=%u "
           "input_fnv=%016llx compressed_fnv=%016llx\n",
           n, block, clen, (unsigned long long)p2p_fnv1a(src, n),
           (unsigned long long)p2p_fnv1a(comp, clen));
    printf("%s\n", ok ? "PASS" : "FAIL");
    free(src);
    free(comp);
    free(back);
    return ok ? 0 : 1;
}
