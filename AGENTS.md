# AGENTS.md

> Engineering guidelines for contributors and AI coding agents working on **Axiom**.
>
> This document defines the architectural boundaries, development philosophy, and engineering conventions for the project. It should be treated as the authoritative guide for implementing new features and modifying existing systems.
>
> **Stack:** Axiom is a single-language **TypeScript on Node.js** project — see [ADR-003](ADR-003.md) and [PLAN-001](PLAN-001.md). Earlier references to Bun, Python, or a standalone Next.js dashboard are superseded.

---

# Project Vision

Axiom is an open-source, AI-native software testing platform designed for modern development teams.

Unlike traditional testing frameworks that rely on brittle selectors or AI-first systems that invoke large language models for every failure, Axiom follows a **deterministic-first** philosophy.

The platform combines:

- Intelligent recording
- Multi-signal element resolution
- Unified UI + API testing
- Rich debugging and visualization
- AI-assisted healing only when deterministic methods are insufficient

The objective is to build a platform that remains reliable as applications evolve while keeping tests fast, explainable, version-controlled, and developer-friendly.

---

# Repository Structure

```
axiom/
│
├── packages/
│   ├── shared/     (Zod IR — single source of truth)
│   ├── cli/        (orchestration + MCP server)
│   ├── core/       (Fastify server — all business logic)
│   └── dashboard/  (Vite SPA — bundled into core)
│
└── docs/
```

The whole workspace is TypeScript on Node.js LTS (22+), managed with pnpm workspaces + Turborepo.

## Package Responsibilities

### shared

Technology:
- TypeScript
- Zod

Responsibilities:

- The Spec IR (`spec.json` step + Tier-1 target), `candidates.json`, resolver models, config, REST DTOs, and WebSocket message shapes — defined **once** as Zod schemas and imported by every other package.

This package is the single source of truth for the IR. It replaces per-package schema duplication (Pydantic vs. Zod).

---

### cli

Technology:
- Node.js
- TypeScript

Responsibilities:

- CLI entry point (commander)
- Process orchestration
- Core (backend) lifecycle management
- Dashboard lifecycle management (opening it — it is served by core)
- MCP server (official TypeScript SDK) — the agent-facing control plane started by `axiom start`
- Configuration loading

The CLI must **never** contain execution logic. MCP tools translate to REST/WebSocket calls into core — never internal cross-package calls.

---

### core

Technology:

- Node.js
- TypeScript
- Fastify
- Playwright

Responsibilities:

- Test execution
- Recording
- Playwright integration
- Multi-Signal Resolver (semantic signal via local embedding search)
- Grounding
- Benchmarking
- API execution
- Storage (SQLite cache via better-sqlite3 + Drizzle)
- REST API
- WebSocket server
- Serving the bundled dashboard (static assets)

This package owns all business logic.

---

### dashboard

Technology:

- Vite
- React
- TypeScript
- Tailwind

Responsibilities:

- Visualization
- Inspection
- Configuration
- Test management
- Live execution monitoring

The dashboard is only a client. It is built to static assets and **served directly by the core server** — it is not a separately deployable package. Keep it deliberately minimal.

---

# Architectural Invariants

These rules should almost never be violated.

## 1.

The core (TypeScript/Node) owns execution.

## 2.

Tests are stored as JSON.

Never generate executable Playwright scripts as the primary artifact.

## 3.

The dashboard never executes tests.

## 4.

The CLI never executes tests.

## 5.

The resolver is deterministic first.

The semantic signal uses a **local, fixed-weight embedding model** (deterministic, no generative/network call), not a runtime LLM. When deterministic confidence is insufficient, the step is marked stale for author review — an LLM is only re-invoked during explicit, developer-triggered maintenance (see ADR-001, ADR-002).

## 6.

Business logic belongs inside core.

## 7.

Communication occurs only through REST APIs and WebSockets.

Packages should never directly call each other's internal functions.

## 8.

Everything should be replaceable.

Every major subsystem should be designed behind interfaces.

## 9.

Avoid framework lock-in.

Frameworks are implementation details.

The platform architecture is more important.

---

# System Responsibilities

## CLI

Responsible for:

- starting services
- stopping services
- configuration
- project initialization
- spawning the core (Node) backend
- opening dashboard
- hosting the MCP server

Not responsible for:

- recording
- execution
- resolver logic
- Playwright
- benchmarking

---

## Core (Backend)

