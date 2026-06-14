# PLE runtime overhead

Cost of running the Paradox Lattice Engine as a sidecar, measured with
`examples/benchmark_overhead.py` (pure Python, no deps; absolute numbers are
machine-dependent — the *scaling shape* is the point).

## One-time
- Cold import: ~35 ms
- Engine init: ~50 µs

## Per `process()` call
| Case | Cost |
|---|---|
| Frames don't conflict (dormant) | ~2 µs |
| Contradiction → full pipeline | ~155 µs |

The dormant path short-circuits, so a host that mostly feeds non-conflicting
frames pays almost nothing.

## Scaling — the part that used to hurt

Earlier the active path degraded badly as history accumulated, because every
cycle (a) deep-copied the **entire** lattice into the memory episode and
(b) appended a fresh synthesis node + edges to the live lattice even when the
contradiction was identical to one already present.

| Prior calls | latency (before → after) | memory/call (before → after) |
|---|---|---|
| 0    | 450 µs → 157 µs | — |
| 1000 | 13 ms → 164 µs  | ~600 KB → ~4 KB |

Two changes fixed it (see `tests/test_overhead.py`):

1. **Content-interned snapshots** (`ple/models/lattice.py`) — successive
   snapshots share unchanged node/edge records instead of copying the whole
   lattice. Per-snapshot storage is now O(changes), not O(lattice size).
   Frozen-copy semantics are preserved: a later mutation produces a new
   content key, so older snapshots keep their original records.
2. **Synthesis node coalescing** (`ple/synthesis/synthesis_engine.py`) — a
   re-encountered contradiction reuses its existing synthesis lattice node
   (and skips duplicate edges) rather than appending an identical one each
   cycle. The synthesis **history** in memory still records every encounter,
   so attractor recurrence detection and finding emergence are unchanged.

Result: under sustained recurrence the live lattice **plateaus** and per-call
cost is **flat**.

## Note on genuinely growing ecologies
For a stream of *distinct* contradictions, memory grows O(n) by design —
append-only history is a contract (`memory_contract.md`: nothing is ever
deleted; archived paradoxes stay queryable forever). A host that needs a hard
ceiling for very long runs would add an opt-in retention bound; it is
deliberately not on by default so the "queryable forever" guarantee holds.
