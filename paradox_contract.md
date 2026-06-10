Paradox Lattice Engine — Paradox Contract

This document defines the behavioral, structural, and semantic rules governing paradoxes inside the Paradox Lattice Engine (PLE).  
If a module violates these rules, it is not part of PLE.

---

1. Definition of a Paradox

A paradox is a structured contradiction between two or more incompatible frames, models, or hypotheses.

A valid paradox must satisfy:

- Frame incompatibility — at least two frames produce mutually exclusive claims.  
- Contextual simultaneity — the contradiction occurs within the same context window.  
- Non‑triviality — the contradiction cannot be removed by simple rephrasing or local correction.  
- Bidirectional tension — each frame exerts pressure on the other.  
- Persistence under normalization — after canonicalization, the contradiction still exists.

If any of these conditions fail → the object is not a paradox.

---

2. Paradox Structure Requirements

Every paradox must be represented as a ParadoxNode containing:

- `frame_a` and `frame_b`  
- `contradiction_type`  
- `intensity`  
- `context_window`  
- `supporting_evidence`  
- `opposing_evidence`  
- `lineage`

A paradox must not:

- collapse into a single frame  
- resolve itself during detection  
- mutate its own contradiction type  
- lose its lineage  
- be overwritten by synthesis  

ParadoxNodes are immutable except for intensity updates.

---

3. Nested Paradoxes

Nested paradoxes are allowed under strict rules.

A paradox may contain:

- sub‑paradoxes  
- recursive contradictions  
- self‑referential loops  

But only if:

- The parent paradox remains valid  
- The nested paradox does not resolve the parent  
- The lattice can represent the nesting  

Nested paradoxes must be represented as:

```
ParadoxNode:
    nested_paradox_ids: list[str]
```

Nested paradoxes must not be flattened unless explicitly simplified by the lattice layer.

---

4. Paradox Intensity Contract

Paradox intensity represents tension magnitude, not importance.

Intensity must:

- increase when contradictions sharpen  
- decrease when synthesis reduces tension  
- never drop below zero  
- never exceed 1.0  
- be updated only by the paradoxintensitymodel  

No other module may mutate intensity.

---

5. Paradox Lifecycle

A paradox has exactly five lifecycle states:

1. detected  
2. normalized  
3. active  
4. attenuated  
5. archived

Rules:

- Only the paradox layer may create paradoxes.  
- Only the synthesis or attractor layers may attenuate paradoxes.  
- Only the memory layer may archive paradoxes.  
- No module may delete a paradox.  

Archived paradoxes remain queryable forever.

---

6. Paradox Validity Conditions

A paradox is valid only if:

- frames remain incompatible  
- contradiction type remains stable  
- context window remains coherent  
- intensity > 0  
- the paradox is represented in the lattice  

If any condition fails → paradox transitions to attenuated state.

---

7. Mutation Rules

Paradoxes are mostly immutable.

Allowed mutations:

- intensity updates  
- lineage extension  
- addition of nested paradoxes  

Forbidden mutations:

- changing contradiction type  
- altering frame identities  
- removing evidence  
- deleting lineage  
- collapsing paradox into a single frame  

Violating these rules invalidates the paradox.

---

8. Interaction With Other Layers

8.1 Tension Field Layer
Tension fields may:

- read paradox intensity  
- group paradoxes into regions  
- compute gradients  

They may not:

- modify paradox structure  
- change contradiction type  
- delete paradoxes  

---

8.2 Lattice Layer
The lattice may:

- create lattice nodes for paradoxes  
- create edges between paradoxes  
- simplify lattice structure  

It may not:

- merge paradoxes  
- rewrite paradox content  
- remove paradox lineage  

---

8.3 Synthesis Layer
Synthesis may:

- reduce paradox intensity  
- generate new frames  
- create coexistence structures  

It may not:

- resolve paradoxes directly  
- delete paradoxes  
- overwrite paradox nodes  

---

8.4 Attractor Layer
Attractors may:

- stabilize paradox coexistence  
- track recurring paradox patterns  

They may not:

- collapse paradoxes  
- mutate paradox structure  

---

8.5 Memory Layer
Memory may:

- archive paradoxes  
- store paradox episodes  
- compress paradox histories  

It may not:

- alter paradox content  
- remove paradoxes from active state prematurely  

---

9. Paradox Events Contract

Valid paradox events:

- `detected`  
- `normalized`  
- `updated`  
- `nested`  
- `attenuated`  
- `archived`

Invalid events:

- `resolved`  
- `deleted`  
- `collapsed`  

Paradoxes cannot be resolved or deleted — only attenuated or archived.

---

10. Prime Directive for Paradoxes

> A paradox must remain structurally intact until synthesis or attractor dynamics reduce its tension.

No module may bypass this rule.

---

11. Paradox Contract Summary

A paradox in PLE must:

- be a real contradiction  
- remain structurally stable  
- be immutable except for intensity  
- be representable in the lattice  
- participate in tension fields  
- feed synthesis  
- survive until archived  

If any of these conditions fail → the paradox is invalid.
