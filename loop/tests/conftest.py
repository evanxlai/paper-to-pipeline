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


def pytest_configure(config):
    """Keep the whole suite off the live Ray cluster.

    A ChiaFunction called locally builds chia's profiler, and the profiler
    looks up its collector actor with ray.get_actor. Ray answers that by
    running ray.init() with no address, which joins whatever cluster
    /tmp/ray/ray_current_cluster names. On the head that is the live cluster,
    where other jobs run for hours. Three test runs on 2026-09-23 attached a
    driver there this way (test_cbp2025_adapter.py, test_dse_wiring.py).

    No collector means a disabled profiler, which is also what the live
    cluster answers, so nothing a test checks changes. A ray.init that still
    happens fails the test instead of connecting. Tests that want to count
    ray.init calls monkeypatch it on top of this."""
    import ray
    from chia.trace import profiler

    profiler.get_collector = lambda namespace=None: None
    profiler._profiler = None

    def refuse(*args, **kwargs):
        raise AssertionError("a unit test tried to start or join Ray")

    ray.init = refuse
