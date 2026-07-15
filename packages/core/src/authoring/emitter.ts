// Repairs trivial drift (snake_case keys, missing defaults) before Zod parsing (LLD-002 §4).
export function normalizeLlmOutput(raw: unknown): unknown {
  if (typeof raw !== "object" || raw === null) return raw;
  const toCamel = (s: string) =>
    s.replace(/_([a-z])/g, (_, c) => c.toUpperCase());
  const walk = (v: unknown): unknown => {
    if (Array.isArray(v)) return v.map(walk);
    if (typeof v === "object" && v !== null) {
      return Object.fromEntries(
        Object.entries(v as Record<string, unknown>).map(([k, val]) => [
          toCamel(k),
          walk(val),
        ]),
      );
    }
    return v;
  };
  return walk(raw);
}
