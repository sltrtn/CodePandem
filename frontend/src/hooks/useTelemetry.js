import { useRef, useCallback } from "react";

export default function useTelemetry() {
  const ref = useRef({
    pasteEvents: [],
    tabSwitches: [],
    keystrokeCount: 0,
    matchStartTime: Date.now(),
    keystrokeEvents: [],
    lastPasteTime: 0,
    burstPasteCount: 0,
  });

  const reset = useCallback(() => {
    ref.current = {
      pasteEvents: [],
      tabSwitches: [],
      keystrokeCount: 0,
      matchStartTime: Date.now(),
      keystrokeEvents: [],
      lastPasteTime: 0,
      burstPasteCount: 0,
    };
  }, []);

  const recordPaste = useCallback((length) => {
    const now = Date.now();
    ref.current.pasteEvents.push({ timestamp: now, length });
    ref.current.paste_event_count = ref.current.pasteEvents.length;

    if (now - ref.current.lastPasteTime < 3000) {
      ref.current.burstPasteCount++;
    }
    ref.current.lastPasteTime = now;
  }, []);

  const recordKeystroke = useCallback((key) => {
    const now = Date.now();
    ref.current.keystrokeCount++;

    if (ref.current.keystrokeEvents.length < 500) {
      ref.current.keystrokeEvents.push({
        key: key.length === 1 ? "char" : key,
        timestamp_ms: now,
      });
    }
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

    const events = t.keystrokeEvents;
    let avgInterval = 0;
    let stddev = 0;
    if (events.length > 1) {
      const intervals = [];
      for (let i = 1; i < events.length; i++) {
        const dt = events[i].timestamp_ms - events[i - 1].timestamp_ms;
        if (dt > 0 && dt < 2000) intervals.push(dt);
      }
      if (intervals.length > 0) {
        avgInterval = intervals.reduce((a, b) => a + b, 0) / intervals.length;
        const variance =
          intervals.reduce((s, x) => s + (x - avgInterval) ** 2, 0) /
          intervals.length;
        stddev = Math.sqrt(variance);
      }
    }

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
      keystroke_events: events.slice(-200),
      avg_key_interval_ms: Math.round(avgInterval * 10) / 10,
      key_interval_stddev: Math.round(stddev * 10) / 10,
      burst_paste_count: t.burstPasteCount,
      max_burst_length: Math.max(...t.pasteEvents.map((e) => e.length), 0),
    };
  }, []);

  return { ref, reset, recordPaste, recordKeystroke, exportTelemetry };
}
