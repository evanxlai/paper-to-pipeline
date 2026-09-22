#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

// The tinysc statistical corrector: one table of signed saturating counters
// indexed by the branch PC folded with a global history register. When the
// selected counter is confident its sign overrides the base prediction;
// otherwise the base prediction stands.
//
// Every parameter is read once in the constructor, so one run has one
// configuration. With the enable knob off nothing here is read or written.
class TinySC {
 public:
  TinySC();

  // The final prediction for `pc`, given the host's base prediction.
  bool apply(uint64_t pc, bool base) const;

  // Train on a resolved outcome. Advances the history register last, after
  // the counter write, so predict and update see the same index.
  void train(uint64_t pc, bool taken);

 private:
  std::size_t index(uint64_t pc) const;

  bool enabled_;
  long threshold_;
  unsigned hist_bits_;
  uint32_t ghist_;
  std::vector<int8_t> table_;
};
