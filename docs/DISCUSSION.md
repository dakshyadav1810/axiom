# DISCUSSION — Resolver System, Scope, and the Intent→Spec-IR Pipeline

**Date:** 2026-07-07 → 2026-07-08
**Companion to:** [ADR-001](adr/ADR-001.md) (Restrict LLM Usage to Authoring & Maintenance)
**Basis:** deep analysis of `old-repo/` (the previous monolith) to inform the `axiom/packages/core` rebuild.

This document compiles a working session that answered four questions:

1. Where is the latest resolver implementation and how do the 5 signals work?
2. How is a test judged pass/fail, and how does self-heal operate?
3. In the new (ADR-001) pipeline, what does the LLM generate, and where do the resolver *candidates* come from?
4. **What is the testing/healing scope of the resolvers** — how much can they test, how much can they heal, exactly where do they fail, and where are they guaranteed to pass?

All file:line references point into `old-repo/` unless noted.

---

## Part A — The resolver system (current state)

### A.1 Where it lives
The authoritative resolver implementation is `old-repo/axiom-resolvers/`:
- `resolver_router.py` — orchestrator (page characterization → strategy → dynamic weights → scoring → selection)
- `resolvers/{semantic,context,selector,affordance,index}.py` — the five signals; `base.py` — the abstract contract
- `models.py` — `DOMElement`, `ActionNode`, `ActionTarget`, `ResolverCandidate`, `ResolutionResult`, enums
- `executor.py` — Playwright runtime: direct-locator ladder + resolver-fallback ("self-heal") + per-step pass/fail

The test-suite verdict layer is separate, in `old-repo/axiom_recorder/`: `test_engine.py` and `semantic_assertions.py`.

### A.2 Naming reconciliation (important)
The product vocabulary is **affordance, semantics, index, structure, context**. The code's canonical five (`resolvers/__init__.py:19-26`) are **semantic, context, selector, affordance, index**. There is **no `structure.py`**:

> **"structure" = the `SelectorResolver`** — "identify an element by *structural identity*" (PRD §7.4.C). Maps: affordance→affordance, semantics→semantic, index→index, **structure→selector**, context→context.

There is no `Enum` of signals; the registry is the `__init__.py` exports + the router constructor + each resolver's `name` attribute.

### A.3 Implementation state
**All five signals are fully implemented — no stubs/TODOs.** Each is a concrete `BaseResolver` subclass. Resolvers are **pure, deterministic, no-network scorers** (`base.py:17-49`) — they locate elements; they never execute actions.

### A.4 How each signal operates
Shared contract (`base.py:30-49`): `resolve(candidates: list[DOMElement], action: ActionNode, context: dict) -> list[ResolverCandidate]`. Input candidates are the live DOM; `action.target` (an `ActionTarget`) carries every authored/recorded signal.

- **Semantic** (`semantic.py`) — fuzzy **lexical** matching via `rapidfuzz` over 6 channels (text, aria-label, id, name, placeholder, role). **Not embeddings, not LLM.** Exact 1.0, substring 0.6, fuzzy `(ratio/100)·0.5` at ratio≥80; aria 0.9 / id 0.85 / name 0.8 / placeholder 0.7; role +0.2. Soft scorer, never a filter.
- **Context** (`context.py`) — walks the ancestor chain (depth 5) + region boosts (modal 0.4 / form 0.3 / container 0.2 / section 0.1) + `context_path` match + nearby-text Jaccard (>0.3 bonus, <0.1 → −0.15 penalty).
- **Selector = structure** (`selector.py`) — recorded-selector match 1.0, test-id 1.0, tag ±, role exact 0.4 / synonym 0.35 (with implicit-role inference), a single `href` match is decisive.
- **Affordance** (`affordance.py`) — the only pure **filter**: visible+enabled gate, then per-`ActionType` capability; failing candidates are dropped.
- **Index** (`index.py`) — positional last-resort; matches `target.index` against DOM `sibling_index`; ambiguous-with-no-index → returns all candidates tagged `index_required` (fails loudly, never guesses).

