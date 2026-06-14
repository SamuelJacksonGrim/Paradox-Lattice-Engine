# Integrating the Paradox Lattice Engine

> A deeper guide than the top-level README: what PLE actually is, what it does
> with a contradiction, and exactly how to wire it into a host system —
> including a local LLM running in a terminal.

This folder is **documentation**. The integration *code* (the external API,
hooks, the RFE-Core2 bridge) lives in the Python package at
[`../ple/integration/`](../ple/integration/), and the implemented reference
adapter is [`../ple/integration/rfecore2hook.py`](../ple/integration/rfecore2hook.py).

---

## 1. What PLE is (and what it is not)

PLE is a **cognitive sidecar** that treats contradictions as a *substrate to
build on*, not errors to delete. You attach it to a thinking system; it is not
an instrument you point at one.

- It is **not a measurement tool.** It does not grade a model's outputs. (The
  only measurement tool here is `examples/benchmark_overhead.py`, which measures
  *PLE's own* runtime cost.)
- It is **not a resolver.** It does not pick a winning frame. Resolution is
  optional; a paradox is allowed to persist forever as useful structure.
- It **is** a contradiction engine: when two views conflict, PLE asks *"what
  becomes possible because this contradiction exists?"* and grows structure —
  tension fields, a lattice, syntheses, attractors, and eventually validated
  findings — from the friction.

The central inversion:

> Most systems eliminate contradictions. PLE metabolizes them.

## 2. What it does with a contradiction

You submit **frames** (positions, model outputs, hypotheses). PLE detects where
they conflict and runs a six-layer pipeline:

```
Paradox → Tension Field → Lattice → Synthesis → Attractor → Finding → Memory
```

| Layer | Produces | Meaning |
|---|---|---|
| Paradox | `ParadoxNode` | the canonical contradiction (immutable, never deleted) |
| Tension Field | `TensionField` | contradiction intensity as geometry |
| Lattice | `ParadoxLattice` | the structural graph of paradoxes/frames/syntheses |
| Synthesis | `SynthesisRecord` | a new structure: `coexistence`, `hybridization`, or `reframing` |
| Attractor | `Attractor` | a *stable* structure that recurrence has reinforced |
| Finding | `Finding` | validated cognitive output, traceable to its source paradoxes |
| Memory | `ParadoxMemoryEpisode` | the full paradox→finding episode, stored forever |

**Recurrence is the engine of emergence.** The same contradiction processed
*twice* forms an attractor, and a finding is extracted the moment stability
crosses threshold — typically on the second encounter. Process it once and
nothing crystallizes; that's expected.

## 3. The integration contract

**Input — a frame:**

```python
{"name": str, "claims": {key: value}}
```

A **contradiction** is two frames that share a claim key with conflicting
values (after canonicalization). Example:

```python
WAVE     = {"name": "wave_theory",     "claims": {"light_is": "a wave"}}
PARTICLE = {"name": "particle_theory", "claims": {"light_is": "a particle"}}
# shared key "light_is", conflicting values -> a paradox
```

**Output — `PipelineResult`:**

```python
result.paradox_nodes   # list[ParadoxNode]
result.tension_field   # TensionField
result.lattice         # ParadoxLattice
result.syntheses       # list[SynthesisRecord]
result.attractors      # list[Attractor]   (populated once recurrence stabilizes)
result.findings        # list[Finding]     (one per attractor, ever)
result.horizons        # resolution horizons (collapse probabilities)
result.metrics         # ecology metrics: tension_load, paradox_density, ...
result.episode         # ParadoxMemoryEpisode
```

PLE stays **dormant** when frames don't actually conflict — feeding agreeing
frames is cheap and produces no paradox.

## 4. Wiring it in — the minimum

```python
from ple import ParadoxLatticeEngine
from ple.integration import external_api

engine = ParadoxLatticeEngine()  # stateful; recurrence accumulates across calls

# two frames:
result = engine.process(WAVE, PARTICLE)

# or many at once (pairwise; ≥3 conflicting frames nest under the hottest):
result = engine.process_many([WAVE, PARTICLE, FIELD])

# or via the facade (validates "≥2 frames", routes 2 vs many for you):
result = external_api.submit_frames(engine, [WAVE, PARTICLE], context={"src": "demo"})

# harvest validated cognitive output whenever you like:
findings = external_api.get_findings(engine, validated_only=True)
report   = external_api.ecology_report(engine)   # observability snapshot
```

