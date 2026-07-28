// Wraps an MCP client session: connects (stdio | streamable HTTP), discovers the
// server's tools as OpenAI/OpenRouter-style schemas, and executes tool calls.

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import type { Config } from "./config.js";

const DESCRIPTION_CAP = 1024; // OpenRouter truncates long tool descriptions anyway
const TOOL_RESULT_CAP = 12000; // keep verbose page dumps from blowing context

export class MCPTools {
  client: Client;
  openaiTools: any[] = [];
  private names = new Set<string>();

  constructor(client: Client) {
    this.client = client;
  }

  /** Connect to the configured MCP server and return a ready wrapper. */
  static async connect(mcp: Config["mcp"]): Promise<MCPTools> {
    let transport;
    if (mcp.transport === "stdio") {
      if (!mcp.stdio) throw new Error("mcp.transport is 'stdio' but mcp.stdio is missing.");
      const s = mcp.stdio;
      // Pass through the current env (filtering undefined) plus any overrides.
      const env: Record<string, string> = {};
      for (const [k, v] of Object.entries(process.env)) if (v !== undefined) env[k] = v;
      Object.assign(env, s.env || {});
      transport = new StdioClientTransport({
        command: s.command,
        args: s.args || [],
        env,
        cwd: s.cwd,
      });
    } else {
      if (!mcp.http) throw new Error("mcp.transport is 'http' but mcp.http is missing.");
      transport = new StreamableHTTPClientTransport(new URL(mcp.http.url), {
        requestInit: { headers: mcp.http.headers || {} },
      });
    }

    const client = new Client({ name: "dhee-eval", version: "0.1.0" }, { capabilities: {} });
    await client.connect(transport);
    return new MCPTools(client);
  }

  /** List server tools and cache them in OpenAI tool-schema form. */
  async discover(): Promise<any[]> {
    const resp = await this.client.listTools();
    for (const t of resp.tools) {
      const schema = t.inputSchema || { type: "object", properties: {} };
      this.openaiTools.push({
        type: "function",
        function: {
          name: t.name,
          description: (t.description || "").slice(0, DESCRIPTION_CAP),
          parameters: schema,
        },
      });
      this.names.add(t.name);
    }
    return this.openaiTools;
  }

  /** Execute a tool, returning a string result (truncated for context safety). */
  async call(name: string, args: Record<string, unknown>): Promise<string> {
    if (!this.names.has(name)) return `ERROR: unknown tool '${name}'.`;
    let res: any;
    try {
      res = await this.client.callTool({ name, arguments: args || {} });
    } catch (e: any) {
      return `ERROR calling ${name}: ${e?.message || e}`;
    }
    const parts: string[] = [];
    for (const c of (res.content as any[]) || []) {
      if (c?.type === "text") parts.push(c.text);
      else parts.push(JSON.stringify(c));
    }
    const out = parts.length ? parts.join("\n") : "(empty result)";
    return out.slice(0, TOOL_RESULT_CAP);
  }

  async close(): Promise<void> {
    await this.client.close();
  }
}
