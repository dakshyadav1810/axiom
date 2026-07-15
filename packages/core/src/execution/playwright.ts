import type { AxiomConfig } from "@axiom/shared";
import {
  type Browser,
  type BrowserContext,
  type Page,
  chromium,
  firefox,
  webkit,
} from "playwright";

const ENGINES = { chromium, firefox, webkit };

export interface BrowserSession {
  browser: Browser;
  context: BrowserContext;
  page: Page;
  close(): Promise<void>;
}

// Shared browser/page lifecycle wrapper — used by grounding (LLD-003) and execution (LLD-005),
// but never sharing live state across their boundary (LLD-005 §8).
export async function openSession(
  config: AxiomConfig,
): Promise<BrowserSession> {
  const browser = await ENGINES[config.browser].launch({
    headless: config.headless,
  });
  const context = await browser.newContext();
  const page = await context.newPage();
  page.setDefaultTimeout(config.timeouts.actionMs);
  page.setDefaultNavigationTimeout(config.timeouts.navMs);
  return {
    browser,
    context,
    page,
    close: async () => {
      await context.close();
      await browser.close();
    },
  };
}
