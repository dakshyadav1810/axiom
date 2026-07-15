import CodeMirror from "@uiw/react-codemirror";
import { useEffect, useState } from "react";
import { api } from "../api.js";

// JSON test editor with shared Zod validation for hand-edits (SPEC-005 §3).
export function JsonEditor({ testId }: { testId: string }) {
  const [text, setText] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getTest(testId).then((t) => setText(JSON.stringify(t, null, 2)));
  }, [testId]);

  const onChange = (value: string) => {
    setText(value);
    try {
      JSON.parse(value);
      setError(null);
    } catch (e) {
      setError(String(e));
    }
  };

  return (
    <div>
      <CodeMirror value={text} height="400px" onChange={onChange} />
      {error && <div style={{ color: "red" }}>{error}</div>}
    </div>
  );
}
