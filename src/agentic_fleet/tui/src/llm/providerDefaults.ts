import type { AppSettings, LlmProvider } from "../types.ts";

const DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1";

function normalizeProvider(provider?: string): LlmProvider | undefined {
  if (!provider) return undefined;
  const normalized = provider.toLowerCase();
  if (normalized === "openai" || normalized === "azure" || normalized === "litellm" || normalized === "custom") {
    return normalized as LlmProvider;
  }
  return undefined;
}

function coerceUrl(value: string | undefined): URL | null {
  if (!value) return null;
  try {
    return new URL(value);
  } catch {
    try {
      return new URL(`https://${value}`);
    } catch {
      return null;
    }
  }
}

function getHost(value: string | undefined): string | null {
  const parsed = coerceUrl(value);
  return parsed ? parsed.hostname.toLowerCase() : null;
}

function isOpenAIEndpoint(endpoint: string | undefined, envOpenaiBase: string | undefined): boolean {
  if (!endpoint) return true;
  const host = getHost(endpoint);
  if (!host) return false;
  const envHost = getHost(envOpenaiBase);
  if (envHost && host === envHost) return true;
  if (endpoint === DEFAULT_OPENAI_BASE_URL) return true;
  return host === "api.openai.com";
}

function looksLikeOpenAIModel(model: string | undefined, envOpenaiModel: string | undefined): boolean {
  if (!model) return true;
  if (envOpenaiModel && model === envOpenaiModel) return true;
  if (model.includes("/")) return false;
  const lower = model.toLowerCase();
  return (
    lower.startsWith("gpt-") ||
    lower.startsWith("o1") ||
    lower.startsWith("o3") ||
    lower.startsWith("gpt4") ||
    lower.startsWith("gpt3")
  );
}

export function applyProviderDefaults(settings: AppSettings, provider?: string): AppSettings {
  const normalized = normalizeProvider(provider);
  if (!normalized) {
    return { ...settings, provider };
  }

  const env = {
    openaiBaseUrl: process.env.OPENAI_BASE_URL,
    openaiApiKey: process.env.OPENAI_API_KEY,
    openaiModel: process.env.OPENAI_MODEL,
    litellmBaseUrl: process.env.LITELLM_BASE_URL,
    litellmApiKey: process.env.LITELLM_API_KEY,
    litellmModel: process.env.LITELLM_MODEL,
  };

  const next: AppSettings = { ...settings, provider: normalized };

  if (normalized === "litellm") {
    if (env.litellmBaseUrl && isOpenAIEndpoint(next.endpoint, env.openaiBaseUrl)) {
      next.endpoint = env.litellmBaseUrl;
    }
    if (env.litellmModel && looksLikeOpenAIModel(next.model, env.openaiModel)) {
      next.model = env.litellmModel;
    }
    if (env.litellmApiKey && (!next.apiKey || (env.openaiApiKey && next.apiKey === env.openaiApiKey))) {
      next.apiKey = env.litellmApiKey;
    }
  }

  if (normalized === "openai") {
    if (!next.endpoint || next.endpoint === env.litellmBaseUrl) {
      next.endpoint = env.openaiBaseUrl || DEFAULT_OPENAI_BASE_URL;
    }
    if (!next.model || (env.litellmModel && next.model === env.litellmModel)) {
      next.model = env.openaiModel || next.model;
    }
    if (!next.apiKey || (env.litellmApiKey && next.apiKey === env.litellmApiKey)) {
      next.apiKey = env.openaiApiKey || next.apiKey;
    }
  }

  return next;
}
