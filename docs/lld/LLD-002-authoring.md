# LLD-002: Authoring Service (`core/authoring`)

**Status:** Draft
**Implements:** [SPEC-001](../specs/SPEC-001-authoring.md), [ADR-002 §1](../../ADR-002.md)
**Depends on:** [LLD-001](./LLD-001-shared-ir.md) (SpecIR, AuthorRequest), [LLD-008](./LLD-008-mcp-server.md) (MCP)

> The only subsystem that touches a **generative** LLM. It composes a DOM-blind `spec.json` from intent,
> grounded in KDG context, and validates + stores it. It runs at authoring/maintenance time, never at run time.

---

## 1. Module shape

```
core/src/authoring/
├── index.ts              # AuthoringService (public interface)
├── kdg-context.ts        # KdgContextProvider — assembles authoring context (getMap)
├── prompt.ts             # PromptBuilder — AuthorRequest + KDG → LLM messages
├── llm-client.ts         # LlmClient interface + providers (anthropic/openai/…) — CLI author path
├── emitter.ts            # parse + validate LLM output → SpecIR
└── store.ts              # persist/read spec.json via storage (LLD-007)
```

## 2. Interfaces

```ts
export interface AuthoringService {
  /** CLI path: core calls a configured LLM provider. */
  author(req: AuthorRequest): Promise<SpecIR>;
  /** Agent path: an external LLM (via MCP) submits a spec; core validates + stores it. */
  submit(spec: unknown): Promise<SpecIR>;
  /** Context an authoring LLM should read (also exposed as the MCP getMap tool). */
  context(entryUrl: string): Promise<KdgContext>;
}

export interface LlmClient {
  complete(messages: LlmMessage[], opts: { jsonSchema: JSONSchema }): Promise<unknown>;
}

export interface KdgContextProvider {
  build(entryUrl: string): Promise<KdgContext>;   // routes, forms, conditionals, parent/child
}
```

`KdgContext` is the versioned app-structure summary the LLM reads (see `core/kdg` — data structure
deferred; the *contract* is: routes/pages, per-page forms & controls with roles/labels, conditionals,
and parent/child containment). Absent a KDG, `context()` returns an empty context and authoring proceeds
from intent alone.

## 3. `author()` algorithm (CLI path)

```ts
async author(req) {
  AuthorRequest.parse(req);
  const ctx = await this.kdg.build(req.entry);
  const messages = this.prompt.build(req, ctx);      // system: rules from SPEC-001 §4
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    const raw = await this.llm.complete(messages, { jsonSchema: specJsonSchema });
    const parsed = SpecIR.safeParse(this.emitter.normalize(raw));
    if (parsed.success && this.lint(parsed.data).ok) {
      return this.store.save(parsed.data);           // status: authored/ungrounded
    }
    messages.push(this.prompt.repair(parsed));       // feed validation errors back
  }
  throw new AuthoringError("spec did not validate after retries");
}
```

- **`MAX_ATTEMPTS = 3`.** Each retry appends the Zod/lint error so the model self-corrects.
- **`submit()`** (agent path) skips generation: it runs `emitter.normalize` + `SpecIR.parse` + `lint`
  only. The agent *is* the LLM; core is the validator/store.

## 4. Prompt contract (`prompt.ts`)

- **System:** the authoring rules from SPEC-001 §4 (DOM-blind; semantics as synonym bag; role required;
  assert an observable outcome; negative intents; vars not secrets) + the `SpecIR` JSON schema.
- **User:** `intent`, `entry`, `vars` (keys only, never values), optional seed `assertions`, and the
  compact `KdgContext`.
- **Output contract:** strict JSON conforming to `SpecIR`. Provider JSON-mode + schema is used where
  available; `emitter.normalize` repairs trivial drift (snake/camel, missing defaults) before parsing.

## 5. Lint rules (beyond schema)

- every `${var}` in any step/assertion exists in `flow.vars`;
- each UI step with an actuating `action` has a `target`; `wait`/`navigate` have none;
- at least one assertion or `expectedOutcome` across the spec (no assertion-free tests);
- `semantics[]` non-empty and not just the role word; `role` is a known ARIA/implicit role.

## 6. Determinism & caching

Authoring is **not** deterministic (it's generative) — which is exactly why it's confined here and gated
by human review. Provider responses are cached by a hash of `(messages, model)` so re-authoring an
unchanged request is free and reproducible within a session.

## 7. Boundaries

- Authoring **never** sees the live DOM and **never** emits selectors (that's grounding, LLD-003).
- It writes only `spec.json` via `storage` (LLD-007); it does not run tests.
- The provider key lives in core config; the CLI/agent never hold it (invariant #6).
