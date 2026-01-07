export function getAuthHeader(
  baseUrl: string | undefined,
  apiKey: string
): Record<string, string> {
  if (baseUrl) {
    let host: string | undefined;
    try {
      host = new URL(baseUrl).host;
    } catch {
      host = undefined;
    }
    if (
      (host && (host === "azure.com" || host.endsWith(".azure.com"))) ||
      baseUrl.includes("/openai/")
    ) {
      return { "api-key": apiKey };
    }
  }
  return { Authorization: `Bearer ${apiKey}` };
}

export { buildResponsesInput } from "./llm/input.ts";

export async function listAgents(
  baseUrl: string,
  foundryEndpoint: string
): Promise<Array<{ id: string; name: string; instructions: string; model: string }>> {
  const url = `${baseUrl.replace(/\/$/, "")}/v1/agents?project_endpoint=${encodeURIComponent(
    foundryEndpoint
  )}`;
  const res = await fetch(url);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status} ${res.statusText}${text ? ` - ${text}` : ""}`);
  }
  try {
    return await res.json();
  } catch (e) {
    throw new Error(`Failed to parse response from ${url}: ${e instanceof Error ? e.message : String(e)}`);
  }
}
