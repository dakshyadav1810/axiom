# Axiom — Walkthrough

A from-scratch guide to running Axiom locally and driving a test through the full
**author → ground → run** loop, starting from a fresh `git clone`.

This complements the [README](README.md) (what Axiom is) and [CONTRIBUTING.md](CONTRIBUTING.md)
(how to contribute). Everything below was verified end-to-end on macOS with Node 20.20.2.

---

## Table of contents

- [1. Prerequisites](#1-prerequisites)
- [2. Clone, install, build](#2-clone-install-build)
- [3. Apply the two required fixes](#3-apply-the-two-required-fixes)
- [4. Start the server](#4-start-the-server)
- [5. Run a test end-to-end](#5-run-a-test-end-to-end)
- [6. The dashboard](#6-the-dashboard)
- [7. Connecting a coding agent (MCP)](#7-connecting-a-coding-agent-mcp)
- [8. Knobs for experiments](#8-knobs-for-experiments)
- [9. Troubleshooting](#9-troubleshooting)
- [10. What is not implemented yet](#10-what-is-not-implemented-yet)

---

## 1. Prerequisites

| Requirement | Notes |
|---|---|
| **Node.js** | `package.json` declares `>=22`. It also runs fine on Node 20 — pnpm prints an `Unsupported engine` warning and proceeds. |
| **pnpm 9.15** | Do **not** install globally. The repo pins `packageManager`, so `corepack pnpm` resolves the right version. Run `corepack enable` once if `corepack` isn't active. |
| **Playwright Chromium** | Grounding and execution launch a real browser. |
| **Network (first run only)** | The first grounding downloads the `Xenova/all-MiniLM-L6-v2` embedding model (~90 MB) to `~/.cache/huggingface`. Everything after that is offline and deterministic. |

Axiom itself never calls an LLM provider and holds no API key. The only model in the loop is
the local embedding model above, plus whatever your own coding agent already talks to over MCP.

> **Note on switching Node versions:** `better-sqlite3` compiles a native binding against your
> Node ABI. If you change Node major versions, re-run `pnpm install` or you'll get a
> `NODE_MODULE_VERSION` mismatch error at startup.

---

## 2. Clone, install, build

```bash
git clone https://github.com/dakshyadav1810/axiom.git
cd axiom

corepack enable            # once, if corepack isn't already active
corepack pnpm install      # ~40s on a cold pnpm store
corepack pnpm build        # ~10s
```

`build` must run before you start anything. Two reasons:

1. **`dist/` is committed to git but is not guaranteed to be current.** A fresh clone ships
   prebuilt output that may predate the source. Always build before running.
2. **The dashboard is served by core, not separately.** `packages/dashboard` builds into
   `packages/core/static`, which does not exist in a fresh clone. Core's static handler roots
   there, so starting core before building the dashboard will fail.

The turbo warning `no output files found for task @axiom/dashboard#build` is expected and
harmless — the dashboard writes outside its own package directory.

Install Chromium if you don't already have it. Playwright is a dependency of `@axiom/core`, not
of the workspace root, so the `--filter` is required — a bare `pnpm exec playwright` fails with
`Command "playwright" not found`:

```bash
corepack pnpm --filter @axiom/core exec playwright install chromium
```

Verify the workspace is sound:

```bash
corepack pnpm test    # 7 tests, all should pass
```

`corepack pnpm lint` currently reports **27 pre-existing errors** on a clean checkout — don't
read that as a broken setup. See [§9](#9-troubleshooting).

---

## 3. Apply the two required fixes

> Skip this section if `git log` already contains these fixes. Check with:
>
> ```bash
> grep -q 'xpath=${xpathFor' packages/core/src/grounding/dom-extractor.ts && echo "fix 1 present"
> grep -q 'return child.pid' packages/cli/src/core-process.ts && echo "fix 2 present"
> ```

As of commit `85d5430`, two bugs block the happy path. Both are one-liners, and without them
nothing below works.

### Fix 1 — grounding crashes on elements without an `id` or `data-testid`

In [`packages/core/src/grounding/dom-extractor.ts`](packages/core/src/grounding/dom-extractor.ts),
`cssSelectorFor()` falls back to `xpathFor(el)`, which emits a single-leading-slash XPath like
`/html[1]/body[1]/p[2]/a[1]`. Playwright only auto-detects XPath when a selector starts with `//`
or `..`, so this gets parsed as CSS and throws. It affects any element without an `id`,
`data-testid`, or input `type` — i.e. most real elements.

```diff
     const tag = el.tagName.toLowerCase();
     const type = el.getAttribute("type");
     if (tag === "input" && type) return `input[type='${type}']`;
-    return xpathFor(el);
+    // Playwright only auto-detects XPath when it starts with `//` or `..`; xpathFor() emits a
+    // single leading slash, so it must be tagged explicitly or it parses as CSS and throws.
+    return `xpath=${xpathFor(el)}`;
   };
```

### Fix 2 — `axiom start` exits immediately and does nothing

In [`packages/cli/src/core-process.ts`](packages/cli/src/core-process.ts), `startCore` ends with
`return child`. `execa()` returns a *thenable that settles only when the spawned process exits*,
and an `async` function **adopts** a returned thenable — so `startCore()` can only resolve once
core *dies*. Since core runs forever, it never resolves: the event loop empties (the child is
`unref`'d), Node exits `0` with no output, and `console.log`, `open()`, and the MCP server never
run. Core itself starts fine, which makes this look like it worked.

```diff
-export async function startCore(config: AxiomConfig, coreEntry: string) {
+export async function startCore(
+  config: AxiomConfig,
+  coreEntry: string,
+): Promise<number | undefined> {
   const child = execa("node", [coreEntry], { ... });
   fs.mkdirSync(".axiom", { recursive: true });
   fs.writeFileSync(PID_FILE, String(child.pid));
   child.unref();

   await waitForHealth(baseUrl(config), 15000);
-  return child;
+  // Return the pid, never `child` itself: execa's result is a thenable that settles only when
+  // core exits, and an async function adopts a returned thenable — so `return child` would make
+  // startCore() hang until the (long-lived) core process died.
+  return child.pid;
 }
```

Rebuild after patching:

```bash
corepack pnpm build
```

---

## 4. Start the server

Scaffold the project state (creates `.axiom/tests/` and `axiom.config.json`):

```bash
node packages/cli/dist/index.js init
```

Then pick one of two ways to run.

### Option A — run core directly (best for experiments)

```bash
node packages/core/dist/main.js
```

Gives you the Fastify server, REST API, WebSocket stream, and dashboard on
`http://127.0.0.1:4319`. No MCP. Stop it with Ctrl-C.

### Option B — run the full CLI (adds the MCP server)

```bash
node packages/cli/dist/index.js start
```

This spawns core as a **detached child**, opens the dashboard, and serves MCP over stdio.
It holds the terminal by design — stdio *is* the MCP transport, so an agent is meant to spawn
it. Because core is detached, it outlives the CLI; stop it from another shell:

```bash
node packages/cli/dist/index.js stop
```

Confirm it's up:

```bash
curl -s http://127.0.0.1:4319/health     # → {"ok":true,"version":"0.1.0"}
```

---

## 5. Run a test end-to-end

### 5.1 Submit a spec

**Axiom has no LLM of its own, so there is deliberately no `axiom author` command.** A spec
enters the system exactly one way: an agent authors it and hands core the finished IR, via
`POST /tests` or the `submitSpec` MCP tool.

Specs are **DOM-blind** — they describe meaning (`label`, `semantics`, `role`, `intent`), never
a selector. This one is verified to work:

```bash
curl -s -X POST http://127.0.0.1:4319/tests \
  -H 'content-type: application/json' -d '{
  "version": "1.0",
  "flow": {
    "id": "example-flow",
    "name": "Example flow",
    "intent": "verify the example.com more info link navigates to IANA",
    "startUrl": "https://example.com",
    "vars": {}
  },
  "steps": [{
    "id": "s1",
    "kind": "ui",
    "intent": "click the more information link",
    "action": "click",
    "target": {
      "label": "More information...",
      "semantics": ["more information", "learn more", "documentation link"],
      "role": "link",
      "actions": ["click"],
      "intent": "navigate to the IANA info page"
    },
    "assertions": [{ "type": "urlContains", "expected": "iana.org" }]
  }]
}'
```

The response returns a `testId` (a UUID) — use it in the next steps.

Specs are linted on submit. The rules that most often bite:

- Every actuating step (`click`, `type`, `select`, `keypress`, `submit`) **must** have a `target`.
- `navigate` and `wait` steps **must not** have a target.
- The spec needs at least one `assertion` or `expectedOutcome` somewhere, or it's rejected.
- Every `${var}` referenced must be declared in `flow.vars`.

### 5.2 Ground it

Grounding opens a browser, extracts candidate elements, and scores each one against the target
with the five signals. This is where the embedding model downloads on first run.

```bash
node packages/cli/dist/index.js ground <testId>
```

Expected result for the spec above: `band: "high"`, `confidence: ~0.78`, and a
`cachedSelector` of `xpath=/html[1]/body[1]/div[1]/p[2]/a[1]`.

If confidence falls below the bands, the step is marked stale for review and grounding stops
there (`stoppedAt`). That's a valid, reviewable outcome — not a crash.

### 5.3 Run it

```bash
node packages/cli/dist/index.js test            # whole suite
node packages/cli/dist/index.js test <testId>   # one test
```

Expected: `<testId>: passed`, exit code 0. No LLM is called on this path.

```bash
node packages/cli/dist/index.js report <runId>  # full stored report
```

A passing report looks like:

```json
{
  "status": "passed",
  "needsReview": false,
  "steps": [{ "stepId": "s1", "status": "passed", "selection": "cached", "band": "high", "durationMs": 1495 }]
}
```

`selection` tells you *how* the element was found: `cached` (selector cache or grounded
artifact) vs `resolver` (drift detected, re-resolved locally).

### 5.4 Where the artifacts live

```
.axiom/
├── cache.db                        # SQLite: embeddings, selector cache, run reports
└── tests/<testId>/
    ├── spec.json                   # DOM-blind intent — what the agent authored
    ├── candidates.json             # every scored candidate + signal breakdown
    └── grounded.json               # spec + resolved selectors — what actually runs
```

`candidates.json` is the interesting one for experiments: it holds the full ranked list with
per-signal scores, so you can see exactly *why* an element won.

---

## 6. The dashboard

Open `http://127.0.0.1:4319`. It's served by core — there is no separate dashboard server to run.

Pick a test to get a JSON editor over its grounded artifact and a **Run test** button. Runs
stream live over WebSocket (`/ws/runs/:id`), so you'll see events arrive in order:

```
run.start → step.start → step.result → run.complete
```

The dashboard is deliberately minimal and never executes anything itself — it only calls core.

For dashboard UI work, run Vite separately for hot reload (it proxies API calls to core on 4319):

```bash
corepack pnpm --filter @axiom/dashboard dev
```

---

## 7. Connecting a coding agent (MCP)

`axiom start` mounts an MCP server over stdio exposing 10 tools:

`getMap`, `getDelta`, `submitSpec`, `groundTest`, `runTest`, `getReport`, `pollRun`,
`healing`, `updateTest`, `deleteTest`

Register it with any MCP client. For Claude Code:

```bash
claude mcp add axiom -- node /absolute/path/to/axiom/packages/cli/dist/index.js start
```

Then drive it in plain language — *"test the login flow"* — and the agent authors the spec,
calls `submitSpec`, grounds it, and runs it.

Every MCP tool proxies to core over REST; nothing shortcuts into core's internals.

---

## 8. Knobs for experiments

Edit `axiom.config.json` (created by `axiom init`) or set `AXIOM_PORT`. Precedence is
CLI flags → env → `axiom.config.json` → defaults.

```jsonc
{
  "port": 4319,
  "headless": false,          // ← watch the browser resolve elements; the most useful knob
  "browser": "chromium",      // chromium | firefox | webkit
  "bands": {
    "high": 0.7,              // ← lower these to accept weaker matches,
    "medium": 0.5             //   raise them to force more steps into review
  },
  "timeouts": { "actionMs": 15000, "navMs": 30000 },
  "embeddingModel": "Xenova/all-MiniLM-L6-v2",
  "dbPath": ".axiom/cache.db",
  "artifactsDir": ".axiom/tests"
}
```

Experiments worth trying:

- **Set `headless: false`** and watch grounding pick elements in real time.
- **Break a selector on purpose.** Ground against a page, change the DOM, re-run, and watch
  `selection` flip from `cached` to `resolver` — that's deterministic healing with no LLM.
- **Squeeze the bands** (e.g. `high: 0.95`) to force steps into the stale/review path, then
  inspect `candidates.json` to see the score breakdown.
- **Weaken the target** (drop `semantics` entries, use a vaguer `label`) and watch confidence fall.

To reset all state, delete `.axiom/` and start over.

---

## 9. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `Unexpected token "/" while parsing css selector "/html[1]/..."` | Fix 1 in [§3](#3-apply-the-two-required-fixes) not applied. |
| `axiom start` prints nothing and exits 0, but core is running | Fix 2 in [§3](#3-apply-the-two-required-fixes) not applied. |
| `ENOENT` on `packages/core/static` at startup | You skipped `pnpm build`. The dashboard build creates that directory. |
| Changes to source have no effect | You're running stale committed `dist/`. Re-run `pnpm build`. |
| `EADDRINUSE` on 4319 | An orphaned core is still running: `kill -9 $(lsof -ti :4319)`. Note `axiom stop` only works if `.axiom/axiom.pid` exists. |
| `NODE_MODULE_VERSION` mismatch from `better-sqlite3` | You changed Node major versions. Re-run `pnpm install`. |
| `WARN Unsupported engine: wanted {"node":">=22"}` | Expected on Node 20. It's a warning; everything works. |
| `pnpm lint` fails on a clean checkout with 27 errors | Pre-existing, not caused by your setup: 7 formatting, 6 `noNonNullAssertion`, 4 `noExplicitAny`, 3 import-order, plus others. `corepack pnpm format` fixes only the formatting subset; `corepack pnpm exec biome check --write .` fixes the auto-fixable rules, but the `noExplicitAny` ones need real edits. Lint is not currently a clean gate. |
| First `ground` is slow | One-time ~90 MB embedding model download. Later runs are cached and offline. |

---

## 10. What is not implemented yet

Don't design an experiment around these — they aren't built:

- **`getMap` / KDG is a stub.** `EmptyKdgContextProvider` always returns
  `{"routes":[],"conditionals":[]}`. The "agent maps your app" story is not implemented.
- **`getDelta` / KDG versioning** returns `{"changed":[]}`.
- **Screenshots and visual replay.** The schema has a slot; nothing populates it.
- **Coverage visibility** and **flaky-test detection**.
- **Test coverage is thin** — 7 unit tests, no integration tests. Both bugs in [§3](#3-apply-the-two-required-fixes)
  survived precisely because nothing exercises the end-to-end path.

Also note: `axiom start` writes `core listening on ...` to stdout, which is the same channel as
the MCP JSON-RPC transport. Lenient clients ignore the non-JSON line; a strict one may complain.
Moving that log to stderr would be the correct fix.

Leftovers from an earlier stack (`packages/core/.venv`, `packages/dashboard/.next`,
`next-env.d.ts`, `bun.lock`) are dead weight — the pnpm + Vite path is the real one. See
[ADR-003](docs/adr/ADR-003.md).
