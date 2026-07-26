import { useState, useRef, useCallback } from "react";
import { useDuel } from "../context/DuelContext";
import useTelemetry from "../hooks/useTelemetry";

export default function CodeEditor() {
  const { submitCode, lastSubmission, roundData } = useDuel();
  const { ref: telemetryRef, exportTelemetry } = useTelemetry();
  const [code, setCode] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handlePaste = useCallback(
    (e) => {
      const text = e.clipboardData.getData("text");
      telemetryRef.current.pasteEvents.push({
        timestamp: Date.now(),
        length: text.length,
        lineCount: text.split("\n").length,
      });
    },
    [telemetryRef]
  );

  const handleKeyDown = useCallback(() => {
    telemetryRef.current.keystrokeCount++;
  }, [telemetryRef]);

  const handleSubmit = useCallback(() => {
    if (!code.trim() || submitting) return;
    setSubmitting(true);
    submitCode(code, exportTelemetry());
  }, [code, submitting, submitCode, exportTelemetry]);

  const result = lastSubmission;

  return (
    <div className="code-editor">
      <div className="editor-header">
        <span className="editor-label">Your Solution</span>
        {result && (
          <span className={`editor-result ${result.error ? "error" : result.test_cases_passed === result.test_cases_total ? "pass" : "partial"}`}>
            {result.error
              ? result.error
              : `${result.test_cases_passed}/${result.test_cases_total} passed · ${result.time_ms}ms · ${(result.memory_kb / 1024).toFixed(1)}MB`}
          </span>
        )}
      </div>
      <textarea
        className="editor-textarea"
        value={code}
        onChange={(e) => setCode(e.target.value)}
        onPaste={handlePaste}
        onKeyDown={handleKeyDown}
        placeholder="Write your Python solution here..."
        spellCheck={false}
      />
      <button
        className="submit-btn"
        onClick={handleSubmit}
        disabled={!code.trim() || submitting}
      >
        {submitting ? "Judging..." : "Submit"}
      </button>
    </div>
  );
}
