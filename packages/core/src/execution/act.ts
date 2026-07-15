import type { UiStep } from "@axiom/shared";
import type { Page } from "playwright";

function interpolate(
  value: string | undefined,
  vars: Record<string, string>,
): string {
  if (!value) return "";
  return value.replace(/\$\{(\w+)\}/g, (_, k) => vars[k] ?? "");
}

// Dispatches the Playwright action for a UI step against a resolved selector (or none, for navigate/wait).
export async function act(
  page: Page,
  step: UiStep,
  selector: string | null,
  vars: Record<string, string>,
): Promise<void> {
  const value = interpolate(step.value, vars);
  switch (step.action) {
    case "navigate":
      await page.goto(interpolate(step.value, vars) || page.url());
      return;
    case "wait":
      await page.waitForTimeout(Number(value) || 500);
      return;
  }
  if (!selector)
    throw new Error(`action ${step.action} requires a resolved selector`);
  const locator = page.locator(selector).first();
  switch (step.action) {
    case "click":
      await locator.click();
      return;
    case "type":
      await locator.fill(value);
      return;
    case "select":
      await locator.selectOption(value);
      return;
    case "keypress":
      await locator.press(value);
      return;
    case "submit":
      await locator.press("Enter");
      return;
  }
}
