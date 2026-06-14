"""Overhead regression tests.

These pin the two scaling fixes so they can't silently regress:

  1. Snapshot interning — successive lattice snapshots share unchanged
     node/edge records instead of deep-copying the whole lattice every cycle
     (was O(nodes) memory per snapshot, O(nodes^2) overall).
  2. Synthesis node coalescing — a re-encountered contradiction reuses its
     existing synthesis lattice node rather than appending an identical one
     each cycle, so the live lattice stays bounded under recurrence.

Neither may change observable cognitive behavior: the synthesis *history*
still records every encounter and findings still emerge from recurrence.
"""

import tracemalloc

import pytest

from ple import ParadoxLatticeEngine

WAVE = {"name": "wave_theory", "claims": {"light_is": "a wave"}}
PARTICLE = {"name": "particle_theory", "claims": {"light_is": "a particle"}}


@pytest.fixture
def engine():
    return ParadoxLatticeEngine()


class TestLatticeBounded:
    def test_lattice_plateaus_under_recurrence(self, engine):
        """The same contradiction processed many times must not grow the
        live lattice without bound."""
        for _ in range(5):
            engine.process(WAVE, PARTICLE)
        nodes_early = len(engine.lattice.nodes)
        edges_early = len(engine.lattice.edges)
        for _ in range(200):
            engine.process(WAVE, PARTICLE)
        assert len(engine.lattice.nodes) == nodes_early
        assert len(engine.lattice.edges) == edges_early

    def test_no_duplicate_synthesis_nodes(self, engine):
        for _ in range(20):
            engine.process(WAVE, PARTICLE)
        synth = engine.lattice.nodes_of_type("synthesis")
        shapes = {
            (n.payload["method"], n.payload["resulting_frame"]) for n in synth
        }
        # One node per distinct synthesis shape, not one per encounter.
        assert len(synth) == len(shapes)

    def test_history_still_records_every_encounter(self, engine):
        """Coalescing lattice nodes must NOT drop synthesis history —
        recurrence detection depends on it."""
        n = 12
        for _ in range(n):
            engine.process(WAVE, PARTICLE)
        assert len(engine.memory.synthesis_history) == n

    def test_emergence_survives_coalescing(self, engine):
        """A finding must still be extracted once recurrence stabilizes."""
        for _ in range(3):
            engine.process(WAVE, PARTICLE)
        assert len(engine.memory.findings) >= 1
        finding = engine.memory.findings[0]
        assert finding.source_paradoxes  # still traceable to its paradox


class TestSnapshotInterning:
    def test_unchanged_records_are_shared(self, engine):
        """Two snapshots of a lattice region that didn't change must reuse
        the identical record objects, not copies."""
        engine.process(WAVE, PARTICLE)
        snap_a = engine.lattice.snapshot()
        # A no-op snapshot right after: same content -> shared records.
        snap_b = engine.lattice.snapshot()
        a_by_id = {n["node_id"]: n for n in snap_a["nodes"]}
        shared = sum(
            1 for n in snap_b["nodes"] if a_by_id.get(n["node_id"]) is n
        )
        assert shared == len(snap_b["nodes"]) > 0

    def test_snapshot_shape_unchanged(self, engine):
        """Interning must not alter the public snapshot shape."""
        engine.process(WAVE, PARTICLE)
        snap = engine.lattice.snapshot()
        assert set(snap) >= {
            "snapshot_id",
            "lattice_id",
            "state",
            "global_tension",
            "nodes",
            "edges",
        }
        for n in snap["nodes"]:
            assert set(n) == {
                "node_id",
                "node_type",
                "payload",
                "tension_load",
                "stability_score",
            }

    def test_mutation_does_not_alter_prior_snapshot(self, engine):
        """A later change to a live node must not retroactively mutate an
        earlier snapshot (frozen-copy guarantee, memory_contract.md §5)."""
        engine.process(WAVE, PARTICLE)
        snap = engine.lattice.snapshot()
        before = {n["node_id"]: n["tension_load"] for n in snap["nodes"]}
        # Drive more cycles, which mutate tension loads.
        for _ in range(5):
            engine.process(WAVE, PARTICLE)
        after = {n["node_id"]: n["tension_load"] for n in snap["nodes"]}
        assert before == after

    def test_snapshot_memory_is_bounded_under_recurrence(self, engine):
        """Per-cycle retained memory must stay flat once the lattice has
        plateaued — the regression that motivated interning + coalescing."""
        for _ in range(20):  # let the lattice settle
            engine.process(WAVE, PARTICLE)
        tracemalloc.start()
        base = tracemalloc.get_traced_memory()[0]
        for _ in range(500):
            engine.process(WAVE, PARTICLE)
        grown = tracemalloc.get_traced_memory()[0] - base
        tracemalloc.stop()
        per_call = grown / 500
        # Baseline before the fix was ~600 KB/call. Allow generous headroom
        # for append-only episode/signature/synthesis-history bookkeeping.
        assert per_call < 50_000, f"{per_call:.0f} B/call is too high"