### A.5 Weights
Final score = **weighted sum of only 4 signals** (`models.py:182-188`); **index is not weighted** (filter/selector only), affordance folds in as boolean 1.0/0.0:
```
score = semantic·w_sem + context·w_ctx + selector·w_sel + affordance·w_aff
default = {semantic:0.4, context:0.3, selector:0.2, affordance:0.1}
```
Weighting is **heuristic + adaptive** (not ML, not user-config), in three layers:
1. **Strategy routing** (`_select_strategy`, `resolver_router.py:226-256`) — Mixture-of-Experts picks *which* resolvers run & order from page heuristics (`_characterize_page`).
2. **Dynamic weights by page** (`_compute_dynamic_weights`, `:417-488`) — icon-heavy → selector 0.4; text-heavy → semantic 0.5; form/modal → context +0.1; any signal with no data for the target is zeroed; renormalized to 1.0.
3. **Post-hoc correction** (`:373-393`) — any resolver whose best score across all candidates is 0 gets zeroed so "empty voters" can't dilute real signals.

Selection (`_select_best`, `:514-778`): gate `CONFIDENCE_THRESHOLD=0.5`, `CONFIDENCE_MARGIN=0.15`, tiebreaker cascade (recorded-selector → durable anchor → bbox<300px → sibling_index → nearby_text → tag → DOM order) + navigation guard; confidence band high/medium/low (`_classify_confidence`, `:824-843`).

### A.6 Self-heal (resolver-fallback ladder)
There is **no code literally named "self-heal."** It is the resolver-fallback ladder: when recorded/deterministic selectors fail, the executor falls back to the 5-signal pipeline to re-find the element live.
- **Trigger** (`executor.py:806-837`): the deterministic direct-locator ladder (`_resolve_locator_direct_first`) returns `None`.
- **Ladder that must fail first:** direct_strict (test-id→id→name→aria→css→xpath) → direct_recovery (×2) → direct_bundle (role/placeholder/type/text).
- **Heal** (`_resolve_with_resolver_fallback`, `:1902-2050`): loop ≤`MAX_RESOLVER_ATTEMPTS=3`, each re-extracting live DOM → `router.resolve` → `_select_best` → confidence gate → policy gate (`resolver_fallback_policy` default `balanced`) → convert to Playwright locator → **iframe fallback** across child frames.
- **Persistence:** none. Healed selectors are used for the current run only; every run re-heals from scratch. (The new pipeline fixes this via the grounding/cache step — see Part B/C.)
- **Status:** fully implemented, production-grade. Caveats: no persistence; `HOVER` intentionally disabled.

### A.7 Pass/fail determination
Two layers:
- **Executor per-step** (`executor.py`, `models.py`): `ActionResult.success` True only after the action executes; failures set a `FailureReason` (`LOW_CONFIDENCE`, `NOT_INTERACTABLE`, `STATE_BLOCKED`, `VALIDATION_FAILED`, `TIMEOUT`, `NAVIGATION_FAILED`, …). Inline `expected_outcome` (`url_change`/`element_appears`/`text_contains`), preconditions, timeouts (`DEFAULT_TIMEOUT=30000ms`), retries (direct×2, resolver×3, action×3).
- **Test engine** (`test_engine.py`): step status passed/failed/warning/skipped; **run status = `passed` iff `actions_failed==0 and actions_executed>0`** (`:1490`).
- **Semantic assertions** (`semantic_assertions.py`) — deterministic, **not LLM**. Six IDs over run/step/network signals; verdict: any failed → fail; else ≥1 passed & none failed → pass; else inconclusive.
- **Expected-outcome inversion** (`test_engine.py:1908-1955`): for negative variants (`input_validation`, `xss_probe`, `sql_injection`, `double_submit`, …) `expected_outcome="fail"`, so the app **correctly rejecting bad input flips `failed→passed`** (and failing to reject flips `passed→failed`).

---

## Part B — Pipeline & scope

### B.1 The reframe: two inputs, LLM produces one
The resolver matches **two independent inputs**:
- **TARGET (query)** — authored, static, in `flow.json`. **The LLM produces only this.**
- **CANDIDATES (haystack)** — the live browser DOM, re-extracted every run and every heal attempt by `executor._extract_dom_elements` (`:2082-2311`, interactive-element filter at `:2101`). **The LLM is never involved.**

The resolver is the **matcher**; a heal is *re-extract haystack → re-match*. So candidates always come from the live DOM. `old-repo/axiom-resolvers/sample_flow.json` proves a DOM-blind semantic target (`label`+`semantic_text`+`role`) resolves for text-bearing elements, and self-documents its failure modes (`index:0` to split repeated Delete buttons; "may fail due to no text content" on the checkbox / number input).

