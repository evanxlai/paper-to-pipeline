#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

// The toy host's conditional branch predictor.
//
// Baseline behavior is a bimodal table of two-bit saturating counters indexed
// by the branch PC. A ported feature wraps this: it may override what
// predict() returns and may keep its own state in update(), but only when its
// own enable knob is on.
class ToyPredictor {
 public:
  ToyPredictor();

  // Prediction for the conditional branch at `pc`. Must be called exactly
  // once per branch, before update() for that same branch.
  bool predict(uint64_t pc);

  // Resolution of the branch last passed to predict().
  void update(uint64_t pc, bool taken);

 private:
  std::size_t bimodal_index(uint64_t pc) const;

  std::vector<uint8_t> bimodal_;  // two-bit counters, 0..3; >= 2 means taken
};
