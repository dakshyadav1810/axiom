# Axiom High-Level Design (HLD) Draft v3

## 1. Executive Summary
Axiom is an open-source testing platform for AI-first teams, built to eliminate the "coverage illusion" and "selector drift" inherent in LLM-generated tests. By decoupling the frontend Dashboard from the execution engine, and treating testing as a sequence of adapter-driven steps, Axiom operates as a robust platform. The centerpiece of Axiom's resilience in UI testing is the deterministic **Multi-Signal Resolver** ("geometry first, AI second"), which intelligently survives UI changes without relying on costly and slow LLM invocations for every broken test.

## 2. System Architecture (Platform Overview)

Axiom is designed as a modular platform with a strict separation of concerns.

### 2.1 Core Components
1. **Node.js Orchestrator (`axiom-cli`)**: A thin orchestration layer exposing the `npx axiom` entry point. It handles MCP communication with the developer's IDE, manages the Python backend lifecycle, and orchestrates dashboard startup.
2. **Python Backend (`axiom-core`)**: Owns *all* execution logic. It houses the Execution Engine, Playwright runner, recorders, the multi-signal resolver, and the API layer.
3. **Independent Dashboard (`axiom-dashboard`)**: A Progressive Web App (React/Next.js) that communicates exclusively via HTTP/WebSocket APIs. It is backend-agnostic (local, cloud, or enterprise) and never interfaces directly with internal subsystems.

### 2.2 Repository Structure
The project operates as a monorepo:
```text
axiom-repo/
├── packages/
│   ├── axiom-cli/          (Thin Node.js orchestrator & MCP interface)
│   ├── axiom-dashboard/    (Independent React/Next.js PWA)
│   └── axiom-core/         (Python Backend API & Execution Engine)
```

---

## 3. Data Storage Strategy

- **Source of Truth (JSON)**: Test definitions and recorded flows live purely as structured JSON files committed to the developer's Git repository. This enables PR-level reviews and ensures tests live alongside the code they test.
- **Cache & Ephemeral Data (`axiom/cache.db` SQLite)**: A local SQLite database is used strictly for things that can be regenerated or represent point-in-time data:
  - DOM embeddings
  - Execution history & replay metadata
  - Resolver cache
  - Screenshots & coverage indexes
  - LLM cache & analytics

---

## 4. Key Workflows

### 4.1 Unified Test Format
Tests are agnostic to the execution method. A single checkout flow might look like:
```json
{
  "steps": [
    { "type": "api", "method": "POST", "endpoint": "/cart", "payload": {...} },
    { "type": "ui", "action": "click", "selector_hints": {...} },
    { "type": "api", "method": "GET", "endpoint": "/order/123" }
  ]
}
```

### 4.2 Test Execution Flow
1. **Execution Engine** loads the JSON test definition.
2. It iterates through the `steps` array.
3. If `type == "api"`, the **API Adapter** executes the HTTP request and asserts the response.
4. If `type == "ui"`, the **UI Adapter** takes over:
   - The **Multi-Signal Resolver** attempts to locate the element using geometric/semantic signals.
   - Playwright performs the action.
5. All results, timings, and screenshots are saved to the `cache.db` for the dashboard to render.

---

## 5. The Core: Multi-Signal Resolver Architecture

The Resolver is the subsystem responsible for maintaining element identity across UI mutations. When a previously recorded element is not found via its strict Playwright locator, the Resolver re-identifies it deterministically using five distinct signals.

### 5.1 Signal Capture & Representation
During recording, the UI Recorder captures a "snapshot" of the target element, containing the following signals:

1. **Affordance (Visual/Interactive properties)**
   - *Representation*: Tag name (e.g., `button`, `a`), computed role, visibility, size boundaries (width/height ratios).
2. **Semantics (Meaning/Content)**
   - *Representation*: Text content, `aria-label`, placeholder text, `alt` attributes, `title`.
3. **Structural Position (DOM Geometry)**
   - *Representation*: Depth in DOM, CSS path signature, relative parent-child constraints.
4. **Context (Neighborhood)**
   - *Representation*: Nearby semantic landmarks (e.g., "closest heading text", "adjacent button text").
5. **Index (Order)**
   - *Representation*: Ordinal position among similar elements (e.g., 3rd list item).

### 5.2 Normalization & Similarity Scoring
When re-identifying an element, the live DOM state is parsed into candidate elements. The Resolver computes a weighted similarity score `S(c)` for each candidate `c` compared to the recorded snapshot `r`.

- **Semantic Normalization**: Text is lowercased, stripped of punctuation, and evaluated using Levenshtein distance or a fast embedding cosine similarity.
- **Structural Normalization**: Paths are abstracted to ignore dynamic utility classes (e.g., Tailwind classes are stripped; semantic tags and IDs are prioritized).

