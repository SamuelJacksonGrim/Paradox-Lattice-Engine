Paradox Lattice Engine — Finding Contract

This document defines the behavioral, structural, and semantic rules governing Findings inside the Paradox Lattice Engine (PLE).  
If a module violates these rules, it is not part of PLE.

---

1. Definition of a Finding

A Finding is the final cognitive output of PLE:  
a distilled, validated, structurally‑grounded insight that emerges from attractors formed through repeated syntheses of paradox.

A valid Finding must satisfy:

- Attractor grounding — must originate from at least one stable attractor.  
- Structural derivation — must be traceable through lattice, synthesis, and paradox lineage.  
- Tension resolution profile — must reflect how tension was reorganized, not erased.  
- Contextual validity — must hold within the context window that produced it.  
- Non‑triviality — must represent a meaningful cognitive shift, not a restatement.

If any of these conditions fail → the finding is invalid.

---

2. Finding Structure Requirements

Every Finding must include:

- `finding_id: str`  
- `attractor_id: str`  
- `source_syntheses: list[str]`  
- `source_paradoxes: list[str]`  
- `insight: str`  
- `confidence: float`  
- `tension_profile: dict`  
- `lineage: list[str]`  
- `validation_status: str`     // unvalidated | validated | deprecated  
- `export_metadata: dict`  

Rules:

- `confidence` ∈ [0.0, 1.0]  
- `source_syntheses` must be non‑empty  
- `source_paradoxes` must be non‑empty  
- `insight` must be a coherent, interpretable statement  
- `lineage` must be monotonic (never removed, only extended)

Findings are immutable except for `validation_status` and `export_metadata`.

---

3. Finding Generation Rules

A Finding may only be generated when:

- an attractor reaches sufficient stability  
- its basin has converged  
- its lineage is complete  
- its tension profile is stable  
- its synthesis history is consistent  

Findings must not be generated from:

- single syntheses  
- unstable attractors  
- transient lattice states  
- incomplete paradox histories  
- unresolved paradox clusters  

Findings represent mature cognitive structure, not intermediate steps.

---

4. Finding Validation Contract

Validation determines whether a Finding is:

- structurally sound  
- contextually correct  
- internally consistent  
- externally coherent  

Validation must check:

- attractor stability  
- synthesis lineage  
- paradox ancestry  
- tension reduction patterns  
- recurrence across episodes  

Validation may not:

- rewrite the finding  
- alter its insight  
- remove lineage  
- delete paradox ancestry  

Validation only updates `validation_status`.

---

5. Finding Confidence Rules

Confidence reflects structural reliability, not truth.

Confidence must:

- increase with attractor stability  
- increase with synthesis recurrence  
- decrease with new paradoxes that destabilize the attractor  
- never exceed 1.0  
- never drop below 0.0  

Only the finding_validator may update confidence.

---

6. Interaction With Other Layers

6.1 Paradox Layer
May:

- read findings  
- trace paradox ancestry  

May not:

- mutate findings  
- generate findings  

---

6.2 Tension Field Layer
May:

- read tension profiles  
- influence confidence indirectly  

May not:

- mutate findings  
- rewrite tension profiles  

---

6.3 Lattice Layer
May:

- read lineage  
- support finding queries  

May not:

- mutate findings  
- alter finding ancestry  

---

6.4 Synthesis Layer
May:

- contribute source_syntheses  
- influence finding formation  

May not:

- create findings  
- mutate findings  

---

6.5 Attractor Layer
May:

- trigger finding creation  
- provide attractor lineage  

May not:

- alter findings  
- delete findings  

---

6.6 Memory Layer
Must:

- store findings permanently  
- preserve lineage  
- preserve validation status  
- preserve export metadata  

May not:

- alter insights  
- delete findings  
- overwrite findings  

---

7. Finding Mutation Rules

Findings are immutable except for:

- `validation_status`  
- `export_metadata`  

Forbidden mutations:

- altering insight  
- altering lineage  
- altering source paradoxes  
- altering source syntheses  
- altering attractor ancestry  
- deleting findings  

Findings must remain stable and permanent.

---

8. Finding Export Contract

Findings may be exported to external systems.

Export must:

- preserve insight  
- preserve lineage  
- preserve validation status  
- preserve confidence  
- include export metadata  

Export must not:

- alter the finding  
- remove paradox ancestry  
- remove attractor ancestry  

Export is a read‑only operation.

---

9. Finding Events Contract

Valid finding events:

- `finding_created`  
- `finding_validated`  
- `finding_deprecated`  
- `finding_exported`  

Invalid events:

- `deleted`  
- `resolved`  
- `overwritten`  

Findings cannot be deleted or overwritten.

---

10. Prime Directive for Findings

> A finding must represent a stable, validated, structurally traceable insight that emerges from attractor dynamics without erasing the paradoxes that generated it.

No module may bypass this rule.

---

11. Finding Contract Summary

A Finding in PLE must:

- originate from stable attractors  
- be grounded in paradox and synthesis lineage  
- preserve tension structure  
- remain immutable  
- be validated, not rewritten  
- be permanently stored  
- be exportable without modification  

If any of these conditions fail → the finding is invalid.
