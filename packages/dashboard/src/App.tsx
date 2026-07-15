import { useState } from "react";
import { JsonEditor } from "./components/JsonEditor.js";
import { RunView } from "./components/RunView.js";
import { TestList } from "./components/TestList.js";

// Thin developer tool — never executes tests itself, only calls core (invariant #3, SPEC-005 §3).
export function App() {
  const [testId, setTestId] = useState<string | null>(null);

  return (
    <div
      style={{
        display: "flex",
        gap: 24,
        padding: 16,
        fontFamily: "sans-serif",
      }}
    >
      <div style={{ minWidth: 200 }}>
        <h2>Axiom</h2>
        <TestList onSelect={setTestId} />
      </div>
      {testId && (
        <div style={{ flex: 1 }}>
          <h3>{testId}</h3>
          <RunView testId={testId} />
          <JsonEditor testId={testId} />
        </div>
      )}
    </div>
  );
}
