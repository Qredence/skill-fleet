/**
 * TUI Entry Point for Skills Fleet
 *
 * This module is spawned as a separate Node.js process from the Python CLI.
 * It connects to the FastAPI backend and provides an interactive terminal UI.
 */

import React from "react";
import { render } from "ink";
import { App } from "./app";

// Parse environment variables
const API_URL = process.env.SKILL_FLEET_API_URL || "http://localhost:8000";
const USER_ID = process.env.SKILL_FLEET_USER_ID || "default";

// Parse command-line arguments
const args = process.argv.slice(2);
let apiUrl = API_URL;
let userId = USER_ID;

for (let i = 0; i < args.length; i++) {
  if (args[i] === "--api-url" && i + 1 < args.length) {
    apiUrl = args[i + 1];
    i++;
  } else if (args[i] === "--user-id" && i + 1 < args.length) {
    userId = args[i + 1];
    i++;
  }
}

// Create and render the app
const app = React.createElement(App, { apiUrl, userId });
const { unmount, waitUntilExit } = render(app);

// Handle graceful shutdown
process.on("SIGINT", () => {
  unmount();
  process.exit(0);
});

process.on("SIGTERM", () => {
  unmount();
  process.exit(0);
});

// Keep process alive
waitUntilExit().catch((err) => {
  console.error("TUI Error:", err);
  process.exit(1);
});
