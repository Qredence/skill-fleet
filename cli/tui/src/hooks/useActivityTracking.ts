import { useEffect, useMemo, useState } from "react";
import type { ActivitySummary } from "../types";

function nowMs(): number {
  return Date.now();
}

/**
 * Hook for tracking activity timestamps and computing activity state.
 * Provides responsive UI feedback based on event timing.
 *
 * @returns Object with activity state and setters for event timestamps
 */
export function useActivityTracking() {
  const [lastEventAt, setLastEventAt] = useState<number | null>(null);
  const [lastTokenAt, setLastTokenAt] = useState<number | null>(null);
  const [lastStatusAt, setLastStatusAt] = useState<number | null>(null);
  const [currentTime, setCurrentTime] = useState<number>(nowMs());

  // Update current time periodically for "time since last event" display
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(nowMs());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // Compute activity summary for child components
  const activity: ActivitySummary = useMemo(() => {
    const timeSinceLastEvent = lastEventAt ? currentTime - lastEventAt : null;
    // Consider activity "active" if we received an event in the last 3 seconds
    const isActive = timeSinceLastEvent !== null && timeSinceLastEvent < 3000;
    // Detect if we received token_stream events recently (within 2s)
    const timeSinceLastToken = lastTokenAt ? currentTime - lastTokenAt : null;
    const hasRecentTokens = timeSinceLastToken !== null && timeSinceLastToken < 2000;
    return {
      lastEventAt,
      lastTokenAt,
      lastStatusAt,
      isActive,
      timeSinceLastEvent,
      hasRecentTokens,
    };
  }, [lastEventAt, lastTokenAt, lastStatusAt, currentTime]);

  return {
    activity,
    currentTime,
    setLastEventAt,
    setLastTokenAt,
    setLastStatusAt,
  };
}
