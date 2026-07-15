import type { RunReport, WsMessage } from "@axiom/shared";
import { useEffect, useRef, useState } from "react";
import { api, wsUrl } from "../api.js";

// Results view: run history, pass/fail/stale per step, selection source, timings (SPEC-005 §3).
// Live updates stream over WebSocket into a plain auto-scrolling view — no terminal emulator.
export function RunView({ testId }: { testId: string }) {
  const [runId, setRunId] = useState<string | null>(null);
  const [report, setReport] = useState<RunReport | null>(null);
  const [log, setLog] = useState<string[]>([]);
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!runId) return;
    const ws = new WebSocket(wsUrl(`/ws/runs/${runId}`));
    ws.onmessage = (evt) => {
      const msg: WsMessage = JSON.parse(evt.data);
      setLog((l) => [...l, JSON.stringify(msg)]);
      if (msg.type === "run.complete") setReport(msg.report);
    };
    return () => ws.close();
  }, [runId]);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight });
  }, [log]);

  const run = async () => {
    setLog([]);
    setReport(null);
    const { runId } = await api.runTest(testId);
    setRunId(runId);
  };

  return (
    <div>
      <button onClick={run}>Run test</button>
      <div
        ref={logRef}
        style={{
          maxHeight: 200,
          overflowY: "auto",
          fontFamily: "monospace",
          fontSize: 12,
        }}
      >
        {log.map((l, i) => (
          <div key={i}>{l}</div>
        ))}
      </div>
      {report && (
        <table>
          <thead>
            <tr>
              <th>step</th>
              <th>status</th>
              <th>selection</th>
              <th>band</th>
              <th>ms</th>
            </tr>
          </thead>
          <tbody>
            {report.steps.map((s) => (
              <tr key={s.stepId}>
                <td>{s.stepId}</td>
                <td>{s.status}</td>
                <td>{s.selection}</td>
                <td>{s.band}</td>
                <td>{s.durationMs}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
