/*
 * Deterministic text-like input for the compression round trips.
 *
 * Why generate the input instead of shipping a corpus: a corpus is a file
 * someone licensed, and it comes in one size. This makes any number of
 * bytes from one fixed seed, and the bytes are identical on every machine,
 * so the size argument in workloads.json is the only knob the lead turns.
 *
 * Why text-like and not random bytes: random bytes do not compress, and
 * then bzip2 and zstd spend their time in a "store it raw" path that no
 * real user of either program exercises. Words drawn with a skewed pick
 * from a short list repeat the way English does. The match finders then
 * see matches of many lengths, and the entropy coders see a skewed
 * alphabet, which is where the data-dependent branches are.
 *
 * Nothing here reads the clock, the environment or /dev/urandom. The
 * guest's instruction stream must be the same with the feature on and off,
 * and gem5 answers every clock read with simulated time, which moves when
 * the predictor changes.
 */
#ifndef P2P_TEXTGEN_H
#define P2P_TEXTGEN_H

#include <stddef.h>
#include <stdint.h>
#include <string.h>

/* Knuth's MMIX LCG. The low bits of an LCG are weak, so callers take the
 * high 32 bits. Quality is not the point: the output has to be repeatable
 * and skewed, and it has to cost few instructions per byte so the
 * compressor, not the generator, dominates the run. */
typedef struct {
    uint64_t s;
} p2p_lcg;

static inline uint32_t p2p_lcg_next(p2p_lcg *g) {
    g->s = g->s * 6364136223846793005ULL + 1442695040888963407ULL;
    return (uint32_t)(g->s >> 32);
}

/* 128 common English words, most common first. p2p_pick_word() favours
 * the low indices, so the head of this list behaves like the frequent
 * words of real text and the tail like the rare ones. */
static const char *const p2p_words[] = {
    "the", "of", "and", "to", "in", "is", "that", "it",
    "was", "for", "on", "are", "as", "with", "his", "they",
    "at", "be", "this", "have", "from", "or", "one", "had",
    "by", "word", "but", "not", "what", "all", "were", "we",
    "when", "your", "can", "said", "there", "use", "an", "each",
    "which", "she", "do", "how", "their", "if", "will", "up",
    "other", "about", "out", "many", "then", "them", "these", "so",
    "some", "her", "would", "make", "like", "him", "into", "time",
    "has", "look", "two", "more", "write", "go", "see", "number",
    "no", "way", "could", "people", "my", "than", "first", "water",
    "been", "call", "who", "oil", "its", "now", "find", "long",
    "down", "day", "did", "get", "come", "made", "may", "part",
    "branch", "predictor", "register", "value", "history", "table",
    "counter", "pipeline", "cache", "memory", "instruction", "cycle",
    "statistical", "corrector", "confidence", "threshold", "loop",
    "global", "local", "path", "signature", "entry", "tag", "index",
    "update", "commit", "fetch", "decode", "retire", "squash", "bias",
    "ahead",
};

/* p2p_pick_word() masks with 127, so a short list would index past the
 * end and a long one would leave words unused. */
_Static_assert(sizeof(p2p_words) / sizeof(p2p_words[0]) == 128,
               "p2p_words must hold exactly 128 words");

/* Minimum of two uniform draws: P(i) falls linearly with i, a cheap
 * stand-in for Zipf's law. */
static inline unsigned p2p_pick_word(p2p_lcg *g) {
    unsigned a = p2p_lcg_next(g) & 127u;
    unsigned b = p2p_lcg_next(g) & 127u;
    return a < b ? a : b;
}

/* Append up to len bytes of s to buf at *pos, never past n. */
static inline void p2p_emit(unsigned char *buf, size_t n, size_t *pos,
                            const char *s, size_t len) {
    size_t room = n - *pos;
    if (len > room)
        len = room;
    memcpy(buf + *pos, s, len);
    *pos += len;
}

/* Fill buf[0..n) with sentences of 4 to 15 words. One word in 16 is a
 * number of 1 to 5 digits, which adds literal-heavy stretches that do not
 * repeat. Sentences end with a newline one time in four, so the text has
 * lines of uneven length, as prose does. */
static inline void p2p_gen_text(unsigned char *buf, size_t n, uint64_t seed) {
    p2p_lcg g = {seed};
    size_t pos = 0;
    unsigned in_sentence = 0;
    unsigned sentence_len = 4 + p2p_lcg_next(&g) % 12;
    char word[32];

    while (pos < n) {
        uint32_t r = p2p_lcg_next(&g);
        size_t len;
        if ((r & 15u) == 0) {
            unsigned digits = 1 + (r >> 4) % 5;
            uint32_t v = p2p_lcg_next(&g);
            for (len = 0; len < digits; len++) {
                word[len] = (char)('0' + v % 10);
                v /= 10;
            }
        } else {
            const char *w = p2p_words[p2p_pick_word(&g)];
            len = strlen(w);
            memcpy(word, w, len);
            if (in_sentence == 0 && word[0] >= 'a' && word[0] <= 'z')
                word[0] = (char)(word[0] - 'a' + 'A');
        }
        p2p_emit(buf, n, &pos, word, len);
        if (++in_sentence == sentence_len) {
            if (((r >> 8) & 3u) == 0)
                p2p_emit(buf, n, &pos, ".\n", 2);
            else
                p2p_emit(buf, n, &pos, ". ", 2);
            in_sentence = 0;
            sentence_len = 4 + p2p_lcg_next(&g) % 12;
        } else if ((r >> 12) % 10 == 0) {
            p2p_emit(buf, n, &pos, ", ", 2);
        } else {
            p2p_emit(buf, n, &pos, " ", 1);
        }
    }
}

/* 64-bit FNV-1a. The drivers print it for the input and for the
 * compressed stream. The input hash proves the generator is the same
 * everywhere. The compressed hash proves the compressor made the same
 * decisions, which a round trip alone does not show: a compressor can make
 * different choices and still decompress to the same bytes. */
static inline uint64_t p2p_fnv1a(const unsigned char *p, size_t n) {
    uint64_t h = 0xcbf29ce484222325ULL;
    for (size_t i = 0; i < n; i++) {
        h ^= p[i];
        h *= 0x100000001b3ULL;
    }
    return h;
}

/* Parse a positive decimal argument, or return 0 so the caller can print
 * its usage line. atoi() would turn "abc" into 0 silently too, but this
 * also rejects trailing junk such as "64k". */
static inline unsigned long p2p_parse_positive(const char *s) {
    unsigned long v = 0;
    if (*s == '\0')
        return 0;
    for (; *s; s++) {
        if (*s < '0' || *s > '9' || v > 100000000UL)
            return 0;
        v = v * 10 + (unsigned long)(*s - '0');
    }
    return v;
}

#endif /* P2P_TEXTGEN_H */