### B.2 What the LLM can vs. cannot author
- **Tier-1 / Semantic (LLM authors blind):** `url`, `label`, `semantic_text[]`, `role` (implicit), `action_intent`, `value`, and assertions (`url_contains`, `text_contains`, `element_appears`).
- **Tier-2 / Structural (needs a rendered DOM):** `selectors.css`/`xpath`, `attributes`/`id`, `context_path`, `sibling_index`/`index`, `nearby_text`, `disambiguators`, `bounding_box`, exact snapshot text.

**Consequence for ADR-001's runtime (`Cached Selector → Resolvers → Adapter`):** on a freshly authored spec the *Cached Selector step is empty* and the *structure/index tier is dark* until something resolves once. → the pipeline needs a **grounding pass** to plant Tier-2 anchors.

**Two port bugs to fix** (they quietly weaken intent-authored specs):
1. Recorder keeps punctuation in `normalized_text` (`interaction_observer.py:642`) but the executor strips it (`executor.py:2114`) — text comparisons misalign.
2. Runtime candidates keep **only explicit `role`** (`executor.py:2199,2206`), while authoring uses implicit tag→role. An LLM authoring `role:"button"` for a native `<button>` (candidate `role=null`) loses the role bonus. **Fix:** apply the implicit tag→role map to candidates too.

### B.3 The refined pipeline
- **Authoring (LLM, offline, DOM-blind):** decompose intent into ordered steps; each target = role + accessible-name + synonyms + `action_intent`; author assertions + generalization + on_failure. Human-reviewable.
- **Grounding (deterministic, one live run — the new bridge):** walk the semantic flow, run `ResolverRouter` per step against the live DOM; on confident resolution capture the winning element's Tier-2 anchors + a `cached_selector`, write them back into the step; then act so the next step sees correct state. Output: grounded `flow.json`.
- **Runtime (deterministic, ADR-001, no LLM):** cached selector fast-path → miss/changed → extract candidates → `ResolverRouter` → confidence gate → act + assert → low confidence → **mark STALE**.
- **Maintenance (LLM, explicit, developer-triggered):** stale step → LLM re-reads current DOM + old target → regenerate → re-ground → review.

**Discovery is ~70% of the grounding engine already** (`old-repo/*/discovery/`): `browser.extract_dom()` yields resolver-grade anchors; the LLM is kept at semantic-hint level (index-based, no hallucinated selectors); a converter to the resolver's flow schema exists and is wired; auth-session capture works. Gaps: weak fuzzy matcher (replace with the resolver's own semantic matcher), no persisted per-state DOM pool, no state graph (`state_hash` computed but unused), `bounding_box` stubbed, gated behind `AXIOM_ENABLE_DISCOVERY_API`.

### B.4 The scope answer
**Resolvers are a LOCATOR, not a test oracle.** A test = *locate (resolver) → act (adapter) → assert (assertion layer)*. Resolvers bound **location reliability**; the assertion layer bounds **correctness**. They heal location only — never assertions or intent.

**How much they can TEST** — any flow shaped as [locate interactive element → act → assert observable state]: click/type/select/keypress/submit/navigate; assertions on URL, DOM text/visibility/presence, network first-party 4xx/5xx, double-submit, console errors; plus negative/security variants via expected-outcome inversion. → functional E2E, form validation, auth, negative-path, basic network-contract.
**Out of scope entirely:** visual/pixel/layout/CSS/animation correctness; subjective content correctness ("is this the right result"); canvas/WebGL/video; perf/a11y audits.

**How much they can HEAL** — re-locate the same element after DOM change **when enough orthogonal signals still uniquely identify one candidate**: test_id/id/attribute churn, class changes, DOM re-ordering, relocation within the same region, wrapper changes (context depth 5), minor text changes (fuzzy ≥80), ambiguous repeats *only if* a disambiguator was grounded.
**They do NOT heal:** assertion failures / changed behavior (a real bug — correct to fail), removed elements, unreached state, full semantic-identity change with no surviving anchor, simultaneous semantic+structural redesign, ambiguity with no disambiguator, shadow-DOM / cross-origin beyond one iframe fallback.

