import { describe, expect, it } from "vitest";
import { GroundedTest } from "./groundedTest.js";
import { lintSpec } from "./spec.js";
import { SpecIR } from "./spec.js";
import type { UiStep } from "./step.js";

const spec: SpecIR = {
  version: "1.0",
  flow: {
    id: "f1",
    name: "login",
    intent: "test login",
    startUrl: "https://app.local",
    vars: { email: "" },
  },
  steps: [
    {
      id: "s1",
      kind: "ui",
      intent: "Enter the user's email address.",
      action: "type",
      value: "${email}",
      generalization: "same_element",
      onFailure: "retry_once",
      preconditions: [{ kind: "visible" }, { kind: "enabled" }],
      expectedOutcome: [{ type: "field_contains", value: "${email}" }],
      assertions: [{ type: "value", expected: "${email}" }],
      negative: false,
      target: {
        label: "Email",
        role: "textbox",
        intent: "Primary email input",
        semantics: ["email", "login", "credential"],
        actions: ["type", "focus"],
      },
    },
  ],
};

describe("SpecIR", () => {
  it("parses and lints clean", () => {
    const parsed = SpecIR.parse(spec);
    expect(lintSpec(parsed).ok).toBe(true);
  });

  it("flags unresolved vars", () => {
    const bad = { ...spec, flow: { ...spec.flow, vars: {} } };
    expect(lintSpec(SpecIR.parse(bad)).ok).toBe(false);
  });
});

describe("GroundedTest", () => {
  it("validates a partially-grounded test (later step has no resolution)", () => {
    const grounded: GroundedTest = {
      ...spec,
      groundedAt: new Date(0).toISOString(),
      groundedUrl: spec.flow.startUrl,
      steps: [
        {
          ...(spec.steps[0] as UiStep),
          target: {
            ...(spec.steps[0] as UiStep).target!,
            resolution: {
              status: "grounded",
              confidence: 0.92,
              band: "high",
              selected: "cand_2",
              cachedSelector: "input[type='email']",
              winner: {
                id: "cand_2",
                selector: "input[type='email']",
                anchors: {},
                signals: {
                  semantics: 0.98,
                  affordance: 1,
                  context: 0.84,
                  structure: 0.91,
                  index: 0.5,
                },
                score: 0.92,
                band: "high",
              },
            },
          },
        },
      ],
    };
    expect(() => GroundedTest.parse(grounded)).not.toThrow();
  });
});
