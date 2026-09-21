// Toy trace-driven simulator.
//
// Reads a workload of "<pc_hex> <taken>" lines, drives ToyPredictor over it,
// and prints one line of JSON statistics. The machine model is deliberately
// trivial and fully deterministic: a fixed number of instructions per branch
// and a fixed misprediction penalty, so two runs of the same binary over the
// same workload produce byte-identical stats. The verify gate depends on that
// determinism for its feature-off equality check.

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <string>

#include "predictor.h"

namespace {

constexpr int kInstructionsPerBranch = 5;
constexpr int kMispredictPenaltyCycles = 20;

}  // namespace

int main(int argc, char** argv) {
  if (argc != 2) {
    std::fprintf(stderr, "usage: %s <workload>\n", argv[0]);
    return 2;
  }

  std::ifstream input(argv[1]);
  if (!input) {
    std::fprintf(stderr, "error: cannot open workload %s\n", argv[1]);
    return 2;
  }

  ToyPredictor predictor;
  uint64_t branches = 0;
  uint64_t mispredicts = 0;

  std::string line;
  while (std::getline(input, line)) {
    if (line.empty() || line[0] == '#') continue;
    std::istringstream fields(line);
    std::string pc_text;
    int taken_flag = 0;
    if (!(fields >> pc_text >> taken_flag)) {
      std::fprintf(stderr, "error: malformed workload line: %s\n", line.c_str());
      return 2;
    }
    const uint64_t pc = std::strtoull(pc_text.c_str(), nullptr, 16);
    const bool taken = taken_flag != 0;

    if (predictor.predict(pc) != taken) ++mispredicts;
    predictor.update(pc, taken);
    ++branches;
  }

  if (branches == 0) {
    std::fprintf(stderr, "error: workload contained no branches\n");
    return 2;
  }

  const uint64_t instructions = branches * kInstructionsPerBranch;
  const uint64_t cycles = instructions + mispredicts * kMispredictPenaltyCycles;
  const double mpki = 1000.0 * static_cast<double>(mispredicts) /
                      static_cast<double>(instructions);
  const double ipc =
      static_cast<double>(instructions) / static_cast<double>(cycles);

  std::printf(
      "{\"branches\": %llu, \"mispredicts\": %llu, \"instructions\": %llu, "
      "\"cycles\": %llu, \"mpki\": %.6f, \"ipc\": %.6f}\n",
      static_cast<unsigned long long>(branches),
      static_cast<unsigned long long>(mispredicts),
      static_cast<unsigned long long>(instructions),
      static_cast<unsigned long long>(cycles), mpki, ipc);
  return 0;
}
