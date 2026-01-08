import { spawn } from "bun";
import path from "node:path";
import process from "node:process";

export type CLIEventType = "stdout" | "stderr" | "exit" | "error";

export interface CLIEvent {
  type: CLIEventType;
  data?: string;
  code?: number;
}

export interface SpawnOptions {
  command: string[];
  cwd?: string;
  env?: Record<string, string>;
  onEvent: (event: CLIEvent) => void;
}

export class CLIBridge {
  private repoRoot: string;
  private cacheDir: string;

  constructor() {
    this.repoRoot = process.cwd();
    this.cacheDir = path.join(this.repoRoot, ".context/cache");
  }

  /**
   * Spawns the skills-fleet CLI command.
   * Returns a promise that resolves when the process exits.
   */
  async run(args: string[], onEvent: (event: CLIEvent) => void): Promise<number> {
    const fullArgs = [
      "uv",
      "run",
      "python",
      "-m",
      "agentic_fleet.agentic_skills_system.cli",
      ...args
    ];

    try {
      const proc = spawn(fullArgs, {
        cwd: this.repoRoot,
        env: {
          ...process.env,
          UV_CACHE_DIR: ".uv-cache",
          DSPY_CACHEDIR: path.join(this.repoRoot, ".dspy_cache"),
          // Force unbuffered output if possible, though Python usually buffers
          PYTHONUNBUFFERED: "1",
        },
        stdin: "ignore",
        stdout: "pipe",
        stderr: "pipe",
      });

      const decoder = new TextDecoder();

      // Stream stdout
      const readStdout = async () => {
        for await (const chunk of proc.stdout) {
          onEvent({ type: "stdout", data: decoder.decode(chunk) });
        }
      };

      // Stream stderr
      const readStderr = async () => {
        for await (const chunk of proc.stderr) {
          onEvent({ type: "stderr", data: decoder.decode(chunk) });
        }
      };

      await Promise.all([readStdout(), readStderr(), proc.exited]);
      
      const exitCode = proc.exitCode ?? 1;
      onEvent({ type: "exit", code: exitCode });
      return exitCode;

    } catch (error) {
      onEvent({ type: "error", data: String(error) });
      return 1;
    }
  }

  /**
   * Helper to run create-skill specifically
   */
  async createSkill(task: string, onEvent: (event: CLIEvent) => void) {
    return this.run(
      ["create-skill", "--task", task, "--cache-dir", this.cacheDir, "--json"],
      onEvent
    );
  }

  /**
   * Helper to list/validate skills (Catalog)
   * This might eventually use a faster method than spawning the full CLI if performance is an issue
   */
  async validateSkill(path: string, onEvent: (event: CLIEvent) => void) {
    return this.run(
      ["validate-skill", path, "--json"],
      onEvent
    );
  }
}

export const cli = new CLIBridge();
