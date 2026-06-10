Paradox Lattice Engine — Attractor Contract

This document defines the behavioral, structural, and semantic rules governing attractors inside the Paradox Lattice Engine (PLE).  
If a module violates these rules, it is not part of PLE.

---

1. Definition of an Attractor

An Attractor is a stable cognitive structure that emerges from repeated syntheses under persistent paradox tension.

A valid attractor must satisfy:

- Recurrence — the same or similar synthesis patterns must appear multiple times.  
- Stability — the structure must persist across context windows.  
- Tension compatibility — the attractor must reduce or reorganize tension without erasing paradox.  
- Representability — must map cleanly to an Attractor model and lattice node.  
- Lineage continuity — must preserve the history of syntheses that formed it.

If any of these conditions fail → the attractor is invalid.

---

2. Attractor Structure Requirements

Every attractor must include:

- attractor_id: str  
- type: str                     // coexistence | hybrid | reframed | emergent  
- coresyntheses: list[str]     // synthesisids  
- stability_score: float  
- tension_profile: dict  
- basin_nodes: list[str]        // lattice nodes in the attractor basin  
- lineage: list[str]            // synthesis + paradox ancestry  

Rules:

- stability_score ∈ [0.0, 1.0]  
- core_syntheses must be non‑empty  
- basin_nodes must form a connected subgraph  
- lineage must be monotonic (never removed, only extended)

Attractors are immutable except for stability_score and basin expansion.

---

3. Attractor Types

Allowed attractor types:

- coexistence attractor  
  Stable partitioning of incompatible frames.

- hybrid attractor  
  A new stable frame formed from repeated hybrid syntheses.

- reframed attractor  
  A stable reinterpretation that dissolves paradox at a higher level.

- emergent attractor  
  A novel structure not predictable from initial paradoxes.

Rules:

- coexistence attractors must preserve all input frames  
- hybrid attractors must reference all contributing frames in lineage  
- reframed attractors must not delete paradoxes — only recontextualize  
- emergent attractors must be validated by recurrence  

No new attractor types may be introduced without updating this contract.

---

4. Attractor Basin Contract

An attractor basin is the set of lattice nodes that converge toward the attractor.

A valid basin must:

- be connected  
- include paradox, synthesis, and frame nodes  
- reflect actual convergence patterns  
- maintain stable tension flow toward the attractor  

A basin must not:

- include void zones  
- include unrelated paradoxes  
- include nodes with incompatible context windows  

Basin expansion is allowed only through attractor_evolution.

---

5. Attractor Stability Rules

Stability is the defining property of attractors.

Stability must:

- increase with repeated syntheses  
- decrease when new paradoxes destabilize the structure  
- never exceed 1.0  
- never drop below 0.0  

Only the attractor_stability module may update stability.

Attractors must not:

- collapse spontaneously  
- be deleted  
- be overwritten by new attractors  

If destabilized, attractors transition to attenuated, not deleted.

---

6. Attractor Lifecycle

Attractors have six lifecycle states:

1. candidate  
2. forming  
3. active  
4. stabilizing  
5. attenuated  
6. archived

Rules:

- only synthesis may promote a structure to candidate  
- only attractor_detector may promote candidate → forming  
- only attractor_evolution may promote forming → active  
- only attractor_stability may promote active → stabilizing  
- only memory may archive attractors  
- no module may delete attractors  

Archived attractors remain queryable forever.

---

7. Attractor Mutation Rules

Attractors are mostly immutable.

Allowed mutations:

- stability_score updates  
- basin expansion  
- lineage extension  

Forbidden mutations:

- changing attractor type  
- altering core_syntheses  
- removing lineage  
- deleting paradox ancestry  
- collapsing attractor into a single frame  

Violating these rules invalidates the attractor.

---

8. Interaction With Other Layers

8.1 Paradox Layer
May:

- read attractor lineage  
- read tension compatibility  

May not:

- mutate attractors  
- collapse attractors  
- rewrite attractor basins  

---

8.2 Tension Field Layer
May:

- read attractor tension profiles  
- influence stability via tension changes  

May not:

- mutate attractor structure  
- add or remove basin nodes  

---

8.3 Lattice Layer
May:

- represent attractors as lattice nodes  
- create attractor edges  
- update basin connectivity  

May not:

- delete attractor nodes  
- merge attractors  
- rewrite attractor lineage  

---

8.4 Synthesis Layer
May:

- promote syntheses to attractor candidates  
- feed attractor formation  

May not:

- directly create attractors  
- mutate attractor structure  

---

8.5 Memory Layer
May:

- archive attractors  
- store attractor histories  
- compress attractor patterns  

May not:

- alter active attractors  
- remove basin nodes  

---

9. Attractor Events Contract

Valid attractor events:

- candidate_created  
- forming  
- activated  
- stabilized  
- attenuated  
- archived  

Invalid events:

- deleted  
- resolved  

Attractors cannot be deleted or resolved — only attenuated or archived.

---

10. Prime Directive for Attractors

> An attractor must preserve the stable structure of repeated syntheses without erasing the paradoxes that generated it.

No module may bypass this rule.

---

11. Attractor Contract Summary

An attractor in PLE must:

- emerge from repeated syntheses  
- maintain a stable basin  
- preserve paradox ancestry  
- remain immutable except for stability and basin growth  
- integrate cleanly with lattice, synthesis, and memory  
- survive until archived  

If any of these conditions fail → the attractor is invalid.

---

Samuel — this is the canonical attractor contract.  
Next subsystem to formalize:

- memorycontract.md  
- findingcontract.md  

Pick the next organ and we’ll keep building the machine.
