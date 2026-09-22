#include "tinysc.h"

#include "params.h"

TinySC::TinySC()
    : enabled_(tinysc_enable() != 0),
      threshold_(tinysc_threshold()),
      hist_bits_(static_cast<unsigned>(tinysc_hist_bits())),
      ghist_(0),
      table_(static_cast<std::size_t>(tinysc_entries()), 0) {}

std::size_t TinySC::index(uint64_t pc) const {
  return static_cast<std::size_t>((pc >> 2) ^ ghist_) & (table_.size() - 1);
}

bool TinySC::apply(uint64_t pc, bool base) const {
  if (!enabled_) return base;
  const long ctr = table_[index(pc)];
  // A counter of exactly 0 is not confident at any threshold of 1 or more,
  // so an untrained entry defers to the base prediction.
  if (ctr >= threshold_ || -ctr >= threshold_) return ctr >= 0;
  return base;
}

void TinySC::train(uint64_t pc, bool taken) {
  if (!enabled_) return;
  int8_t& ctr = table_[index(pc)];
  if (taken) {
    if (ctr < 31) ++ctr;
  } else {
    if (ctr > -32) --ctr;
  }
  ghist_ = ((ghist_ << 1) | (taken ? 1u : 0u)) & ((1u << hist_bits_) - 1u);
}
