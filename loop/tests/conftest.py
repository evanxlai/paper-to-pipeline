"""Put loop/ and the repo root on sys.path the same way the driver does.

adopt_a_paper_loop.py relies on Python putting its own directory on sys.path
when run as a script, so the loop modules import each other flat
(`import constants as C`). Tests are not run from that directory, so they
reproduce the same path setup here.
"""

import os
import sys

LOOP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(LOOP_DIR)

for path in (LOOP_DIR, REPO_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)
