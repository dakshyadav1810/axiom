import type { GroundedTest, RunReport, SpecIR } from "@axiom/shared";

export interface TestSummary {
  testId: string;
  name: string;
  grounded: boolean;
}

async function req<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(path, opts);
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return res.json();
}

export const api = {
  listTests: () => req<TestSummary[]>("/tests"),
  getTest: (id: string) => req<GroundedTest | SpecIR>(`/tests/${id}`),
  runTest: (testId: string) =>
    req<{ runId: string }>("/runs", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ testId }),
    }),
  getReport: (runId: string) => req<RunReport>(`/runs/${runId}`),
};

export function wsUrl(path: string): string {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${location.host}${path}`;
}
