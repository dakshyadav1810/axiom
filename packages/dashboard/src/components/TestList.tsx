import { useEffect, useState } from "react";
import { type TestSummary, api } from "../api.js";

export function TestList({ onSelect }: { onSelect: (testId: string) => void }) {
  const [tests, setTests] = useState<TestSummary[]>([]);

  useEffect(() => {
    api
      .listTests()
      .then(setTests)
      .catch(() => setTests([]));
  }, []);

  return (
    <ul>
      {tests.map((t) => (
        <li key={t.testId}>
          <button onClick={() => onSelect(t.testId)}>
            {t.name} {t.grounded ? "✓" : "(ungrounded)"}
          </button>
        </li>
      ))}
    </ul>
  );
}
