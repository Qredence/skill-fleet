import { resolve, relative, isAbsolute } from "path";
import type { AppSettings, PermissionMode } from "../types.ts";
import type { ToolCall, ToolName } from "./index.ts";

const DEFAULT_PERMISSIONS: Record<ToolName | "external_directory" | "doom_loop", PermissionMode> = {
  read_file: "allow",
  list_dir: "allow",
  write_file: "ask",
  run_command: "ask",
  external_directory: "ask",
  doom_loop: "ask",
};

export function isExternalPath(path: string, cwd: string): boolean {
  const resolved = resolve(cwd, path);
  const root = resolve(cwd);
  const rel = relative(root, resolved);
  if (!rel) return false;
  return rel.startsWith("..") || isAbsolute(rel);
}

function getPermission(settings: AppSettings, key: keyof typeof DEFAULT_PERMISSIONS): PermissionMode {
  return settings.tools?.permissions?.[key] || DEFAULT_PERMISSIONS[key];
}

export function resolveToolPermission(params: {
  settings: AppSettings;
  call: ToolCall;
  cwd: string;
  isDoomLoop: boolean;
}): { mode: PermissionMode; reason?: string } {
  const { settings, call, cwd, isDoomLoop } = params;

  if (!settings.tools?.enabled) {
    return { mode: "deny", reason: "tools-disabled" };
  }

  const tool = call.tool;
  let mode = getPermission(settings, tool);

  const path = typeof call.args?.path === "string" ? call.args.path.trim() : "";
  if (path && (tool === "read_file" || tool === "list_dir" || tool === "write_file")) {
    if (isExternalPath(path, cwd)) {
      const externalMode = getPermission(settings, "external_directory");
      if (externalMode === "deny") return { mode: "deny", reason: "external-directory" };
      if (externalMode === "ask") mode = "ask";
    }
  }

  if (isDoomLoop) {
    const doomMode = getPermission(settings, "doom_loop");
    if (doomMode === "deny") return { mode: "deny", reason: "doom-loop" };
    if (doomMode === "ask") mode = "ask";
  }

  if (mode === "ask" && settings.tools?.autoApprove) {
    if (tool === "read_file" || tool === "list_dir") {
      mode = "allow";
    }
  }

  return { mode };
}
