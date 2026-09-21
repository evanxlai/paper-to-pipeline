#pragma once

#include <cstdlib>

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
