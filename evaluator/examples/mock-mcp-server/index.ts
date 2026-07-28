// A tiny stdio MCP server with canned tool results, so you can exercise the
// harness's MCP wiring + tool loop without a real server. Not a real corpus.
//
// Run standalone:  pnpm mock-server
// Used by:         examples/getting-started/config.json (spawned over stdio)

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({ name: "mock-md", version: "0.1.0" });

server.tool(
  "semantic_search",
  "Search the (mock) corpus for a query; returns canned passages.",
  { query: z.string().describe("search query") },
  async ({ query }) => ({
    content: [
      {
        type: "text",
        text:
          `Top passages for "${query}":\n` +
          `1. [Manav Vyavhar Darshan, p.12] सह-अस्तित्व (co-existence) is the ` +
          `fundamental reality: nature exists as an organized whole.\n` +
          `2. [Samadhanatmak Bhautikvad, p.45] व्यवस्था (order/system) is the ` +
          `natural, self-regulating arrangement observed at every level.`,
      },
    ],
  }),
);

server.tool(
  "get_book_page",
  "Return the (mock) text of a given book page.",
  { book: z.string(), page: z.number() },
  async ({ book, page }) => ({
    content: [
      {
        type: "text",
        text: `(${book}, p.${page}) [mock page] This canned page discusses सह-अस्तित्व and व्यवस्था as they relate to मानव (the human being).`,
      },
    ],
  }),
);

server.tool("list_books", "List the (mock) books in the corpus.", {}, async () => ({
  content: [
    {
      type: "text",
      text: JSON.stringify([
        "Manav Vyavhar Darshan",
        "Samadhanatmak Bhautikvad",
        "Vyavharvadi Samajshastra",
      ]),
    },
  ],
}));

const transport = new StdioServerTransport();
await server.connect(transport);
