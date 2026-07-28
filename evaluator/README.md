# dhee-eval

*dhee* (धी) — intellect, discernment.

A small, reusable harness for evaluating LLMs on **tool-calling RAG** through a
real [MCP](https://modelcontextprotocol.io) server. Point it at your MCP server,
your questions, and your scoring rubric, and it tells you which model is best —
with hard metrics (tool-use rate, latency, tokens, cost) and LLM-judge scores.

## Origin

This was built to answer a concrete question: **which LLM should power the
[Madhyasth Darshan](https://en.wikipedia.org/wiki/Madhyasth_Darshan) study
assistant?** That assistant retrieves from the works of Shree A. Nagraj via an MCP
server and must answer faithfully - grounded in the source texts, citing pages,
without hallucinating a doctrinal corpus. Picking a model by vibes wasn't good
enough, so this harness runs the *real* tool loop against each candidate and
scores the results. It turned out to be generic enough to open-source: any
MCP-backed assistant can be evaluated the same way.

## Profiles

The harness is built around **profiles**: distinct assistant configurations (each
with its own system prompt, question set, and judge rubric) that you sweep over the
**same list of candidate LLMs**. The Madhyasth Darshan example ships two —

- **Anand** — answers in plain, everyday language, *avoiding* technical jargon
  (judged on `simplicity`).
- **Astitva** — answers using *exact* Madhyasth Darshan terms in Devanagari
  (judged on `devanagari` fidelity).

The eval matrix is therefore **profile × model × question**, and the winner may
differ per profile (a cheap model may suffice for Anand; Astitva may need a model
with stronger Devanagari fidelity).

## How it works

For every (profile × model × question):

1. Sends the question to the model with the MCP server's tools attached.
2. Runs the **full tool loop**: model calls a tool → harness executes it against
   your real MCP server → result fed back → repeat until a final answer.
3. An **LLM judge** scores the answer 1–5 on **that profile's dimensions**.
4. Logs hard metrics: tool-call rate, iterations, latency, tokens, and **cost**
   (from `pricing.json`).

Outputs a per-run `runs_*.jsonl` (full answers + transcripts), a `scores_*.json`
(aggregated), and a per-profile console summary. Open `viewer/index.html` to read
answers + transcripts interactively.

## Setup

```bash
pnpm install
cp .env.example .env    # then set OPENROUTER_API_KEY
```

## Quick start (no real server needed)

A bundled **mock MCP server** (`examples/mock-mcp-server`) returns canned tool
results so you can exercise the wiring. First, confirm MCP discovery works without
even needing an API key:

```bash
pnpm eval --config examples/getting-started/config.json --list-tools
```

Then a real smoke run (needs `OPENROUTER_API_KEY`):

```bash
pnpm eval --config examples/getting-started/config.json --limit-questions 2 --no-judge
pnpm eval --config examples/getting-started/config.json          # with the judge
```

## Running your own eval

Edit a config JSON (start from `examples/madhyasth-darshan/config.json`). The one
required change is pointing `mcp` at your server:

- **stdio** (harness launches it): set `mcp.transport: "stdio"` and
  `mcp.stdio.command` / `args`.
- **http** (already running): set `mcp.transport: "http"` and `mcp.http.url`.

```bash
pnpm eval --config examples/madhyasth-darshan/config.json                 # all profiles
pnpm eval --config examples/madhyasth-darshan/config.json --profile anand # one profile
pnpm eval --config examples/madhyasth-darshan/config.json --concurrency 8
```

### Local configs

Configs with machine-specific paths (like `mcp.stdio.args` pointing at your MCP
build) or private model lists shouldn't be committed. Any file matching
`*.local.json` is gitignored — copy an example, edit it, and point `--config` at it:

```bash
cp examples/madhyasth-darshan/config.json examples/madhyasth-darshan/config.local.json
# edit config.local.json → set mcp.stdio.args to your real server path
pnpm eval --config examples/madhyasth-darshan/config.local.json
```

Keep the copy in the same directory as the example so its relative `questions`
paths still resolve.

### CLI flags

| flag | meaning |
|---|---|
| `--config <path>` | config JSON (default `config.json`) |
| `--profile <a,b>` | only run these profile name(s) |
| `--limit-models <n>` | cap models under test |
| `--limit-questions <n>` | cap questions per profile |
| `--concurrency <n>` | parallel tasks (overrides `run.concurrency`) |
| `--no-judge` | skip the LLM judge (faster smoke tests) |
| `--list-tools` | connect to the MCP server, print its tools, exit |
| `--pricing <path>` | pricing JSON for cost (default `pricing.json`) |
| `--outdir <dir>` | output directory (default `results`) |

## Config schema

```jsonc
{
  "providers": {                       // OpenAI-compatible endpoints
    "openrouter": { "base_url": "...", "api_key_env": "OPENROUTER_API_KEY",
                    "extra_headers": { "X-Title": "..." } },
    "sarvam":     { "base_url": "...", "api_key_env": "SARVAM_API_KEY",
                    "auth_header": "api-subscription-key", "auth_scheme": "" }
  },
  "mcp":    { "transport": "stdio", "stdio": { "command": "...", "args": [...] } },
  "models": [ { "id": "google/gemini-2.5-flash", "label": "...",
                "provider": "openrouter" } ],       // candidate LLMs (shared)
  "judge":  { "id": "anthropic/claude-sonnet-5", "temperature": 0.0 },
  "run":    { "max_tool_iterations": 10, "temperature": 0.2,
              "request_timeout_s": 120, "retries": 2,
              "save_transcripts": true, "concurrency": 4 },
  "profiles": [                        // each swept over every model above
    {
      "name": "anand",
      "questions": "anand.questions.json",   // path relative to this config file
      "system_prompt": "...",
      "dimensions": [                        // this profile's judge rubric
        { "name": "tool_use",       "description": "..." },
        { "name": "faithfulness",   "description": "..." },
        { "name": "simplicity",     "description": "..." },
        { "name": "answer_quality", "description": "..." }
      ]
    }
  ]
}
```

Each **question file** is a JSON array of
`{ "id", "category", "question", "expectation" }`. `category` is free-form
(`lookup` / `conceptual` / `adversarial` in the examples); `expectation` is
guidance for the judge, not a rigid answer key.

The judge system prompt is composed from an editable preamble (`judge.preamble`,
optional) plus each profile's `dimensions`. Add or remove dimensions freely — the
CSV/JSON columns, console summary, and viewer all adapt to whatever you declare.

## Pricing / cost

`pricing.json` maps model ids to `$/M` token rates. Refresh it from the live
OpenRouter models list:

```bash
pnpm fetch-models        # writes pricing.json (tool-capable models, cheapest first)
```

Cost per row uses the model that actually served the request (matters for
`openrouter/auto`, whose routing is recorded per question and shown in the summary
under **AUTO ROUTING**).

## Notes

- One MCP session is reused for the whole run; tasks run up to `concurrency` in
  parallel over it.
- Tool results are truncated to 12k chars before being fed back (adjust in
  `src/mcp.ts`).
- If a model never calls tools (`tool% = 0`), it likely doesn't support tools on
  its current route — pin a provider or drop it.

## Sample results

Real runs from the Madhyasth Darshan eval live in
[`examples/sample-results/`](examples/sample-results/) — drop any `runs_*.jsonl`
there into `viewer/index.html` to see the output format without running an eval.

## Project layout

```
src/            harness (cli, config, mcp, chat, runner, judge, pricing, report, pool)
examples/       madhyasth-darshan (anand/astitva) · getting-started · mock-mcp-server
                · sample-results (real runs, browsable in the viewer)
scripts/        fetch-models.ts (refresh pricing.json)
viewer/         index.html (drop a runs_*.jsonl in to browse)
```
