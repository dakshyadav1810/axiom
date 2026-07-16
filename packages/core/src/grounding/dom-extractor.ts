// Runs inside the page via page.evaluate(fn) — Playwright serializes ONLY this function's source,
// so every helper/const it needs must be declared inside it (no module-scope closures survive the trip).
export interface RawDomElement {
  tag: string;
  role?: string;
  label?: string;
  disabled: boolean;
  visible: boolean;
  focusable: boolean;
  clickable: boolean;
  boundingBox: { x: number; y: number; width: number; height: number };
  ancestorChain: string[];
  region: "form" | "modal" | "section" | null;
  nearbyText?: string;
  testId?: string;
  attributes: Record<string, string>;
  xpath: string;
  contextPath: string[];
  siblingIndex: number;
  cssSelector: string;
}

export function extractInteractiveElementsInPage(): RawDomElement[] {
  const INTERACTIVE_SELECTOR =
    "button,a,input,select,textarea,[role=button],[role=link],[role=textbox],[role=checkbox],[role=radio],[role=menuitem],[role=tab],[tabindex],[onclick]";

  const els = Array.from(
    document.querySelectorAll(INTERACTIVE_SELECTOR),
  ) as HTMLElement[];

  const accessibleName = (el: HTMLElement): string | undefined => {
    const ariaLabel = el.getAttribute("aria-label");
    if (ariaLabel) return ariaLabel;
    const labelledBy = el.getAttribute("aria-labelledby");
    if (labelledBy) {
      const target = document.getElementById(labelledBy);
      if (target?.textContent) return target.textContent.trim();
    }
    if (el.id) {
      const forLabel = document.querySelector(`label[for="${el.id}"]`);
      if (forLabel?.textContent) return forLabel.textContent.trim();
    }
    const placeholder = el.getAttribute("placeholder");
    if (placeholder) return placeholder;
    const title = el.getAttribute("title");
    if (title) return title;
    const text = el.textContent?.trim();
    return text || undefined;
  };

  const xpathFor = (el: HTMLElement): string => {
    if (el.id) return `//*[@id="${el.id}"]`;
    const parts: string[] = [];
    let node: HTMLElement | null = el;
    while (node && node.nodeType === Node.ELEMENT_NODE) {
      let index = 1;
      let sibling = node.previousElementSibling;
      while (sibling) {
        if (sibling.tagName === node.tagName) index++;
        sibling = sibling.previousElementSibling;
      }
      parts.unshift(`${node.tagName.toLowerCase()}[${index}]`);
      node = node.parentElement;
    }
    return `/${parts.join("/")}`;
  };

  const contextPathFor = (el: HTMLElement): string[] => {
    const path: string[] = [];
    let node = el.parentElement;
    let depth = 0;
    while (node && depth < 5) {
      path.push(node.tagName.toLowerCase() + (node.id ? `#${node.id}` : ""));
      node = node.parentElement;
      depth++;
    }
    return path;
  };

  const regionFor = (el: HTMLElement): "form" | "modal" | "section" | null => {
    if (el.closest('[role="dialog"], .modal, dialog')) return "modal";
    if (el.closest("form")) return "form";
    if (el.closest("section")) return "section";
    return null;
  };

  const cssSelectorFor = (el: HTMLElement): string => {
    if (el.id) return `#${el.id}`;
    const testId = el.getAttribute("data-testid");
    if (testId) return `[data-testid="${testId}"]`;
    const tag = el.tagName.toLowerCase();
    const type = el.getAttribute("type");
    if (tag === "input" && type) return `input[type='${type}']`;
    // Playwright only auto-detects XPath when it starts with `//` or `..`; xpathFor() emits a
    // single leading slash, so it must be tagged explicitly or it parses as CSS and throws.
    return `xpath=${xpathFor(el)}`;
  };

  return els.map((el) => {
    const rect = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    const visible =
      style.display !== "none" &&
      style.visibility !== "hidden" &&
      rect.width > 0 &&
      rect.height > 0;
    const siblings = Array.from(el.parentElement?.children ?? []).filter(
      (s) => s.tagName === el.tagName,
    );

    const attributes: Record<string, string> = {};
    for (const attr of Array.from(el.attributes))
      attributes[attr.name] = attr.value;

    return {
      tag: el.tagName.toLowerCase(),
      role: el.getAttribute("role") ?? undefined,
      label: accessibleName(el),
      disabled:
        (el as HTMLInputElement).disabled === true ||
        el.getAttribute("aria-disabled") === "true",
      visible,
      focusable: el.tabIndex >= 0,
      clickable: true,
      boundingBox: {
        x: rect.x,
        y: rect.y,
        width: rect.width,
        height: rect.height,
      },
      ancestorChain: contextPathFor(el),
      region: regionFor(el),
      nearbyText: el.parentElement?.textContent?.trim().slice(0, 200),
      testId: el.getAttribute("data-testid") ?? undefined,
      attributes,
      xpath: xpathFor(el),
      contextPath: contextPathFor(el),
      siblingIndex: siblings.indexOf(el),
      cssSelector: cssSelectorFor(el),
    };
  });
}
