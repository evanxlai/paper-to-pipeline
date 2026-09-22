#pragma once

#include <cstdlib>

#include "sr_params.h"

// Every knob of the toy host is read from the environment exactly once per
// run, so a configuration change never needs a rebuild. This is the header a
// tuning stage would mutate; it is also where a ported feature declares its
// own knobs, including its enable flag.
inline long param(const char* name, long fallback) {
  const char* value = std::getenv(name);
  return value ? std::strtol(value, nullptr, 0) : fallback;
}

// Baseline bimodal predictor: 1024 two-bit saturating counters.
inline long bimodal_entries() { return param("BIMODAL_ENTRIES", 1024); }

// tinysc. The fallback of each is the matching define in sr_params.h, which
// is the file stage 4 rewrites; the environment override exists so a unit
// test can configure itself without a rebuild.
inline long tinysc_enable() { return param("TINYSC_ENABLE", SR_TINYSC_ENABLE); }
inline long tinysc_entries() { return param("TINYSC_ENTRIES", SR_TINYSC_ENTRIES); }
inline long tinysc_hist_bits() { return param("TINYSC_HIST_BITS", SR_TINYSC_HIST_BITS); }
inline long tinysc_threshold() { return param("TINYSC_THRESHOLD", SR_TINYSC_THRESHOLD); }
