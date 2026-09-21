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

}  // namespace

int main() {
  test_always_taken_is_learned();
  test_never_taken_is_learned();
  test_distinct_pcs_are_independent();

  std::printf("%d checks, %d failures\n", checks, failures);
  return failures == 0 ? 0 : 1;
}
