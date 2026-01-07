export type LogLevel = "debug" | "info" | "warn" | "error";

function enabled(level: LogLevel): boolean {
  const env = (process.env.QLAW_LOG_LEVEL || "info").toLowerCase();
  const order: Record<LogLevel, number> = { debug: 10, info: 20, warn: 30, error: 40 };
  return order[level] >= order[env as LogLevel] ? true : env === "debug";
}

export function debug(message: string, meta?: Record<string, any>) {
  if (enabled("debug")) console.debug(message, meta || "");
}

export function info(message: string, meta?: Record<string, any>) {
  if (enabled("info")) console.info(message, meta || "");
}

export function warn(message: string, meta?: Record<string, any>) {
  if (enabled("warn")) console.warn(message, meta || "");
}

export function error(message: string, meta?: Record<string, any>) {
  if (enabled("error")) console.error(message, meta || "");
}

