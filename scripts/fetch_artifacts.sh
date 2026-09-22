#!/usr/bin/env bash
# Fetch third-party artifacts this repo builds against (none are committed).
# Verified sources as of 2026-09-11; see docs/research/ for provenance.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TP="$ROOT/third_party"
mkdir -p "$TP"

# 1. CBP2025 simulator kit (Rami Sheikh, ARM) — the yardstick host.
test -d "$TP/cbp2025" || git clone https://github.com/ramisheikh/cbp2025 "$TP/cbp2025"

# 2. RUNLTS paper (CBP2025 winner, Koizumi et al.) + extracted text for the distiller.
mkdir -p "$TP/runlts"
PDF="$TP/runlts/runlts.pdf"
test -f "$PDF" || curl -fL -o "$PDF" \
  "https://ericrotenberg.wordpress.ncsu.edu/files/2025/06/cbp2025-final44-Koizumi.pdf"
if [ ! -f "$TP/runlts/runlts.txt" ]; then
  if command -v pdftotext >/dev/null; then
    pdftotext -layout "$PDF" "$TP/runlts/runlts.txt"
  else
    # poppler is not installed on the head. pypdf gets the text out, but it
    # emits NUL and other C0 control bytes for some glyphs, and the
    # Antigravity CLI rejects the whole prompt with "embedded null byte".
    # That failure arrives three retries into --stage distill and says
    # nothing about the paper, so strip them at extraction time.
    python3 - "$PDF" "$TP/runlts/runlts.txt" <<'PY'
import sys
from pypdf import PdfReader

pdf, out = sys.argv[1], sys.argv[2]
text = "\n".join((page.extract_text() or "") for page in PdfReader(pdf).pages)
with open(out, "w") as f:
    f.write("".join(c for c in text if c >= " " or c in "\t\n\r"))
PY
  fi
fi
# Whatever produced it, the distiller reads this file verbatim into a prompt.
python3 -c "
import sys
p = sys.argv[1]
raw = open(p, 'rb').read()
clean = bytes(b for b in raw if b >= 32 or b in (9, 10, 13))
if clean != raw:
    open(p, 'wb').write(clean)
    print(f'stripped {len(raw) - len(clean)} control bytes from {p}')
" "$TP/runlts/runlts.txt"

# 3. RUNLTS reference artifact (Google Drive zip; paper_plus_reference arm).
#    pip install gdown
ARTIFACT_ID="1VcjlfeyKgEqgwvUhXWGCeT4Nul8oGlkO"
if [ ! -d "$TP/runlts/artifact" ]; then
  command -v gdown >/dev/null || { echo "pip install gdown to fetch the artifact"; exit 0; }
  gdown "$ARTIFACT_ID" -O "$TP/runlts/artifact.zip"
  mkdir -p "$TP/runlts/artifact" && unzip -o "$TP/runlts/artifact.zip" -d "$TP/runlts/artifact"
fi

# 4. CBP2025 training traces: the 105-trace "competition" set (~11.3 GiB
#    compressed .tar.xz per workload). Big: `chia up` now fetches these onto
#    each sim_worker node directly (cluster/cluster.yaml, cbp2025_worker
#    worker_setup_commands), not onto this machine.
#    (Zenodo record 15883615 has the full set -- training plus the held-out
#    scoring traces released after the workshop -- if that's ever needed
#    instead of the competition set.)
echo "Traces: provisioned per-node by 'chia up' (see cluster/cluster.yaml)."

# 5. Hosts.
test -d "$TP/ChampSim" || git clone https://github.com/ChampSim/ChampSim "$TP/ChampSim"
test -d "$TP/gem5" || git clone --branch v25.1.0.0 --depth 1 https://github.com/gem5/gem5 "$TP/gem5"

echo "done. See docs/plan.md for the next steps."
