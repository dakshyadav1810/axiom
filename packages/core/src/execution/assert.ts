import type { Assertion, ExpectedOutcome } from "@axiom/shared";
import type { Page } from "playwright";

export interface AssertOutcome {
  ok: boolean;
  reason?: string;
}

function interpolate(s: string, vars: Record<string, string>): string {
  return s.replace(/\$\{(\w+)\}/g, (_, k) => vars[k] ?? "");
}

// Unified UI/API/DB assertion evaluation (SPEC-003 §3). Locate failure is handled by the caller
// (locate.ts) and never reaches here — this only judges outcomes for elements/responses that were found.
export async function evaluateAssertion(
  a: Assertion,
  ctx: {
    page?: Page;
    apiResponse?: { status: number; body: unknown };
    dbRow?: unknown;
    vars: Record<string, string>;
  },
): Promise<AssertOutcome> {
  switch (a.type) {
    case "urlContains":
      return ok(
        ctx.page
          ? ctx.page.url().includes(interpolate(a.expected, ctx.vars))
          : false,
      );
    case "textContains": {
      const text = await ctx.page?.textContent("body");
      return ok(!!text?.includes(interpolate(a.expected, ctx.vars)));
    }
    case "value": {
      const val = await ctx.page
        ?.locator(":focus")
        .inputValue()
        .catch(() => "");
      return ok(val === interpolate(a.expected, ctx.vars));
    }
    case "elementVisible":
      return ok(
        !!(await ctx.page
          ?.getByRole(a.target.role as any, { name: a.target.label })
          .isVisible()
          .catch(() => false)),
      );
    case "elementAbsent":
      return ok(
        !(await ctx.page
          ?.getByRole(a.target.role as any, { name: a.target.label })
          .isVisible()
          .catch(() => false)),
      );
    case "apiStatus":
      return ok(ctx.apiResponse?.status === a.expected);
    case "apiBody":
      return ok(
        JSON.stringify(getPath(ctx.apiResponse?.body, a.path)) ===
          JSON.stringify(a.expected),
      );
    case "dbRow":
      return ok(JSON.stringify(ctx.dbRow) === JSON.stringify(a.expected));
  }
}

export async function evaluateExpectedOutcome(
  o: ExpectedOutcome,
  ctx: { page: Page; urlBefore: string; vars: Record<string, string> },
): Promise<AssertOutcome> {
  switch (o.type) {
    case "navigation":
    case "url_change":
      return ok(
        ctx.page.url() !== ctx.urlBefore &&
          (o.type === "navigation" || ctx.page.url().includes(o.value)),
      );
    case "element_appears":
      return ok(
        await ctx.page
          .locator(o.value)
          .isVisible()
          .catch(() => false),
      );
    case "text_contains": {
      const text = await ctx.page.textContent("body");
      return ok(!!text?.includes(interpolate(o.value, ctx.vars)));
    }
    case "field_contains": {
      const val = await ctx.page
        .locator(":focus")
        .inputValue()
        .catch(() => "");
      return ok(val.includes(interpolate(o.value, ctx.vars)));
    }
  }
}

function ok(b: boolean): AssertOutcome {
  return b ? { ok: true } : { ok: false, reason: "assertion returned false" };
}
function getPath(obj: unknown, path: string): unknown {
  return path.split(".").reduce((o, k) => (o as any)?.[k], obj);
}
