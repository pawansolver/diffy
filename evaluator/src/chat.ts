// OpenAI/OpenRouter-style chat completion over fetch, with retries + timeout.
// Providers differ only in base_url + auth header/scheme + extra headers, so the
// same function serves OpenRouter, Sarvam, and anything else OpenAI-compatible.

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export interface ChatOptions {
  baseUrl: string;
  apiKey: string;
  model: string;
  messages: any[];
  tools?: any[];
  temperature?: number;
  timeoutMs?: number;
  retries?: number;
  extraHeaders?: Record<string, string>;
  authHeader?: string;
  authScheme?: string;
}

export async function chatCompletion(opts: ChatOptions): Promise<any> {
  const {
    baseUrl,
    apiKey,
    model,
    messages,
    tools,
    temperature = 0.2,
    timeoutMs = 120_000,
    retries = 2,
    extraHeaders,
    authHeader = "Authorization",
    authScheme = "Bearer ",
  } = opts;

  const url = `${baseUrl}/chat/completions`;
  const headers: Record<string, string> = {
    [authHeader]: `${authScheme}${apiKey}`,
    "Content-Type": "application/json",
    ...(extraHeaders || {}),
  };
  const body: any = { model, messages, temperature };
  if (tools && tools.length) {
    body.tools = tools;
    body.tool_choice = "auto";
  }

  let last = "";
  for (let attempt = 0; attempt <= retries; attempt++) {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), timeoutMs);
    try {
      const r = await fetch(url, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
        signal: ctrl.signal,
      });
      if (r.status === 200) return await r.json();
      last = `HTTP ${r.status}: ${(await r.text()).slice(0, 500)}`;
    } catch (e: any) {
      last = e?.name === "AbortError" ? `timeout after ${timeoutMs}ms` : String(e?.message || e);
    } finally {
      clearTimeout(timer);
    }
    await sleep(1500 * (attempt + 1));
  }
  throw new Error(`chat call failed after retries: ${last}`);
}