Responsible for:

- execution
- recording
- grounding
- state management
- storage
- APIs
- resolver
- authoring-time AI integration (via MCP)
- analytics
- serving the bundled dashboard

---

## Dashboard

Responsible for:

- visualization
- editing JSON tests
- displaying logs
- screenshots
- network inspector
- benchmark visualization
- configuration
- reviewing heal suggestions

Never performs execution.

---

# Communication Model

```
Dashboard
        │
 REST / WebSocket
        │
   Core (Node)
        │
 Playwright
```

REST should be used for:

- historical data
- configuration
- projects
- tests
- analytics

WebSocket should be used for:

- execution progress
- logs
- screenshots
- resolver events
- benchmark progress
- notifications

---

# Recording Pipeline

Recording follows this lifecycle.

```
Developer

↓

CLI

↓

Recorder Service

↓

Recorder Session

↓

Flow Compiler

↓

flow.json
```

Recording should capture:

- user interactions
- DOM snapshots
- resolver metadata
- screenshots
- network requests
- timing
- page state

Recording produces JSON.

Not Playwright code.

---

# Execution Pipeline

```
flow.json

↓

Execution Engine

↓

Step Dispatcher

↓

UI Adapter
API Adapter

↓

Results

↓

Dashboard
```

Execution is step-based.

Every step is independent.

---

# Multi-Signal Resolver

The resolver is the core differentiator of Axiom.

Its purpose is to identify elements after UI changes without relying on LLMs.

Signals include:

- semantics
- affordance
- context
- structure
- index

Deterministic matching is attempted first. The semantic signal is a **local embedding search** (fixed-weight ONNX model + cosine similarity, embeddings cached in SQLite) — deterministic, not a generative LLM call.

When confidence falls below the predefined bands, the step is marked stale for author review; an LLM re-enters only in explicit maintenance healing (ADR-002), never automatically at runtime.

Never make the LLM the primary resolution strategy.

---

# Test Format

The JSON representation is the single source of truth.

Every execution must originate from JSON.

Future tooling should transform JSON—not generated code.

---

# Dashboard Philosophy

The dashboard is a developer tool.

It should resemble tools such as:

- browser developer tools
- trace viewers
- API inspectors
- observability dashboards

The dashboard should:

- remain responsive
- stream live updates
- support large datasets
- avoid unnecessary client-side computation

Business logic belongs in the backend.

---

# Development Principles

## Prefer composition over inheritance.

---

## Prefer explicit APIs over hidden coupling.

---

## Keep modules small.

---

## Avoid circular dependencies.

---

## Design for testing.

---

## Keep public interfaces stable.

---

## Avoid global mutable state.

---

## Prefer asynchronous APIs.

---

## Make failures observable.

---

## Document architectural decisions.

---

# Coding Standards

Write code that prioritizes:

- readability
- maintainability
- extensibility

Avoid clever implementations that obscure intent.

When faced with multiple implementations:

Prefer the one that future contributors will understand quickly.

---

# Project Organization

Prefer feature-based organization.

Example:

```
features/

resolver/

recording/

execution/

network/

benchmarks/

dashboard/
```

Avoid organizing large systems solely by file type.

---

# Future Expansion

The architecture should naturally support:

- Cloud execution
- Enterprise deployment
- Multiple browsers
- Mobile testing
- Plugin ecosystem
- API recording
- Benchmark suite
- AI trace inspection
- Visual regression
- Distributed execution
- Parallel workers

New features should extend existing interfaces rather than rewriting core systems.

---

# Performance Goals

Optimize for:

- fast startup
- low memory usage
- deterministic execution
- responsive UI
- efficient caching

Do not prematurely optimize.

Measure before optimizing.

---

# Documentation

Every major subsystem should contain documentation explaining:

- purpose
- responsibilities
- public interfaces
- lifecycle
- extension points

Comments should explain **why**, not **what**.

---

# Decision Framework

> **Important**: Record every specific architectural or implementation decision made by AI agents or human contributors in the [DECISIONS.md](DECISIONS.md) file.

When making engineering decisions, prioritize in this order:

1. Correctness
2. Maintainability
3. Simplicity
4. Extensibility
5. Performance
6. Developer Experience

Never sacrifice architecture for short-term convenience.

---

# Guiding Principle

Axiom is not a collection of scripts.

It is a software platform.

Every contribution should make the platform easier to extend, easier to understand, and more reliable over time.