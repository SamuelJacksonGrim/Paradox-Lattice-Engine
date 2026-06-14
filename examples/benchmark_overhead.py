"""Runtime-overhead benchmark for the Paradox Lattice Engine.

Measures the cost a host pays to run PLE as a sidecar:

  * import + init (one-time)
  * per-call latency when frames do NOT conflict (the common, dormant case)
  * per-call latency when a contradiction drives the full pipeline
  * how per-call latency and retained memory scale with accumulated history

Run:  python3 examples/benchmark_overhead.py
"""

from __future__ import annotations

import gc
import statistics
import time
import tracemalloc

from ple import ParadoxLatticeEngine

WAVE = {"name": "wave", "claims": {"light_is": "a wave"}}
PARTICLE = {"name": "particle", "claims": {"light_is": "a particle"}}
NOCONFLICT_A = {"name": "x", "claims": {"k": "v"}}
NOCONFLICT_B = {"name": "y", "claims": {"j": "w"}}


def bench(fn, n=2000, warmup=200):
    for _ in range(warmup):
        fn()
    gc.disable()
    s = []
    for _ in range(n):
        t = time.perf_counter()
        fn()
        s.append(time.perf_counter() - t)
    gc.enable()
    s.sort()
    return {
        "median_us": statistics.median(s) * 1e6,
        "p95_us": s[int(len(s) * 0.95)] * 1e6,
    }


def main():
    t = time.perf_counter()
    _ = ParadoxLatticeEngine()
    print(f"init: {(time.perf_counter() - t) * 1e6:.1f} us")

    none = ParadoxLatticeEngine()
    print("no-contradiction (dormant): ", bench(
        lambda: none.process(dict(NOCONFLICT_A), dict(NOCONFLICT_B))))

    active = ParadoxLatticeEngine()
    print("active (full pipeline):     ", bench(
        lambda: active.process(dict(WAVE), dict(PARTICLE))))

    print("\nlatency vs accumulated calls (should stay flat):")
    for pf in (0, 100, 500, 1000):
        e = ParadoxLatticeEngine()
        for _ in range(pf):
            e.process(dict(WAVE), dict(PARTICLE))
        s = []
        for _ in range(200):
            t = time.perf_counter()
            e.process(dict(WAVE), dict(PARTICLE))
            s.append(time.perf_counter() - t)
        print(f"  after {pf:5d}: {statistics.median(s) * 1e6:8.1f} us")

    e = ParadoxLatticeEngine()
    gc.collect()
    tracemalloc.start()
    base = tracemalloc.get_traced_memory()[0]
    for _ in range(1000):
        e.process(dict(WAVE), dict(PARTICLE))
    grown = tracemalloc.get_traced_memory()[0] - base
    tracemalloc.stop()
    print(f"\nmemory after 1000 recurrences: +{grown / 1024:.0f} KiB "
          f"({grown / 1000:.0f} B/call)")


if __name__ == "__main__":
    main()
