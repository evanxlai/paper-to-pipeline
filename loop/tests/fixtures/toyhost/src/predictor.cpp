#include "predictor.h"

#include "params.h"

ToyPredictor::ToyPredictor()
    : bimodal_(static_cast<std::size_t>(bimodal_entries()), 2) {}

std::size_t ToyPredictor::bimodal_index(uint64_t pc) const {
  return static_cast<std::size_t>(pc >> 2) & (bimodal_.size() - 1);
}

bool ToyPredictor::predict(uint64_t pc) {
  return bimodal_[bimodal_index(pc)] >= 2;
}

void ToyPredictor::update(uint64_t pc, bool taken) {
  uint8_t& counter = bimodal_[bimodal_index(pc)];
  if (taken) {
    if (counter < 3) ++counter;
  } else {
    if (counter > 0) --counter;
  }
}
