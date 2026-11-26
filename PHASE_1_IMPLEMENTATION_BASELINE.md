# PHASE 1 IMPLEMENTATION BASELINE: CODE AUDIT & COMPATIBILITY MAP
**Document ID:** `PHASE_1_IMPLEMENTATION_BASELINE.md`  
**Repository:** `c:\Users\pawan\Downloads\diffy-main\diffy-main`  
**Branch:** `main` | **Commit Baseline:** `75881f3`  
**Generated:** 2026-11-23  
**Status:** AUDIT COMPLETE — BASELINE LOCKED

---

## 1. EXISTING REPOSITORY ARCHITECTURE

### 1.1 Server Entry Points & Transport
- **`app.py`:**
  - Production ASGI Starlette application.
  - Mounts FastMCP server at `/mcp` using `StreamableHttpTransport`.
  - Appends alias route `/mcp/` to ensure trailing-slash tolerance.
  - Inserts auxiliary routes: `GET /health`, `GET /get-base-instruction`, `GET /get-default-user-prompt`, `GET /`.
  - Applies `ApiKeyMiddleware` validating optional `Bearer <MCP_API_KEY>`.
- **`main.py`:**
  - Instantiates `SkillsProviderServer` and `FastMCP("Skills Provider", instructions=BASE_SYSTEM_INSTRUCTION)`.
  - Wraps `SkillsDirectoryProvider` pointing to configured local directories.
  - Provides GitHub remote skill fetching fallback with a 1-hour in-memory cache.
  - Registers 3 core MCP tools: `list_skills`, `get_skill`, `list_skill_files`.
- **`instruction_api.py`:**
  - Standalone FastAPI application on port 8000 providing REST endpoints (`/get-base-instruction`, `/get-instruction`) primarily for Dify HTTP node integration.
