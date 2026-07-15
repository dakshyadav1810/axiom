import type { Tier1Target } from "@axiom/shared";
import { describe, expect, it } from "vitest";
import type { DomCandidate, PageContext } from "./base.js";
import { MultiSignalResolver } from "./index.js";

// Deterministic bag-of-words fake embedder — no network/model download in tests.
const VOCAB = [
  "email",
  "login",
  "credential",
  "password",
  "submit",
  "cancel",
  "sign",
  "in",
  "textbox",
  "button",
];
const fakeEmbedder = {
  async embed(text: string): Promise<Float32Array> {
    const v = new Float32Array(VOCAB.length);
    const words = text.toLowerCase().split(/\W+/);
    for (const w of words) {
      const i = VOCAB.indexOf(w);
      if (i >= 0) v[i] = 1;
    }
    return v;
  },
};

const bands = { high: 0.7, medium: 0.5 };
const page: PageContext = {
  textDensity: 0.8,
  iconRatio: 0,
  hasForm: true,
  hasModal: false,
  repeatedStructure: false,
};

function cand(over: Partial<DomCandidate>): DomCandidate {
  return {
    id: "c",
    selector: "#c",
    tag: "input",
    role: "textbox",
    visible: true,
    disabled: false,
    ...over,
  };
}

describe("MultiSignalResolver golden cases", () => {
  const resolver = new MultiSignalResolver(fakeEmbedder as any, bands);

  it("unique semantic match grounds high", async () => {
    const target: Tier1Target = {
      label: "Email",
      semantics: ["email", "login", "credential"],
      role: "textbox",
      actions: ["type"],
      intent: "email input",
    };
    const candidates = [
      cand({ id: "c1", label: "Email", region: "form", testId: "email-input" }),
      cand({ id: "c2", label: "Cancel", role: "button", tag: "button" }),
    ];
    const res = await resolver.resolve({
      target,
      candidates,
      page,
      generalization: "same_element",
    });
    expect(res.status).toBe("grounded");
    expect(res.selected).toBe("c1");
    expect(res.band).toBe("high");
  });

  it("icon-only candidate (no label) scores semantics 0 and loses to a labeled one", async () => {
    const target: Tier1Target = {
      label: "Submit",
      semantics: ["submit", "login"],
      role: "button",
      actions: ["click"],
      intent: "submit form",
    };
    const candidates = [
      cand({ id: "icon", tag: "button", role: "button" }), // no label
      cand({ id: "labeled", tag: "button", role: "button", label: "Submit" }),
    ];
    const res = await resolver.resolve({
      target,
      candidates,
      page,
      generalization: "same_element",
    });
    expect(res.selected).toBe("labeled");
    const icon = res.candidates.find((c) => c.id === "icon")!;
    expect(icon.signals.semantics).toBe(0);
  });

  it("affordance filter drops disabled candidates entirely", async () => {
    const target: Tier1Target = {
      label: "Submit",
      semantics: ["submit"],
      role: "button",
      actions: ["click"],
      intent: "x",
    };
    const candidates = [
      cand({ id: "disabled", label: "Submit", disabled: true }),
    ];
    const res = await resolver.resolve({
      target,
      candidates,
      page,
      generalization: "same_element",
    });
    expect(res.status).toBe("ungrounded");
    expect(res.candidates).toHaveLength(0);
  });

  it("ambiguous near-ties within margin downgrade band instead of guessing", async () => {
    const target: Tier1Target = {
      label: "Item",
      semantics: ["item"],
      role: "button",
      actions: ["click"],
      intent: "x",
    };
    const candidates = [
      cand({ id: "a", label: "Item", tag: "button", role: "button" }),
      cand({ id: "b", label: "Item", tag: "button", role: "button" }),
    ];
    const res = await resolver.resolve({
      target,
      candidates,
      page,
      generalization: "same_element",
    });
    expect(res.status).not.toBe("grounded");
  });
});
