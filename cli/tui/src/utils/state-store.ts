/**
 * TUI State Persistence
 *
 * Persists TUI state to ~/.skill-fleet/tui-state.json for:
 * - Known job IDs (survives TUI restart)
 * - Last active tab
 * - User preferences
 */

import { homedir } from "os";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "fs";
import { join } from "path";

export interface TUIState {
  /** Known job IDs that should be tracked */
  knownJobIds: string[];
  /** Last active tab index */
  lastActiveTab: number;
  /** User ID for filtering */
  userId: string;
  /** API URL */
  apiUrl: string;
  /** Last updated timestamp */
  updatedAt: string;
}

const DEFAULT_STATE: TUIState = {
  knownJobIds: [],
  lastActiveTab: 0,
  userId: "default",
  apiUrl: "http://localhost:8000",
  updatedAt: new Date().toISOString(),
};

/**
 * Get the state file path (~/.skill-fleet/tui-state.json)
 */
function getStatePath(): string {
  const dir = join(homedir(), ".skill-fleet");
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }
  return join(dir, "tui-state.json");
}

/**
 * Load TUI state from disk, returning defaults if not found
 */
export function loadState(): TUIState {
  try {
    const path = getStatePath();
    if (!existsSync(path)) {
      return { ...DEFAULT_STATE };
    }
    const data = readFileSync(path, "utf-8");
    const parsed = JSON.parse(data) as Partial<TUIState>;
    return {
      ...DEFAULT_STATE,
      ...parsed,
    };
  } catch (error) {
    console.error("Failed to load TUI state:", error);
    return { ...DEFAULT_STATE };
  }
}

/**
 * Save TUI state to disk
 */
export function saveState(state: Partial<TUIState>): boolean {
  try {
    const path = getStatePath();
    const current = loadState();
    const updated: TUIState = {
      ...current,
      ...state,
      updatedAt: new Date().toISOString(),
    };
    writeFileSync(path, JSON.stringify(updated, null, 2), "utf-8");
    return true;
  } catch (error) {
    console.error("Failed to save TUI state:", error);
    return false;
  }
}

/**
 * Add a job ID to the known list
 */
export function addKnownJob(jobId: string): void {
  const state = loadState();
  if (!state.knownJobIds.includes(jobId)) {
    state.knownJobIds.push(jobId);
    // Keep only the last 100 jobs
    if (state.knownJobIds.length > 100) {
      state.knownJobIds = state.knownJobIds.slice(-100);
    }
    saveState(state);
  }
}

/**
 * Remove a job ID from the known list
 */
export function removeKnownJob(jobId: string): void {
  const state = loadState();
  state.knownJobIds = state.knownJobIds.filter((id) => id !== jobId);
  saveState(state);
}

/**
 * Get all known job IDs
 */
export function getKnownJobs(): string[] {
  return loadState().knownJobIds;
}

/**
 * Update last active tab
 */
export function setLastActiveTab(tabIndex: number): void {
  saveState({ lastActiveTab: tabIndex });
}

/**
 * Get last active tab
 */
export function getLastActiveTab(): number {
  return loadState().lastActiveTab;
}

/**
 * Update user settings
 */
export function updateSettings(settings: {
  userId?: string;
  apiUrl?: string;
}): void {
  saveState(settings);
}