- **`config.py`:**
  - Pydantic models: `SkillsConfig`, `HttpConfig`, `GatewayConfig`, `GithubConfig`.
  - Loads [skills.settings.json](file:///c:/Users/pawan/Downloads/diffy-main/diffy-main/skills.settings.json).

---

## 2. EXISTING API CONTRACTS & CONSUMER DEPENDENCIES

### 2.1 MCP Tools Contract
| Tool Name | Parameters | Output Schema | Error Behavior |
|---|---|---|---|
| `list_skills` | None | `List[Dict[str, str]]` (`name`, `description`, `source`) | Returns empty list if no skills found. |
| `get_skill` | `skill_name: str` | `str` (Raw Markdown text) | Returns `SKILL_NOT_FOUND: ...` string if missing. |
| `list_skill_files` | `skill_name: str` | `List[str]` (List of relative filenames) | Returns empty list if missing. |

### 2.2 Active Consumers
1. **ProductSpeaker ([C:\ProductSpeaker\backend\ai\mcp_client.py](file:///C:/ProductSpeaker/backend/ai/mcp_client.py)):**
   - Connects to `/mcp` via `fastmcp.Client`.
   - Discovers tools via `list_tools()`.
   - Calls `list_skills()` to build system instruction catalogs.
   - Dispatches `get_skill(skill_name)` dynamically during multi-turn LLM agent execution.
2. **Open WebUI ([c:\Users\pawan\Downloads\llm-main\llm-main\backend\open_webui\utils\middleware.py](file:///c:/Users/pawan/Downloads/llm-main/llm-main/backend/open_webui/utils/middleware.py)):**
   - Resolves MCP tool server connection `diffy` or `skills`.
   - Intercepts user messages and queries `list_skills` / `get_skill` to inject skill instructions into system prompts.

---

## 3. COMPLETE EXISTING SKILL INVENTORY (18 SKILLS)

All 18 skills currently reside in flat directories directly under `skills/`:

| # | Skill Name | Path | Size | Frontmatter Description |
|---|---|---|---|---|
| 1 | `adaptive-authoritative-style` | `skills/adaptive-authoritative-style/SKILL.md` | 20,070 B | Balances high responsiveness and clear developmental boundaries (Baumrind). |
| 2 | `child-development-sequence` | `skills/child-development-sequence/SKILL.md` | 22,708 B | Piaget/Erikson developmental cognitive/emotional milestones for parenting. |
| 3 | `civic-dialogue-consensus` | `skills/civic-dialogue-consensus/SKILL.md` | 3,704 B | De-escalates political and ideological disputes, focusing on shared humanity. |
| 4 | `context-evaluation-framework` | `skills/context-evaluation-framework/SKILL.md` | 23,225 B | Micro, Meso, Macro environmental stressor audit. |
| 5 | `dimensional-decision-making` | `skills/dimensional-decision-making/SKILL.md` | 23,992 B | Multi-criteria 5-dimensional trade-off decision matrix. |
| 6 | `dimensional-loops` | `skills/dimensional-loops/SKILL.md` | 21,777 B | Identifies self-reinforcing interpersonal conflict patterns. |
| 7 | `dimensional-principle-of-solution-design` | `skills/dimensional-principle-of-solution-design/SKILL.md` | 24,044 B | Systems engineering principles for restorative, non-zero-sum solutions. |
| 8 | `dimensional-stability-index` | `skills/dimensional-stability-index/SKILL.md` | 23,685 B | Quantitative resilience and emotional volatility scoring. |
| 9 | `documentation-skill` | `skills/documentation-skill/SKILL.md` | 19,695 B | Standardizes executive recaps, action items, and structured Markdown output. |
| 10 | `etar-framework` | `skills/etar-framework/SKILL.md` | 27,084 B | Emotion-Trigger-Action-Result cognitive behavioral loop analysis. |
| 11 | `example-skill` | `skills/example-skill/SKILL.md` | 1,857 B | Demonstrates FastMCP skill provider structure and supporting files. |
| 12 | `feminine-masculine-dimensional-dynamics` | `skills/feminine-masculine-dimensional-dynamics/SKILL.md` | 20,815 B | Archetypal relational polarity and communication bids in intimate relationships. |
| 13 | `gendered-communication-personalization` | `skills/gendered-communication-personalization/SKILL.md` | 24,444 B | Calibrates empathy tokens and directness across communication styles. |
| 14 | `intergenerational-joint-family` | `skills/intergenerational-joint-family/SKILL.md` | 4,265 B | Resolves in-law friction, elder loneliness, and autonomy vs tradition. |
| 15 | `misapplication-ethics` | `skills/misapplication-ethics/SKILL.md` | 22,011 B | Guardrails against emotional manipulation, coercive control, and misuse. |
| 16 | `residential-community-harmony` | `skills/residential-community-harmony/SKILL.md` | 3,974 B | De-escalates neighborhood, apartment, noise, parking, and RWA disputes. |
| 17 | `resilience-scoring-system` | `skills/resilience-scoring-system/SKILL.md` | 22,140 B | Psychometric evaluation of stress adaptation and coping capacity. |
| 18 | `vyavastha-typology-feedback-loops` | `skills/vyavastha-typology-feedback-loops/SKILL.md` | 21,648 B | Madhyasth Darshan systemic harmony across Individual, Family, Society, Nature. |

---

## 4. COMPATIBILITY & REGRESSION RISKS

1. **Path Invariance Requirement:** Existing consumers look for skills under `skills/<skill_name>/SKILL.md`. **Existing folders MUST NOT be physically moved or renamed.**
2. **Tool Signature Preservation:** `list_skills()`, `get_skill()`, and `list_skill_files()` must return identical data structures. New capabilities must be exposed via **new, additive MCP tools**:
   - `understand_human_problem`
   - `route_skills`
3. **No External LLM API Overhead:** The router must work deterministically without introducing paid external API dependencies (such as unapproved OpenAI/Anthropic keys).
4. **Auth Preservation:** `ApiKeyMiddleware` must continue to guard both old and new routes uniformly when `MCP_API_KEY` is configured.

---

## 5. FILES PROPOSED FOR MODIFICATION & CREATION

### Files to Modify:
- [main.py](file:///c:/Users/pawan/Downloads/diffy-main/diffy-main/main.py): Register new tools (`understand_human_problem`, `route_skills`), update `BASE_SYSTEM_INSTRUCTION` to replace robotic missing skill fallback with safe empathetic fallback.

### New Modules to Create:
- `router/__init__.py`: Package initialization.
- `router/taxonomy.py`: Pydantic models for the multi-dimensional taxonomy, safety indicators, and uncertainty representation.
- `router/taxonomy_config.json`: Extensible multilingual taxonomy configuration (domains, relations, patterns, emotional signals, intentions, multilingual synonyms in English, Hindi, Hinglish).
- `router/registry.py`: Non-invasive Skill Registry loading all 18 existing skills into 4 logical tiers.
- `router/skills_metadata.json`: Rich metadata mapping for the 18 skills into Tiers 1–4.
- `router/analyzer.py`: Human problem understanding engine implementing `understand_human_problem`.
- `router/skill_router.py`: Dynamic skill router implementing `route_skills` with safety precedence.
- `evaluator/scenarios/100_human_scenarios.json`: Comprehensive 100-scenario multilingual evaluation benchmark.
- `tests/test_taxonomy_and_registry.py`: Unit tests for taxonomy schema & skill registry.
- `tests/test_router_and_tools.py`: Unit tests for router logic, safety precedence, and MCP tool handlers.
- `tests/test_100_scenarios.py`: Automated benchmark evaluation test suite executing all 100 scenarios.

### Files That Must Remain Unchanged:
- All 18 existing `skills/*/SKILL.md` files.
- `config.py`
- `instruction_api.py`
- `skills.settings.json`
- `evaluator/package.json` & existing evaluator test files.