**Scoring Algorithm**:
```text
S(c) = (W_aff * AffordanceScore) + 
       (W_sem * SemanticScore) + 
       (W_str * StructuralScore) + 
       (W_ctx * ContextScore) + 
       (W_idx * IndexScore)
```
*Initial Weights (subject to tuning)*: Semantics and Context carry the highest weight (`W_sem = 0.4`, `W_ctx = 0.25`), followed by Affordance (`W_aff = 0.2`), Structure (`W_str = 0.1`), and Index (`W_idx = 0.05`).

### 5.3 Confidence Thresholds & Decision Flow
The highest-scoring candidate dictates the execution path based on predefined thresholds:

- **High Confidence (e.g., > 0.85)**: *Deterministic Resolution*. The element is confidently re-identified. Playwright executes the action. No LLM invoked.
- **Moderate Confidence (e.g., 0.60 - 0.85)**: *LLM Escalation*. The resolver requests the LLM to verify the candidate using the DOM snippet. If confirmed, a **Heal Suggestion** event is emitted.
- **Low Confidence (e.g., < 0.60)**: *Failure*. The element is assumed removed or fundamentally changed. The test fails, and a Heal Suggestion is requested from the LLM for the developer to review.

### 5.4 Heal Suggestions
Heal Suggestions are shared events produced by the Resolver. They are surfaced simultaneously via:
1. **MCP Responses**: To alert the developer natively within their IDE (Claude/Cursor).
2. **Dashboard**: For a visual diff and manual approval/rejection.

### 5.5 Current Implementation Details
Based on the existing codebase (`axiom-resolvers` and `axiom_recorder`):
- **Resolver Router (`resolver_router.py`)**: Implements a Mixture-of-Experts approach. It analyzes `PageCharacteristics` (e.g., text density, icon-only ratio, presence of forms/modals) to dynamically route resolution through specific expert resolvers (`SemanticResolver`, `ContextResolver`, `SelectorResolver`, `AffordanceResolver`, `IndexResolver`). It currently uses hardcoded confidence thresholds (e.g., `HIGH_CONFIDENCE_THRESHOLD = 0.78`).
- **Recorders (`recorder.py` & `state_aware_recorder.py`)**: The recording engine is built on asynchronous Playwright APIs. The `StateAwareRecorder` captures advanced intelligence layers including DOM snapshots, interaction graphs, and semantic page classifiers before and after every interaction, laying the groundwork for the required signal extraction.

### 5.6 Key Areas for Development
To realize the target platform architecture, the following areas require focused development:
1. **Network Recorder Module**: Build the separate Network Recorder to passively capture HTTP requests using Playwright interception during UI tests, moving towards the unified test format.
2. **Unified Execution Engine**: Refactor the current `test_engine.py` into a Step Dispatcher that routes to either the UI Adapter or the new API Adapter.
3. **Resolver Tuning & Embeddings**: Upgrade the `SemanticResolver` to utilize local embedding models (e.g., ONNX) rather than basic text comparisons, and make the scoring weights fully dynamic.
4. **Node.js MCP Orchestrator**: Build the lightweight `axiom-cli` package in TypeScript to serve as the local entry point, stripping any heavy Python execution logic out of the current JS/TS scaffolding.
5. **Dashboard Decoupling**: Ensure the dashboard communicates entirely via REST/WebSockets from `packages/axiom-dashboard` to the Python backend API without tight coupling.

---

## 6. Benchmarking & Evaluation Methodology

To validate the "geometry first" moat, the Resolver must be benchmarked against standard Playwright locators and existing AI self-healing tools.

### 6.1 Evaluation Metrics
1. **Accuracy (Success Rate)**: Percentage of elements successfully re-identified after a UI mutation.
2. **False Positives**: Instances where the Resolver clicked the *wrong* element instead of failing. (Critical metric: must approach 0).
3. **False Negatives**: Instances where the element was present but the Resolver failed to meet the confidence threshold.
4. **Latency (Resolution Time)**: Time taken to resolve a missing element deterministically (Target: < 200ms) vs. via LLM (Target: ~2-5s).

### 6.2 Comparison Strategy
We will build a controlled benchmark suite consisting of typical UI mutations:
- **Class / CSS Framework Migration** (e.g., Bootstrap to Tailwind).
- **DOM Restructuring** (e.g., wrapping a button in a new `div` or moving it to a sidebar).
- **Copy Changes** (e.g., "Add to Cart" -> "Buy Now").
- **A/B Testing Variants** (e.g., visual layout shifts).

**The Baseline**: Standard Playwright Codegen scripts (brittle).
**The Goal**: Axiom Resolver successfully completes >90% of the benchmark flows deterministically without LLM intervention, with 0 false positives.

---

## 7. Network Recorder & Future Capabilities
The **Network Recorder** uses Playwright's built-in network interception to capture HTTP requests and responses passively during UI interactions. While initially used for debugging and context, this metadata forms the foundation for a future feature: automatically suggesting the conversion of slow UI test steps into fast API test steps (UI-to-API conversion) within the unified JSON workflow definition.