**EXACTLY where they FAIL:**
1. **Ambiguity below margin** — ≥2 candidates within 0.15, no disambiguator → `SEMANTIC_AMBIGUITY`/`index_required`.
2. **No usable signal (icon-only)** — no text/aria/test_id/attrs → semantic+selector zeroed → score <0.5 → `LOW_CONFIDENCE`.
3. **Semantic + structural drift together** — nothing to anchor on.
4. **Element absent / state not reached** — no candidates.
5. **Navigation-guard ambiguity** — non-nav click where only href-links are near the top.
6. **Affordance mismatch** — no candidate can perform the action type.
7. **Weak/incorrect authored target** — only intent, or wrong/implicit role (bug #2).
8. **Beyond DOM reach** — shadow DOM, canvas, cross-origin frames past the one fallback.

**Where they are GUARANTEED to pass** (given the element exists, is visible+enabled, and its signal is preserved & unique):
1. **Cached selector still matches** (ADR fast path — resolvers not even invoked).
2. **Unique durable anchor** — test_id or unique css/xpath → `SelectorResolver` 1.0 → high band.
3. **Unique strong semantic identity** — accessible-name matches exactly one visible affordable element → high band (most nav links, labeled fields, uniquely-labeled buttons).
4. **Single affordable candidate** after the affordance filter.

**One-line scope statement:** *Resolvers deterministically test-and-heal any flow whose every step targets an element that is (a) interactive, (b) present & visible in a reachable state, and (c) uniquely identifiable by at least one preserved signal — accessible-name, a stable structural anchor, or a grounded positional disambiguator. They cannot locate ambiguous or signal-less elements, and cannot judge visual or semantic correctness.*

---

## Part C — Spec IR, field by field

**One document, three writers:** LLM (Tier-1, offline) · Grounding (Tier-2 + cache, one live run) · Runtime (nothing back; transient results + `stale` flag).

### C.1 Flow envelope
`schema_version`, `name`, `intent` (original NL goal), `start_url`, `variables` (`${...}` params), `steps[]`, grounding-written `grounding_meta`.

### C.2 Step (`ActionNode`)
| Field | Writer | Consumer |
|---|---|---|
| `id`, `action` (`navigate\|click\|type\|select\|keypress\|submit\|wait`) | LLM | dispatch + affordance |
| `target` | LLM→grounding | resolver |
| `value` | LLM | adapter |
| `intent` (per-step NL) | LLM | repair context |
| `generalization` (`same_element\|any_matching\|aggressive\|flexible`) | LLM (grounding may tighten) | `_select_best` strictness |
| `preconditions`, `expected_outcome`, `assertions[]` | LLM | gate + verdict |
| `on_failure` (`abort\|continue\|retry_once\|optional`) | LLM | flow control |
| `grounding` block | grounding | fast-path + status |

### C.3 Target (`ActionTarget`), by tier
- **Tier-1 (LLM):** `label`, `semantic_text[]`, `role`, `action_intent`, `url`.
- **Tier-2 (grounding):** `test_id`, `attributes`, `index`, `element_snapshot{tag,text,normalized_text,role,aria_label,attributes,bounding_box,is_visible,is_enabled,nearby_text}`, `selectors{css,xpath,text,accessibility,test_id}`, `context_path[]`, `disambiguators{row_identity,nearby_text_hash,sibling_index,sibling_count}`.

### C.4 `grounding` block
```json
{ "status":"grounded|ungrounded|stale", "confidence_band":"high|medium|low",
  "confidence_score":0.0, "cached_selector":"#username",
  "cache_strategy":"test_id|id|css|xpath|role_name",
  "grounded_at":"ISO8601", "grounded_url":"..." }
```

### C.5 Assertion grammar
- `expected_outcome`: `{type: url_change|element_appears|text_contains, value}`
- `assertions[]`: `{kind: url_contains|text_contains|element_visible|element_absent|network_no_5xx|no_double_submit, value?, target?}`
- `preconditions`: `{url_contains?, element_visible?, element_enabled?, modal_visible?}`

### C.6 Worked example — one step, both states

**Authored (Tier-1 only):**
```json
{ "id":"s2","action":"type","value":"${username}","intent":"Enter the username",
  "target":{"label":"Username","semantic_text":["username","email","user"],
            "role":"textbox","action_intent":"input"},
  "generalization":"same_element","preconditions":{"url_contains":"/login"},
  "on_failure":"abort","grounding":null }
```

**Grounded (Tier-1 + Tier-2 + cache):**
```json
{ "id":"s2","action":"type","value":"${username}","intent":"Enter the username",
  "target":{ "label":"Username","semantic_text":["username","email","user"],"role":"textbox","action_intent":"input",
    "test_id":"username","attributes":{"id":"username","name":"username","type":"text"},"index":null,
    "element_snapshot":{"tag":"input","text":"","normalized_text":"","role":"textbox","aria_label":null,
      "attributes":{"id":"username","name":"username","type":"text"},
      "bounding_box":{"x":360,"y":220,"width":240,"height":38},"is_visible":true,"is_enabled":true,"nearby_text":"Username"},
    "selectors":{"css":"form#login > div:nth-of-type(1) > input#username",
      "xpath":"/html/body/div[2]/form/div[1]/input","text":null,
      "accessibility":"textbox[name=\"Username\"]","test_id":"username"},
    "context_path":[{"tag":"form","role":null,"class_name":"login","attributes":{"id":"login"}}],
    "disambiguators":{"row_identity":null,"nearby_text_hash":"a1b2c3d4e5f6","sibling_index":0,"sibling_count":1} },
  "generalization":"minimal","preconditions":{"url_contains":"/login"},"on_failure":"abort",
  "grounding":{"status":"grounded","confidence_band":"high","confidence_score":1.0,
    "cached_selector":"#username","cache_strategy":"test_id",
    "grounded_at":"2026-07-08T10:12:00Z","grounded_url":"https://app.example.com/login"} }
```

### C.7 Transient runtime objects (never persisted)
`DOMElement` (candidate) · `ResolverCandidate` (candidate + per-signal scores + reasons) · `ResolutionResult` (winner + band + failure_reason) · `StepResult`/`FlowResult`.

---

## Part D — Information flow graph

```
                    ┌──────────────── AUTHORING (LLM, offline) ────────────────┐
 [User prompt]      │  P0 ─▶ LLM ─▶ P1                                          │
 "test the login    │  P0 = {intent, start_url, vars, [optional DOM snapshot]} │
  flow"             │  P1 = Authored Flow IR  (Tier-1 only, grounding:null)     │
                    └───────────────────────┬──────────────────────────────────┘
                                            │ P1
                                            ▼
        ┌──────────── GROUNDING (deterministic, ONE live run) ─────────────────┐
        │ launch browser @ start_url;  FOR EACH step:                          │
        │   P2 = extract_dom_elements(page)      ── List[DOMElement] (haystack) │
        │   P3 = ResolverRouter.resolve(target_T1, P2) ── ResolutionResult      │
        │   band≥medium ? ── yes ─▶ serialize winner → Tier-2 anchors + cache   │
        │                          then ACT (so next step sees right state)     │
        │                └─ no ─▶ grounding.status="ungrounded" (author review)  │
        │ P4 = Grounded Flow IR (Tier-1+Tier-2+cache) ─▶ PERSIST                 │
        └───────────────────────┬──────────────────────────────────────────────┘
                                │ P4 (stored)
                                ▼
        ┌──────────── RUNTIME (deterministic, NO LLM — ADR-001) ───────────────┐
        │ FOR EACH step:                                                        │
        │  ① CACHED SELECTOR:  R1 = locator(grounding.cached_selector)          │
        │        unique&visible? ─yes─▶ locator ✓ (skip resolvers)              │
        │                        └─no/changed─┐                                 │
        │  ② RESOLVER HEAL ◀───────────────────┘  loop ≤3:                       │
        │        R2 = extract_dom_elements(page)  ── candidates                  │
        │        R3 = ResolverRouter.resolve(target_T1+T2, R2)                   │
        │        gate: score≥0.5, margin≥0.15, band×policy                       │
        │        ├─ confident ─▶ locator ✓                                       │
        │        └─ low ─▶ iframe fallback ─▶ still low ─▶ ✗ STALE               │
        │  ③ ACT:    R4 = adapter.dispatch(action, locator, value)  (Playwright) │
        │  ④ ASSERT: R5 = eval(preconditions, expected_outcome, assertions,      │
        │                      network/console) → StepResult                     │
        └───────────────────────┬──────────────────────────────────────────────┘
                                │ R6 = FlowResult + verdicts
             ┌──────────────────┼─────────────────────┐
             ▼                  ▼                      ▼
        all steps ✓       step ✗ STALE (locate)   step ✗ ASSERT (behavior)
        PASS              → maintenance queue      → real BUG, report
                                │
                                ▼
        ┌──────── MAINTENANCE (LLM, explicit, developer-triggered) ────────────┐
        │ M0 = {stale step, its intent, OLD target, FRESH DOM snapshot}         │
        │ M0 ─▶ LLM ─▶ M1 = re-authored Tier-1 target                           │
        │ M1 ─▶ re-run GROUNDING for that step ─▶ P4' ─▶ review ─▶ store         │
        └──────────────────────────────────────────────────────────────────────┘
```

**Stage narration:**
- **① Authoring.** `P0 {intent, start_url, vars, [DOM snapshot]}` → LLM decomposes into ordered Tier-1 steps + assertions + control → `P1`. DOM-blind unless a discovery snapshot is supplied (then the LLM picks elements by index for higher fidelity).
- **② Grounding (the bridge).** Same loop as runtime heal, but its job is to *capture*: extract live candidates (`P2`), resolve Tier-1 hints against them (`P3`), copy the winning candidate's real anchors back into the step (`element_snapshot`, `selectors`, `context_path`, `disambiguators`, `index`) + choose `cached_selector`, set `generalization=minimal` if a durable anchor exists, then act. Unresolved steps → `ungrounded` for author review.
- **③ Runtime.** Cached selector first (`R1`, O(1), no resolvers). On miss, resolver heal re-extracts candidates (`R2`) and re-resolves with the full Tier-1+Tier-2 target (`R3`) — now structure/index signals light up. Gate → accept or STALE. Adapter acts (`R4`), assertions evaluate (`R5`) → `StepResult` → aggregate `FlowResult` (`R6`).
- **④ Two failure exits:** locate failure → **STALE** (drift → maintenance, never an LLM at runtime); assert failure → **real BUG** (element found, app misbehaved — resolvers never touch this).
- **⑤ Maintenance.** `M0 {stale step + intent + old target + fresh DOM}` → LLM re-authors Tier-1 → re-ground that step → review → store. The only place an LLM re-enters after authoring, on explicit trigger only.

---

## Final note

**Where we are.** The resolver engine is complete and production-grade in `old-repo/axiom-resolvers`, but it was built for *recorded* ground-truth targets. The rebuild in `axiom/packages/core` co-locates resolvers + execution under unified models, and ADR-001 fixes the runtime as deterministic with LLM confined to authoring/maintenance. The intent→spec authoring path is partially prototyped in the (blocked, flag-gated) `discovery/` module, which already extracts resolver-grade anchors and converts to the resolver's flow schema — it is the natural home for the **grounding** step.

**The core insight of this discussion.** The confusion of "resolvers need candidates — where do they come from?" dissolves once the two inputs are separated: **the LLM authors the query (Tier-1 target + assertions); the live browser DOM supplies the candidates; a one-time grounding run uses the resolver to copy the winning candidate's real anchors back into the query (Tier-2 + cached selector); runtime then matches query→candidates deterministically and heals by re-matching, escalating to STALE — never to an LLM — when confidence is too low.** Grounding is what turns a DOM-blind intent into an ADR-compliant, cache-backed, self-healing spec.

**The one open decision.** How the Tier-2 anchors get planted — i.e. the grounding strategy:
- **A. Discovery-grounded authoring** — most autonomous ("test the login flow" with zero recording), highest build cost (needs state graph + persisted DOM pools; strengthen the fuzzy matcher).
- **B. Semantic-spec + first-run grounding** — lightest; LLM writes Tier-1, a deterministic first run caches anchors; first run can miss on icon-only/ambiguous steps.
- **C. Record-then-generalize** — highest anchor fidelity, least autonomous (needs a recording session).

These are not mutually exclusive — B is the minimal viable core; A is where autonomy comes from; C is the high-fidelity fallback for hard flows. Recommended next artifact: a concrete **spec-IR JSON schema** (Part C formalized) plus a thin **B-path prototype** (intent → LLM → semantic spec → grounding run → resolve → execute) to validate the loop end-to-end before investing in discovery's state graph.
