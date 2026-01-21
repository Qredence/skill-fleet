/**
 * useHitlConfig Hook
 *
 * Fetches and caches HITL configuration from the API,
 * enabling the UI to stay in sync with backend settings.
 */

import { useEffect, useState } from "react";
import { ActionKeywords, HITL_ACTION_KEYWORDS } from "../utils/hitl-keywords.js";

interface UseHitlConfigOptions {
  apiUrl: string;
  enabled?: boolean;
}

interface UseHitlConfigResult {
  keywords: ActionKeywords;
  isLoading: boolean;
  error: string | null;
}

/**
 * Fetch HITL configuration from the API
 *
 * Falls back to bundled defaults if API fetch fails.
 * Caches result in local storage to minimize API calls.
 */
export function useHitlConfig({
  apiUrl,
  enabled = true,
}: UseHitlConfigOptions): UseHitlConfigResult {
  const [keywords, setKeywords] = useState<ActionKeywords>(
    HITL_ACTION_KEYWORDS
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled) return;

    // Try local storage first (cache)
    const cached = localStorage.getItem("hitl_config");
    if (cached) {
      try {
        const config = JSON.parse(cached);
        setKeywords(config.action_keywords);
        return;
      } catch (_err) {
        // Invalid cache, proceed to fetch
      }
    }

    // Fetch from API
    const fetchConfig = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(`${apiUrl}/api/v2/hitl/config`);

        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }

        const data = (await response.json()) as {
          action_keywords: ActionKeywords;
        };

        setKeywords(data.action_keywords);

        // Cache in local storage for 1 hour
        localStorage.setItem(
          "hitl_config",
          JSON.stringify({
            action_keywords: data.action_keywords,
            cached_at: Date.now(),
          })
        );
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to fetch HITL config";
        setError(message);
        // Fall back to bundled defaults
        setKeywords(HITL_ACTION_KEYWORDS);
      } finally {
        setIsLoading(false);
      }
    };

    fetchConfig();
  }, [apiUrl, enabled]);

  return {
    keywords,
    isLoading,
    error,
  };
}
