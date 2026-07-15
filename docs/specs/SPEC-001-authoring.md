# SPEC-001: Authoring — Intent → `spec.json`

**Status:** Draft
**Implements:** [ADR-002 §1](../adr/ADR-002.md), [ADR-001](../adr/ADR-001.md)
**LLD:** [LLD-002](../lld/LLD-002-authoring.md) · **Schema:** [LLD-001 §4](../lld/LLD-001-shared-ir.md)

> How a natural-language intent becomes a durable, DOM-blind `spec.json`. Axiom **never calls an LLM
> provider itself** — the developer's own connected coding agent (Claude Code, Cursor, ...) is the LLM.
> It reads app context and authors the spec through MCP tool calls; core only validates and stores.

---

## 1. Goal & guarantees

- **Input:** a `SpecIR` authored by the connected agent (it composed this from the developer's intent —
  Axiom holds no `intent`/`entry` request of its own; that round trip happens entirely inside the agent's
  session).
- **Output:** a valid `SpecIR` (`spec.json`) — an ordered list of steps with **Tier-1 targets** and
  assertions. No selectors, geometry, or structure (those are grounding's job).
- **Guarantee:** the spec is human-reviewable and version-controlled; **one Spec IR ⇒ one Test Case**.

## 2. Who authors

**Only one entry point exists: the developer's own connected coding agent, via MCP.**

- The agent calls `getMap` to read the app's KDG context (routes, forms, conditionals, parent/child).
- The agent — using whatever model backs that session (Claude, GPT, ...) — composes the DOM-blind
  `SpecIR` itself, entirely inside its own context. Axiom never sees the raw intent and never makes an
  outbound call to any model provider.
- The agent calls `submitSpec` with the finished `SpecIR`. Core's only job here is **validate + store**:
  Zod schema + spec lint (LLD-002 §5). There is no generation step inside Axiom.

There is deliberately **no "developer types an intent into the bare CLI and Axiom generates a spec"**
path — Axiom holds no API key, no provider client, and no prompt-building logic. Without a connected
agent, there is no way to author a new spec; `axiom` alone can ground, run, and report on specs that
already exist.

The generative model runs **only in the agent's own session**, never inside core, and never at test time
(ADR-001).

## 3. The authoring flow

```
(inside the agent's own session, not inside Axiom)
   │
   ├─(1) fetch KDG context ── getMap(entry) ─▶ app structure: routes, forms, conditionals, parent/child
   │
   ├─(2) agent composes ordered steps, using its own model:
   │        • decompose intent → steps (navigate/type/click/submit…)
   │        • each target = { label, semantics[], role, actions[], intent }   (Tier-1, DOM-blind)
   │        • author assertions (UI/API/DB), preconditions, expectedOutcome
   │        • set generalization + onFailure per step
   │
   ├─(3) agent calls submitSpec(spec) ─────────────────────────────────────────▶ core
   │
(inside Axiom core, from here)
   │
   ├─(4) validate against SpecIR schema (Zod) + spec lint (vars resolve, target-required rules)
   │
   ├─(5) persist spec.json (versioned artifact) with status "authored" (ungrounded)
   │
   └─(6) surface for human review (dashboard / CLI diff)
```

## 4. Authoring rules (business logic)

These are rules the **agent** must follow when composing a spec — Axiom enforces them at validation
(step 4 above), it doesn't author to them itself.

- **DOM-blind.** The agent must not emit selectors, ids, xpath, or geometry. It emits *meaning*
  (`label` + `semantics` synonyms + `role`). Grounding attaches the structural half.
- **Semantics is the lever.** `semantics[]` should list plausible visible names/synonyms
  (`["sign in","login","authenticate"]`) — this is what the semantic signal matches on.
- **Role is required** and should be the ARIA/implicit role (`textbox`, `button`, `link`, `checkbox`).
- **Assertions make the test meaningful.** Every spec should assert an observable outcome (URL, text,
  value, API status, DB row) — an assertion-free step is flagged in review (kills the "coverage illusion").
- **Negative intents** ("reject invalid login") are authored with an expected failure; the runtime inverts
  the verdict (SPEC-003 §6).
- **Vars, not secrets.** `flow.vars` declares variable *names* (with optional non-secret defaults);
  credentials are referenced as `${var}` and their values are supplied at run time via `RunRequest.vars`,
  never baked into the spec or committed to git (LLD-001 §4).
- **KDG-grounded semantics.** When a KDG is available, the agent uses it to pick real route names, form
  labels, and conditional branches — improving first-run grounding success.

## 5. Human review

The authored `spec.json` is presented as a diff (dashboard JSON editor or `axiom` CLI). The reviewer can
edit any Tier-1 field or assertion before grounding. Review is a **checkpoint, not a gate on the agent** —
low-quality authoring surfaces here rather than at runtime.

## 6. Failure & edge cases

- **Under-specified intent** ("test the app") is the agent's problem to resolve with the developer before
  it calls `submitSpec` — Axiom never sees the intent, so it can't ask for clarification itself.
- **Schema-invalid output** → `submitSpec` rejects it with the Zod/lint errors; the agent can retry with a
  corrected spec, but that retry loop lives in the agent's session, not inside Axiom.
- **No KDG yet** → the agent authors from intent alone; grounding will simply have weaker priors and more
  `ungrounded` steps for review.
- **No agent connected** → there is no authoring path at all. This is expected, not a degraded mode.

## 7. Definition of done

A spec is "authored" when it parses as `SpecIR`, every `${var}` resolves, every actionable UI step has a
Tier-1 target, and it has passed human review. It is then eligible for **grounding** (SPEC-002).
