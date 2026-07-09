# SPEC-001: Authoring — Intent → `spec.json`

**Status:** Draft
**Implements:** [ADR-002 §1](../../ADR-002.md), [ADR-001](../../ADR-001.md)
**LLD:** [LLD-002](../lld/LLD-002-authoring.md) · **Schema:** [LLD-001 §4](../lld/LLD-001-shared-ir.md)

> How a natural-language intent becomes a durable, DOM-blind `spec.json`. Authoring is the one place a
> **generative** LLM participates, and it participates through MCP at authoring time only.

---

## 1. Goal & guarantees

- **Input:** `AuthorRequest = { intent, entry, vars, assertions? }` (LLD-001 §7).
- **Output:** a valid `SpecIR` (`spec.json`) — an ordered list of steps with **Tier-1 targets** and
  assertions. No selectors, geometry, or structure (those are grounding's job).
- **Guarantee:** the spec is human-reviewable and version-controlled; **one Spec IR ⇒ one Test Case**.

## 2. Who authors

Two entry points, same output:
- **Coding agent** (e.g. Claude Code) via the **MCP** control plane — the agent is the LLM; core supplies
  KDG context and validates/stores the emitted spec.
- **Developer** via `axiom author "<intent>" --entry <url>` — core calls a configured LLM provider at
  authoring time, then stores the spec for review.

Either way the generative model runs **only here**, never at test time (ADR-001).

## 3. The authoring flow

```
AuthorRequest
   │
   ├─(1) fetch KDG context ── getMap(entry) ─▶ app structure: routes, forms, conditionals, parent/child
   │
   ├─(2) LLM composes ordered steps:
   │        • decompose intent → steps (navigate/type/click/submit…)
   │        • each target = { label, semantics[], role, actions[], intent }   (Tier-1, DOM-blind)
   │        • author assertions (UI/API/DB), preconditions, expectedOutcome
   │        • set generalization + onFailure per step
   │
   ├─(3) validate against SpecIR schema (Zod) + spec lint (vars resolve, target-required rules)
   │
   ├─(4) persist spec.json (versioned artifact) with status "authored" (ungrounded)
   │
   └─(5) surface for human review (dashboard / CLI diff)
```

## 4. Authoring rules (business logic)

- **DOM-blind.** The LLM must not emit selectors, ids, xpath, or geometry. It emits *meaning*
  (`label` + `semantics` synonyms + `role`). Grounding attaches the structural half.
- **Semantics is the lever.** `semantics[]` should list plausible visible names/synonyms
  (`["sign in","login","authenticate"]`) — this is what the semantic signal matches on.
- **Role is required** and should be the ARIA/implicit role (`textbox`, `button`, `link`, `checkbox`).
- **Assertions make the test meaningful.** Every spec should assert an observable outcome (URL, text,
  value, API status, DB row) — an assertion-free step is flagged in review (kills the "coverage illusion").
- **Negative intents** ("reject invalid login") are authored with an expected failure; the runtime inverts
  the verdict (SPEC-003 §6).
- **Vars, not secrets.** Credentials are referenced as `${var}`; values are injected at run time, never
  baked into the spec.
- **KDG-grounded semantics.** When a KDG is available, the LLM uses it to pick real route names, form
  labels, and conditional branches — improving first-run grounding success.

## 5. Human review

The authored `spec.json` is presented as a diff (dashboard JSON editor or `axiom` CLI). The reviewer can
edit any Tier-1 field or assertion before grounding. Review is a **checkpoint, not a gate on the LLM** —
low-quality authoring surfaces here rather than at runtime.

## 6. Failure & edge cases

- **Under-specified intent** ("test the app") → the LLM asks for clarification (agent path) or the CLI
  prompts for an entry URL / scope. No spec is emitted from an unresolvable intent.
- **Schema-invalid output** → rejected and regenerated (LLD-002 retries with the validation error).
- **No KDG yet** → authoring proceeds from intent alone; grounding will simply have weaker priors and
  more `ungrounded` steps for review.

## 7. Definition of done

A spec is "authored" when it parses as `SpecIR`, every `${var}` resolves, every actionable UI step has a
Tier-1 target, and it has passed human review. It is then eligible for **grounding** (SPEC-002).
