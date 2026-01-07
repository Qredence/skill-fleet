export function parseModelList(value?: string): string[] {
  if (!value) return [];
  const raw = value.trim();
  if (!raw) return [];

  if (raw.startsWith("[")) {
    try {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        return parsed
          .map((item) => {
            if (typeof item === "string") return item.trim();
            if (item && typeof item === "object" && "id" in item) {
              return String((item as { id?: unknown }).id ?? "").trim();
            }
            return "";
          })
          .filter(Boolean);
      }
    } catch {
      // Fall through to delimiter parsing
    }
  }

  return raw
    .split(/[\n,]/)
    .map((part) => part.trim())
    .filter(Boolean);
}
