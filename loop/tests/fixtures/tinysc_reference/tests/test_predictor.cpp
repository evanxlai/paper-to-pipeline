// The toy host's own correctness suite. It ships with the host, so the
// integration loop treats a failure here as a regression the port introduced.
// A ported feature adds its own cases to this file; it must never weaken one
// of the baseline cases below to make its own pass.

#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

#include "params.h"
#include "predictor.h"

namespace {

int failures = 0;
int checks = 0;

void check(bool condition, const std::string& what) {
  ++checks;
  if (!condition) {
    ++failures;
    std::printf("FAIL: %s\n", what.c_str());
  }
}

// Added by the tinysc port. The test plan matches on the `ok:` line, not on
// the absence of a `FAIL:` line: a case that was never written also never
// prints a failure, so only a positive marker proves the case ran.
void report(bool condition, const std::string& what) {
  check(condition, what);
  if (condition) std::printf("ok: %s\n", what.c_str());
}

// Baseline: a branch that is always taken must be predicted taken once the
// bimodal counter has saturated.
void test_always_taken_is_learned() {
  ToyPredictor predictor;
  const uint64_t pc = 0x400100;
  for (int i = 0; i < 8; ++i) {
    predictor.predict(pc);
    predictor.update(pc, true);
  }
  check(predictor.predict(pc), "always-taken branch predicted taken");
}

// Baseline: a branch that is never taken must be predicted not-taken.
void test_never_taken_is_learned() {
  ToyPredictor predictor;
  const uint64_t pc = 0x400200;
  for (int i = 0; i < 8; ++i) {
    predictor.predict(pc);
    predictor.update(pc, false);
  }
  check(!predictor.predict(pc), "never-taken branch predicted not-taken");
}

// Baseline: two PCs that land in different bimodal entries must not train
// each other.
void test_distinct_pcs_are_independent() {
  ToyPredictor predictor;
  const uint64_t hot = 0x400300;
  const uint64_t cold = 0x400400;
  for (int i = 0; i < 8; ++i) {
    predictor.predict(hot);
    predictor.update(hot, true);
    predictor.predict(cold);
    predictor.update(cold, false);
  }
  check(predictor.predict(hot), "hot PC still predicted taken");
  check(!predictor.predict(cold), "cold PC still predicted not-taken");
}

// spec /unit_tests/0. Each tinysc case sets the knobs it needs itself,
// because params.h reads the environment on every call and TinySC reads its
// parameters in its constructor -- that is what lets cases needing the
// feature on and off share one binary.
void test_disabled_matches_base_predictor() {
  setenv("TINYSC_ENABLE", "0", 1);
  ToyPredictor predictor;
  std::vector<uint8_t> bimodal(static_cast<std::size_t>(bimodal_entries()), 2);
  const uint64_t pcs[] = {0x400600, 0x400700, 0x400800};
  bool same = true;
  for (int i = 0; i < 200; ++i) {
    for (uint64_t pc : pcs) {
      const bool taken = (i % 4) < 2;
      const std::size_t idx =
          static_cast<std::size_t>(pc >> 2) & (bimodal.size() - 1);
      if (predictor.predict(pc) != (bimodal[idx] >= 2)) same = false;
      predictor.update(pc, taken);
      if (taken) {
        if (bimodal[idx] < 3) ++bimodal[idx];
      } else {
        if (bimodal[idx] > 0) --bimodal[idx];
      }
    }
  }
  report(same, "disabled path matches the base predictor");
}

// spec /unit_tests/1.
void test_history_correlated_branch_is_learned() {
  setenv("TINYSC_ENABLE", "1", 1);
  ToyPredictor predictor;
  const uint64_t pc = 0x400500;
  int misses = 0;
  for (int i = 0; i < 400; ++i) {
    const bool taken = (i % 4) < 2;  // taken, taken, not-taken, not-taken
    const bool predicted = predictor.predict(pc);
    if (i >= 300 && predicted != taken) ++misses;
    predictor.update(pc, taken);
  }
  report(misses <= 5, "history-correlated branch is learned");
}

// spec /unit_tests/2.
void test_untrained_entry_defers_to_base() {
  setenv("TINYSC_ENABLE", "1", 1);
  ToyPredictor predictor;
  report(predictor.predict(0x400900),
         "untrained entry defers to the base predictor");
}

}  // namespace

int main() {
  test_always_taken_is_learned();
  test_never_taken_is_learned();
  test_distinct_pcs_are_independent();

  test_disabled_matches_base_predictor();
  test_history_correlated_branch_is_learned();
  test_untrained_entry_defers_to_base();

  std::printf("%d checks, %d failures\n", checks, failures);
  return failures == 0 ? 0 : 1;
}
