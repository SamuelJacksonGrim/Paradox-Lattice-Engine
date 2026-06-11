"""Paradox Lattice Engine demo.

Feeds the engine the wave/particle duality contradiction repeatedly and an
unrelated logical contradiction, then prints the cognitive structures that
emerge: paradoxes, syntheses, attractors, and finally a validated Finding.

Run:  python3 examples/demo.py
"""

from ple import ParadoxLatticeEngine
from ple.findings import finding_export

WAVE = {"name": "wave_theory", "claims": {"light_is": "a wave"}}
PARTICLE = {"name": "particle_theory", "claims": {"light_is": "a particle"}}
OPTIMIST = {"name": "optimist", "claims": {"glass_is_full": True}}
PESSIMIST = {"name": "pessimist", "claims": {"glass_is_full": False}}


def banner(text):
    print(f"\n{'=' * 64}\n{text}\n{'=' * 64}")


def main():
    engine = ParadoxLatticeEngine()

    banner("Encounter 1: wave vs particle")
    r = engine.process(WAVE, PARTICLE)
    node = r.paradox_nodes[0]
    print(f"paradox    : {node.frame_a} <-> {node.frame_b}")
    print(f"  type     : {node.contradiction_type}, intensity now {node.intensity:.3f}")
    print(f"synthesis  : [{r.syntheses[0].method}] {r.syntheses[0].resulting_frame}")
    print(f"tension    : global {r.metrics['tension_load']:.3f}, "
          f"paradox density {r.metrics['paradox_density']:.3f}")
    print(f"attractors : {len(r.attractors)} (recurrence not yet established)")

    banner("Encounter 2: the same contradiction returns — recurrence!")
    r = engine.process(WAVE, PARTICLE)
    attractor = r.attractors[0]
    print(f"attractor  : {attractor.type} [{attractor.state.value}] "
          f"stability {attractor.stability_score:.3f}")
    print(f"  basin    : {len(attractor.basin_nodes)} lattice nodes")
    print(f"findings   : {len(r.findings)} (extracted the moment the attractor stabilized)")

    banner("Encounters 3-5: stability keeps reinforcing")
    for _ in range(3):
        r = engine.process(WAVE, PARTICLE)
        a = r.attractors[0]
        print(f"stability -> {a.stability_score:.3f} [{a.state.value}], "
              f"new findings: {len(r.findings)} (one finding per attractor, ever)")

    finding = engine.memory.findings[0]
    banner("FINDING extracted and validated")
    print(f"insight    : {finding.insight}")
    print(f"confidence : {finding.confidence:.3f} ({finding.validation_status})")
    print(f"lineage    : {len(finding.lineage)} ancestors, traceable to "
          f"{finding.source_paradoxes[0]}")

    banner("An unrelated logical paradox joins the ecology")
    r = engine.process(OPTIMIST, PESSIMIST)
    print(f"paradox    : {r.paradox_nodes[0].contradiction_type} -> "
          f"[{r.syntheses[0].method}] {r.syntheses[0].resulting_frame}")
    print(f"lattice    : {len(r.lattice.nodes)} nodes, {len(r.lattice.edges)} edges, "
          f"{len(r.lattice.nodes_of_type('paradox'))} paradoxes coexisting")

    banner("Memory: the full cognitive history")
    print(f"episodes   : {len(engine.memory.episodes)}")
    print(f"syntheses  : {len(engine.memory.synthesis_history)}")
    print(f"findings   : {len(engine.memory.findings)}")
    payload = finding_export.export(finding, destination="demo_host")
    print(f"export     : finding {payload['finding_id']} shipped, read-only ✓")

    # The prime directive held: paradoxes were never erased.
    survivors = engine.memory.get_active_paradoxes()
    print(f"\nParadoxes still alive and structurally intact: {len(survivors)}")
    print("PLE never resolved anything. It grew structure from the tension.")


if __name__ == "__main__":
    main()
