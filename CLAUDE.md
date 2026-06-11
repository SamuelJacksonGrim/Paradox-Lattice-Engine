# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Repository Status

The engine is **implemented** as the Python package `ple/` (Phases 1, 2 (partial), 3 (partial), and 5 of the roadmap). The contract documents (`*_contract.md`) remain the authoritative behavioral spec; the code enforces them at runtime via `ContractViolation` exceptions.

## Commands

```bash
pip install -e ".[dev]"        # install package + pytest (required once)
pytest                          # run the full test suite
pytest tests/test_pipeline.py   # run one test file
pytest tests/test_pipeline.py::TestFindings::test_repeated_tension_produces_validated_finding  # one test
python3 examples/demo.py        # end-to-end demo: contradiction -> Finding
```

There is no linter configured. Python ≥ 3.10 (uses modern type syntax); only dev dependency is pytest.

## Implementation Map

```
ple/models/      — frozen dataclasses for all TYPES.md types + ParadoxLattice graph
ple/models/_mutation.py — the authorized-mutation gateway (actor allowlists per field)
ple/errors.py    — ContractViolation hierarchy
ple/events/      — typed events; invalid types (resolved/deleted/overwritten) raise at construction
ple/core/        — ParadoxLatticeEngine orchestrator (paradox_pipeline.py) + TensionRouter
ple/paradox/     — detector, classifier, intensity model (sole intensity mutator), normalizer
ple/fields/      — tension field generator, coherence map processor, resolution horizons
ple/lattice/     — lattice builder, simplifier (cannot delete paradox/attractor nodes)
ple/synthesis/   — synthesis engine (method chosen by contradiction type)
ple/attractors/  — detector (recurrence >= 2), evolution, stability, registry
ple/findings/    — extractor (requires stable attractor), validator, export
ple/memory/      — append-only ParadoxMemoryBuffer
ple/metrics/     — ecology metrics (density, tension load, quality, stability)
tests/           — contract enforcement + end-to-end pipeline tests
```

### Key implementation patterns

- **Immutability**: models are frozen dataclasses. The narrow mutable fields (intensity, stability_score, validation_status, …) are written only through `ple/models/_mutation.py:authorized_set`, which checks a per-(type, field) actor allowlist. When adding a processor that needs write access, register it there.
- **Lifecycle**: each model owns a `transition(new_state, actor=...)` method validating both the state edge and the acting layer against the contract tables.
- **Actor strings**: modules declare an `ACTOR` constant (e.g. `"synthesis_engine"`) and pass it to guarded operations. The lattice additionally restricts which node types each actor may add.
- **Recurrence drives emergence**: `ParadoxLatticeEngine` is stateful. The same contradiction processed twice forms an attractor; a finding is extracted once per attractor the moment stability crosses `finding_extractor.MIN_STABILITY` (0.5) — typically on the second encounter.
- **Frames** are plain dicts: `{"name": str, "claims": {key: value}}`; contradictions are shared claim keys with conflicting (post-canonicalization) values.

---

## What This Repository Is

The Paradox Lattice Engine (PLE) is a cognitive subsystem that treats contradictions as a primary computational substrate rather than errors to eliminate. It activates on conflicting model outputs, incompatible frames, logical/semantic contradictions, multi-agent disagreement, and self-referential inconsistencies.

The central question PLE answers: **"What becomes possible because this contradiction exists?"**

---

## Six-Layer Architecture

Processing flows through these layers in order, with feedback possible in both directions:

```
Paradox → Tension Field → Lattice → Synthesis → Attractor → Finding → Memory
```

| Layer | Purpose | Primary output type |
|---|---|---|
| **Paradox** | Detects contradictions, creates canonical structures | `ParadoxNode` |
| **Tension Field** | Models paradox intensity as geometry (regions, gradients, voids) | `TensionField` |
| **Lattice** | Builds the structural graph of paradoxes, frames, and syntheses | `ParadoxLattice` |
| **Synthesis** | Generates new cognitive structures from tension | `SynthesisRecord` |
| **Attractor** | Identifies stable structures from repeated syntheses | `Attractor` |
| **Findings** | Extracts and validates cognitive output | `Finding` |
| **Memory** | Stores full paradox-to-finding episodes as first-class history | `ParadoxMemoryEpisode` |

Cross-layer communication is handled through typed events (`ParadoxEvent`, `TensionFieldEvent`, `LatticeUpdateEvent`, `SynthesisEvent`, `ResolutionEvent`) routed through `core/tension_router.py`. The orchestration entry point is `core/paradox_pipeline.py`.

---

## Core Types

All types are defined in `TYPES.md`. The most critical:

- **`ParadoxNode`** — `{paradox_id, frame_a, frame_b, contradiction_type, intensity: float[0,1], context_window, supporting_evidence, opposing_evidence, lineage}`
- **`TensionField`** — `{field_id, regions: list[TensionRegion], global_intensity, coherence_map, void_zones}`
- **`ParadoxLattice`** — `{lattice_id, nodes: list[LatticeNode], edges: list[LatticeEdge], global_tension, resolution_horizons}`
- **`SynthesisRecord`** — `{synthesis_id, paradox_ids, method: coexistence|hybridization|reframing, resulting_frame, quality_score, tension_reduction: float[0,1], lineage}`
- **`LatticeNode`** — `node_type` is one of: `paradox | frame | synthesis | attractor`
- **`LatticeEdge`** — `relation_type` is one of: `contradiction | overlap | synthesis | dependency`

