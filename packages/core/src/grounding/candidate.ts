import type { Page } from "playwright";
import type { DomCandidate } from "../resolver/base.js";
import { extractInteractiveElementsInPage } from "./dom-extractor.js";

// Node-side wrapper: injects the typed in-page module, returns serializable DomCandidates (LLD-003 §4).
export async function extractCandidates(page: Page): Promise<DomCandidate[]> {
  const raw = await page.evaluate(extractInteractiveElementsInPage);
  return raw.map((r, i) => ({
    id: `cand_${i}`,
    selector: r.cssSelector,
    tag: r.tag,
    role: r.role,
    label: r.label,
    disabled: r.disabled,
    visible: r.visible,
    focusable: r.focusable,
    clickable: r.clickable,
    boundingBox: r.boundingBox,
    ancestorChain: r.ancestorChain,
    region: r.region,
    nearbyText: r.nearbyText,
    testId: r.testId,
    attributes: r.attributes,
    xpath: r.xpath,
    contextPath: r.contextPath,
    siblingIndex: r.siblingIndex,
  }));
}
