import { useRef, useCallback } from "react";

export default function useTelemetry() {
  const ref = useRef({
    pasteEvents: [],
    tabSwitches: [],
    keystrokeCount: 0,
    matchStartTime: Date.now(),
  });

  const reset = useCallback(() => {
    ref.current = {
      pasteEvents: [],
      tabSwitches: [],
      keystrokeCount: 0,
      matchStartTime: Date.now(),
    };
  }, []);

  const exportTelemetry = useCallback(() => {
    const t = ref.current;
    const now = Date.now();
    const elapsed = now - t.matchStartTime;
    const kps = elapsed > 0 ? (t.keystrokeCount / elapsed) * 1000 : 0;

    const totalTabTime = t.tabSwitches.reduce((sum, sw, i) => {
      if (sw.type === "left" && i + 1 < t.tabSwitches.length) {
        return sum + (t.tabSwitches[i + 1].timestamp - sw.timestamp);
      }
      return sum;
    }, 0);

    return {
      paste_events: t.pasteEvents,
      tab_switches: t.tabSwitches,
      keystroke_count: t.keystrokeCount,
      keystrokes_per_second: Math.round(kps * 100) / 100,
      time_since_match_start_ms: elapsed,
      paste_event_count: t.pasteEvents.length,
      total_paste_length: t.pasteEvents.reduce((s, e) => s + e.length, 0),
      tab_switch_count: t.tabSwitches.length,
      total_tab_time_ms: totalTabTime,
    };
  }, []);

  return { ref, reset, exportTelemetry };
}