Keep **one long-lived engine** per cognitive context — emergence depends on it
seeing the same contradiction more than once.

## 5. The real work: turning host signal into frames

PLE ships no built-in connector for any specific host because the modeling
decision — *what is a frame, and which claim key makes two of them conflict?* —
is yours. The implemented reference,
[`rfecore2hook.py`](../ple/integration/rfecore2hook.py), discretizes one
RFE-Core2 cycle's evaluator telemetry into eight frames sharing claim keys like
`coherence_band` and `threat_level`; copy its shape for your host.

### Wiring a local LLM running in a terminal

The trick is to manufacture *disagreement* and express it as frames that share
a claim key. Options, model-agnostic unless noted:

- **Multi-sample.** Sample the model several times; turn distinct answers into
  frames that share one claim key, so divergent samples contradict:

  ```python
  samples = [llm(prompt) for _ in range(5)]
  frames = [
      {"name": f"sample_{i}", "claims": {"answer": normalize(s)}}
      for i, s in enumerate(samples)
  ]
  result = external_api.submit_frames(engine, frames, context={"prompt": prompt})
  # identical samples -> no paradox (dormant); divergent -> paradox -> synthesis
  ```

  Ask the *same* prompt again later; if the model keeps splitting the same way,
  recurrence forms an attractor and a finding ("this prompt is genuinely
  ambiguous, and here's the synthesis that holds").

- **Multi-persona / multi-prompt.** Run the question under different framings
  (optimist/pessimist, two system prompts); each becomes a frame on a shared
  claim key.

- **Two-model / ensemble disagreement.** Frames from two different local models
  answering the same question — their conflicts are the substrate.

- **Logprob-derived alternatives (needs a backend exposing them).** The top-k
  candidate completions become competing frames.

What you get back is *structure about the disagreement* — a synthesis frame,
and on recurrence a validated finding — not a chosen answer. PLE never collapses
the contradiction for you.

## 6. Optional power

**Hooks** (read-only observers over the typed event stream):

```python
from ple.integration import system_hooks

system_hooks.register(engine, "finding", on_finding)        # channels below
system_hooks.register(engine, "synthesis", on_synthesis)
```

Channels: `paradox | tension_field | lattice | synthesis | resolution |
attractor | finding | memory`.

**LAE-style transition trigger** — treat paradox-driven tension as a signal a
transition layer (like the Liminal Anchor Engine) can react to:

```python
system_hooks.register_transition_trigger(engine, on_tension)
```

**Ecology report** (observability for host dashboards): `active_paradoxes`,
`mean_intensity`, `lattice_nodes/edges`, `episodes`, `findings`,
`recurring_lattice_patterns`, `events_routed`, per-attractor stability.

## 7. Behaviors worth knowing

- **Habituation → collapse → flare.** A contradiction synthesized over and over
  drains in intensity and attenuates; if it returns after collapsing, it flares
  back to active. Collapse is never resolution.
- **Append-only, forever.** No layer may delete a paradox; archived paradoxes
  stay queryable. Findings are always traceable through lineage to their source
  paradoxes.
- **Three synthesis methods only.** `coexistence` (partition domains),
  `hybridization` (new frame subsumes both), `reframing` (dissolve at a higher
  order — marked, never silently discarded).

## 8. Common pitfalls

- **Submitting non-conflicting frames and expecting output.** No shared,
  conflicting claim key → no paradox → dormant. Make the disagreement explicit
  on a shared key.
- **Using a fresh engine every call.** Recurrence (and therefore attractors and
  findings) needs a persistent engine instance.
- **Expecting a resolved answer.** PLE produces *findings about* a
  contradiction, not a verdict that ends it.
- **Reaching past the facade.** Use `ParadoxLatticeEngine` /
  `ple.integration.external_api`; models, layers, and actor-guarded fields are
  internal.

---

See [`../README.md`](../README.md) for the overview and the per-subsystem
`*_contract.md` files for the non-negotiable behavioral rules.
