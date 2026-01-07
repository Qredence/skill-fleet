import { readFile, writeFile, readdir, stat, mkdir } from "fs/promises";
import { resolve } from "path";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

export type ToolName = "read_file" | "list_dir" | "write_file" | "run_command";

export interface ToolCall {
  tool: ToolName;
  args?: Record<string, any>;
}

export interface ToolResult {
  tool: ToolName;
  ok: boolean;
  output: string;
  error?: string;
}

export interface ToolExecutionOptions {
  cwd: string;
  maxFileBytes: number;
  maxDirEntries: number;
  maxOutputChars: number;
}

const TOOL_BLOCK_REGEX = /```tool\s*([\s\S]*?)```/gi;

export function parseToolCalls(text: string): ToolCall[] {
  const calls: ToolCall[] = [];
  if (!text) return calls;

  let match: RegExpExecArray | null;
  while ((match = TOOL_BLOCK_REGEX.exec(text)) !== null) {
    const payload = match[1]?.trim();
    if (!payload) continue;
    try {
      const parsed = JSON.parse(payload);
      if (Array.isArray(parsed)) {
        parsed.forEach((item) => pushToolCall(item, calls));
      } else if (parsed && typeof parsed === "object") {
        if (Array.isArray((parsed as any).tools)) {
          (parsed as any).tools.forEach((item: any) => pushToolCall(item, calls));
        } else {
          pushToolCall(parsed, calls);
        }
      }
    } catch {
      continue;
    }
  }
  return calls;
}

function pushToolCall(raw: any, calls: ToolCall[]) {
  if (!raw || typeof raw !== "object") return;
  const tool = String(raw.tool || raw.name || "").trim();
  if (!tool) return;
  if (tool !== "read_file" && tool !== "list_dir" && tool !== "write_file" && tool !== "run_command") return;
  calls.push({ tool: tool as ToolName, args: raw.args || raw.parameters || {} });
}

function truncate(value: string, maxChars: number): string {
  if (value.length <= maxChars) return value;
  return `${value.slice(0, maxChars)}\n…truncated (${value.length - maxChars} chars)`;
}

export async function executeToolCall(call: ToolCall, options: ToolExecutionOptions): Promise<ToolResult> {
  const { cwd, maxFileBytes, maxDirEntries, maxOutputChars } = options;
  const args = call.args || {};

  try {
    switch (call.tool) {
      case "read_file": {
        const path = String(args.path || "").trim();
        if (!path) throw new Error("Missing path");
        const fullPath = resolve(cwd, path);
        const file = await readFile(fullPath);
        const limited = file.length > maxFileBytes ? file.subarray(0, maxFileBytes) : file;
        const text = limited.toString("utf-8");
        const output = file.length > maxFileBytes ? `${text}\n…truncated (${file.length - maxFileBytes} bytes)` : text;
        return { tool: call.tool, ok: true, output: truncate(output, maxOutputChars) };
      }
      case "list_dir": {
        const path = String(args.path || ".").trim();
        const fullPath = resolve(cwd, path);
        const entries = await readdir(fullPath);
        const sliced = entries.slice(0, maxDirEntries);
        const labeled = await Promise.all(
          sliced.map(async (entry) => {
            const fullEntry = resolve(fullPath, entry);
            try {
              const stats = await stat(fullEntry);
              return stats.isDirectory() ? `${entry}/` : entry;
            } catch {
              return entry;
            }
          })
        );
        const output = labeled.join("\n") + (entries.length > maxDirEntries ? `\n…truncated (${entries.length - maxDirEntries} more)` : "");
        return { tool: call.tool, ok: true, output: truncate(output, maxOutputChars) };
      }
      case "write_file": {
        const path = String(args.path || "").trim();
        const content = String(args.content ?? "");
        if (!path) throw new Error("Missing path");
        const fullPath = resolve(cwd, path);
        await mkdir(resolve(fullPath, ".."), { recursive: true });
        await writeFile(fullPath, content, "utf-8");
        return { tool: call.tool, ok: true, output: `Wrote ${content.length} chars to ${path}` };
      }
      case "run_command": {
        const command = String(args.command || "").trim();
        if (!command) throw new Error("Missing command");
        const { stdout, stderr } = await execAsync(command, { cwd, maxBuffer: maxOutputChars * 2 });
        const output = [stdout, stderr].filter(Boolean).join("\n");
        return { tool: call.tool, ok: true, output: truncate(output || "(no output)", maxOutputChars) };
      }
      default:
        throw new Error(`Unsupported tool: ${call.tool}`);
    }
  } catch (e: any) {
    return {
      tool: call.tool,
      ok: false,
      output: "",
      error: e?.message || String(e),
    };
  }
}

export function formatToolResult(result: ToolResult): string {
  const status = result.ok ? "ok" : "error";
  const header = `Tool ${result.tool} (${status})`;
  const body = result.ok ? result.output : result.error || "Unknown error";
  return `${header}\n${body}`;
}
