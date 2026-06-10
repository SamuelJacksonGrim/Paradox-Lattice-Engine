🧬 Paradox Lattice Engine — TYPES.md

This file defines all core data structures used across the Paradox Lattice Engine (PLE).  
If a module violates these type contracts, it is not part of PLE.

---

1. ParadoxNode

A paradox is a structured contradiction between two or more incompatible frames.

```
ParadoxNode:
- paradox_id: str
- frame_a: str
- frame_b: str
- contradiction_type: str          # e.g., logical, semantic, contextual, self-referential
- intensity: float                 # 0.0–1.0 paradox heat
- context_window: dict             # metadata about where paradox emerged
- supporting_evidence: list[str]
- opposing_evidence: list[str]
- lineage: list[str]               # ancestry of paradox formation
```

---

2. TensionField

A geometric representation of paradox-induced tension.

```
TensionField:
- field_id: str
- regions: list[TensionRegion]
- global_intensity: float
- coherence_map: dict[str, float]  # frame → coherence score
- void_zones: list[str]            # areas with no valid model coverage
```

TensionRegion
```
TensionRegion:
- region_id: str
- paradox_ids: list[str]
- tension_density: float
- coherence_score: float
- gradient_vector: dict[str, float]   # directional tension flow
- neighbors: list[str]
```

---

3. LatticeNode

Nodes in the paradox lattice graph.

```
LatticeNode:
- node_id: str
- node_type: str            # paradox | frame | synthesis | attractor
- payload: dict             # type-specific data
- tension_load: float
- stability_score: float
```

---

4. LatticeEdge

Edges represent structural relationships between paradoxes, frames, and syntheses.

```
LatticeEdge:
- edge_id: str
- source: str
- target: str
- relation_type: str        # contradiction | overlap | synthesis | dependency
- weight: float
- tension_transfer: float
```

---

5. ParadoxLattice

The full paradox lattice structure.

```
ParadoxLattice:
- lattice_id: str
- nodes: list[LatticeNode]
- edges: list[LatticeEdge]
- global_tension: float
- resolution_horizons: list[str]
```

---

6. ResolutionHorizon

A boundary where paradox might collapse but hasn’t yet.

```
ResolutionHorizon:
- horizon_id: str
- paradox_ids: list[str]
- collapse_probability: float
- stability_window: {start: float, end: float}
- triggers: list[str]               # events that could cause collapse
```

---

7. SynthesisRecord

Represents a synthesis event emerging from paradox tension.

```
SynthesisRecord:
- synthesis_id: str
- paradox_ids: list[str]
- method: str                      # coexistence | hybridization | reframing
- resulting_frame: str
- quality_score: float
- tension_reduction: float
- lineage: list[str]
```

---

8. ParadoxMemoryEpisode

Memory of paradox → tension → lattice → synthesis cycles.

```
ParadoxMemoryEpisode:
- episode_id: str
- paradox_ids: list[str]
- tension_signature: dict
- latticesnapshotid: str
- synthesis_ids: list[str]
- resolution_state: str            # unresolved | partial | collapsed
- identityshiftdelta: dict
```

---

9. TensionSignature

A compressed representation of tension topology.

```
TensionSignature:
- signature_id: str
- paradox_density: float
- tensiondistribution: dict[str, float]   # regionid → density
- coherence_profile: dict[str, float]      # frame → coherence
- void_ratio: float
```

---

10. StabilityProfile

Tracks how stable paradox coexistence or synthesis is.

```
StabilityProfile:
- profile_id: str
- nodestability: dict[str, float]   # nodeid → stability
- edgestability: dict[str, float]   # edgeid → stability
- global_stability: float
- drift_vectors: dict[str, float]
```

---

11. PLE Events

PLE uses typed events for cross-layer communication.

ParadoxEvent
```
ParadoxEvent:
- event_id: str
- paradox_id: str
- event_type: str        # detected | updated | normalized
- metadata: dict
```

TensionFieldEvent
```
TensionFieldEvent:
- event_id: str
- field_id: str
- change_type: str       # expanded | collapsed | intensified | diffused
- metadata: dict
```

LatticeUpdateEvent
```
LatticeUpdateEvent:
- event_id: str
- lattice_id: str
- updatetype: str       # nodeadded | edge_added | simplified | reweighted
- metadata: dict
```

SynthesisEvent
```
SynthesisEvent:
- event_id: str
- synthesis_id: str
- event_type: str        # created | updated | collapsed
- metadata: dict
```

ResolutionEvent
```
ResolutionEvent:
- event_id: str
- horizon_id: str
- resolution_type: str   # collapsed | stabilized | deferred
- metadata: dict
```

---

12. Global Validity Conditions

A PLE state is valid only if:

- paradoxes are represented as ParadoxNodes
- tension is represented as TensionFields
- contradictions form a ParadoxLattice
- synthesis is recorded as SynthesisRecords
- resolution boundaries exist as ResolutionHorizons

If any of these are missing → the system is not PLE.