---

## Non-Negotiable Behavioral Contracts

These constraints apply across all layers. Any implementation that violates them is invalid PLE.

**Paradoxes (`paradox_contract.md`):**
- `ParadoxNode` is immutable except for `intensity` (updated only by `paradoxintensitymodel`) and `lineage` (append-only) and nested paradox additions.
- Forbidden mutations: changing `contradiction_type`, altering frame identities, removing evidence, deleting lineage.
- No module may delete a paradox. Archived paradoxes remain queryable forever.
- Only the paradox layer creates paradoxes; only synthesis/attractor may attenuate them; only memory may archive them.
- Valid lifecycle: `detected → normalized → active → attenuated → archived`.
- Invalid events: `resolved`, `deleted`, `collapsed` — these must never be emitted.

**Synthesis (`synthesis_contract.md`):**
- `SynthesisRecord` is immutable once created. Lineage is monotonically append-only.
- Three allowed methods only: `coexistence` (both frames preserved, domains partitioned), `hybridization` (new frame subsumes both), `reframing` (paradox dissolves at higher-order level — must not silently discard; mark as reframed).
- Synthesis may attenuate paradox tension but must never delete, overwrite, or merge paradox nodes.
- Synthesis produces attractor *candidates* only — it must never directly create `Attractor` objects.
- Any lattice simplification triggered by synthesis must go through lattice processors, not synthesis modules.

**General rules across all layers:**
- No layer may mutate objects owned by another layer (e.g., tension fields cannot modify paradox structure).
- Memory never alters content of any stored object — it only archives and retrieves.
- Findings must be traceable through their full lineage back to source paradoxes.

---

## Module Organization (Planned)

Modules follow snake_case naming. The planned directory layout:

```
core/          — orchestration: ple_orchestrator, paradox_pipeline, tension_router, execution_context
paradox/       — detection: paradox_detector, contradiction_classifier, paradoxintensitymodel, paradox_normalizer
fields/        — tension geometry: tensionfieldgenerator, tensionfieldmodel, tension_topology, coherence_map, void_mapper
lattice/       — graph: lattice_builder, latticenodemodel, latticeedgemodel, multiframeindex, lattice_simplifier
synthesis/     — transformation: synthesis_engine, dualframeresolver, tensioncollapsepredictor, emergentattractorbuilder
attractors/    — stability: attractor_model, attractor_detector, attractor_stability, attractor_registry, attractor_evolution
findings/      — output: finding, finding_registry, finding_validator, finding_export
memory/        — history: paradoxmemorybuffer, tensionsignatureindex, latticepatternstore, synthesis_history, compression_strategy
state/         — runtime: active_paradoxes, active_fields, active_lattice, active_attractors, runtime_state
query/         — retrieval: lattice_search, paradox_lookup, attractor_lookup, pattern_query
metrics/       — ecology: paradoxdensitymetrics, tensionloadmonitor, synthesisqualityestimator, stabilityprofileanalyzer
events/        — typed events (one file per event type)
integration/   — bridges: lae_bridge, chimera_bridge, rfecore2hook, system_hooks, external_api
models/        — data classes: paradox, tension_field, lattice, synthesis, attractor, horizon, finding
```

---

## Integration Points

PLE is a sidecar subsystem. Three external integration targets:

- **LAE (Liminal Anchor Engine)** — LAE structures transitions; PLE structures contradictions. PLE can emit paradox-driven tension that LAE treats as transition triggers. Bridge: `integration/lae_bridge.py`.
- **Chimera Core / multi-mind systems** — micro-mind collisions become `ParadoxNode`s. Bridge: `integration/chimera_bridge.py`.
- **RFE-Core2** — hooks into conflict layers and evaluator disagreements. Bridge: `integration/rfecore2hook.py`.

---

## Failure Modes to Guard Against

- **Paradox flooding** — too many paradoxes → unbounded tension → no useful synthesis. Needs density thresholds.
- **Premature collapse** — resolving paradox before it's structurally useful. Resolution is optional, not required.
- **Over-synthesis** — forcing synthesis where coexistence is more appropriate.
- **Lattice over-simplification** — compressing topology so much that paradox structure is lost.
- **Stability ossification** — attractors becoming dogma that blocks new paradox recognition.

---

## Contract Files

Each subsystem has a full behavioral contract. When implementing any module, read the relevant contract first:

- `paradox_contract.md` — paradox rules
- `field_contract.md` — tension field rules
- `lattice_contract.md` — lattice rules
- `synthesis_contract.md` — synthesis rules
- `attractor_contract.md` — attractor rules
- `memory_contract.md` — memory rules
- `finding_contract.md` — finding rules
- `paradox_pipeline.md` — full pipeline with pseudocode for all 5 stages
