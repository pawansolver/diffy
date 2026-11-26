# PHASE 2 — INTEGRATION GAP REPORT
## Smart Human Problem Understanding & Dynamic Skill Routing Framework
**Project Owner:** Pawan Kumar  
**Audit Scope:** Issue Identification, Root Cause Analysis, Regression Risk Assessment, Remediation Specifications  
**Status:** AUDIT ONLY (Zero Existing Code Modification)

---

## 1. GAP INVENTORY SUMMARY

| Issue ID | Severity | Repository | Affected Component | Summary of Impact |
|---|---|---|---|---|
| **GAP-01** | **CRITICAL** | `llm-main` | `routers/mediation.py` | Mediation engine runs 3-party dispute simulation on domestic violence scenarios without safety checks. |
| **GAP-02** | **CRITICAL** | `llm-main` | `routers/mediation.py` | Mediation engine has no connection to Diffy FastMCP tools or skills. |
| **GAP-03** | **HIGH** | `llm-main` | `utils/middleware.py` | Chat middleware relies on voluntary LLM tool calling; never executes `understand_human_problem` or `route_skills`. |
| **GAP-04** | **MEDIUM** | `llm-main` | `utils/middleware.py` | Hardcoded 15-skill enum ignores 3 new skills added in Phase 1. |
| **GAP-05** | **CRITICAL** | `ProductSpeaker` | `core/assistant.py` | Voice pipeline sends user transcripts directly to Gemini without calling problem understanding or safety routing. |
| **GAP-06** | **HIGH** | `ProductSpeaker` | `core/assistant.py`, `ai/mcp_client.py` | Silent fallback on MCP downtime allows ungrounded Gemini responses with zero safety triage. |
| **GAP-07** | **HIGH** | `ProductSpeaker` | `core/memory.py` | All voice queries default to a shared `default_user` profile, leaking private facts across household members. |
| **GAP-08** | **MEDIUM** | `diffy-main` | `app.py` | Missing `mcp-session-id` header in HTTP JSON-RPC calls produces HTTP 400 `-32600` errors. |
| **GAP-09** | **MEDIUM** | `diffy-main` | `app.py` | FastMCP Streamable HTTP requires an active ASGI lifespan context; ad-hoc client calls raise `RuntimeError`. |
| **GAP-10** | **LOW** | `ProductSpeaker` | `ai/gemini_service.py` | System prompt does not adapt dynamically to Hindi / Hinglish colloquial dispute resolution styles. |

---

## 2. DETAILED GAP REPORTS

### GAP-01: Mediation Router Runs Simulation on Domestic Violence Scenarios
- **Severity:** **CRITICAL**
- **Repository:** `llm-main` (`Open WebUI`)
- **File Path:** `backend/open_webui/routers/mediation.py`
- **Class / Function:** `MultiAgentMediationEngine.simulate_dialogue_round`, `simulate_mediation_pipeline` (lines 200–320)
- **Current Behavior:** The mediation endpoint `/api/v1/mediation/simulate` takes any `conflict_scenario` string and immediately executes dialogue rounds between `Party A` (aggrieved) and `Party B` (defensive), followed by an attempt by `Sarah Collins` to forge a compromise agreement.
- **Expected Behavior:** Every conflict scenario must pass through Diffy MCP `understand_human_problem` before any simulation starts. If `domestic_violence`, `self_harm`, `child_abuse`, or `threat_immediate_harm` is detected, the endpoint must abort the simulation immediately with HTTP 403/422, activate `safety_lockout = True`, and return protective helpline guidance.
- **Root Cause:** The mediation router was built as a standalone NVC demonstration without any intake risk screening or integration with Diffy's safety triage.
- **Proposed Solution:** Introduce a pre-execution safety interceptor in `simulate_mediation_pipeline`. Call Diffy MCP `understand_human_problem`. If `severity_level == "CRITICAL"` or safety flags are present, abort simulation and return emergency safety directives.
- **Dependencies:** Active Diffy FastMCP server.
- **Regression Risks:** None. Valid non-violent dispute scenarios will continue to mediation.
- **Verification Method:** Send payload: *"My husband beat me yesterday and locked me in the room"* to `/api/v1/mediation/simulate`. Verify simulation is aborted and crisis helplines are returned.

---

### GAP-02: Mediation Engine Has Zero Diffy FastMCP Integration
- **Severity:** **CRITICAL**
- **Repository:** `llm-main` (`Open WebUI`)
- **File Path:** `backend/open_webui/routers/mediation.py`
- **Class / Function:** `MultiAgentMediationEngine._call_llm` and `simulate_mediation_pipeline` (lines 46–49, 138–165)
- **Current Behavior:** The router looks for knowledge only via `Knowledges.get_knowledge_by_id(db, knowledge_id)` querying local vector DB collections. It never queries Diffy FastMCP.
- **Expected Behavior:** The mediator persona and party personas should be grounded dynamically using Diffy MCP skills (`nonviolent-communication`, `marital-conflict-resolution`, `de-escalation-tactics`, `boundary-setting`).
- **Root Cause:** Diffy MCP client was implemented only in `DiffySkillMiddleware` for general chat, leaving `mediation.py` completely isolated.
- **Proposed Solution:** Inject an MCP client instance or shared orchestrator into `MultiAgentMediationEngine` to dynamically fetch required skill instructions from Diffy FastMCP.
- **Dependencies:** Diffy FastMCP `get_skill` tool.
- **Regression Risks:** Low. Fallback to hardcoded NVC prompts if MCP is unreachable.
- **Verification Method:** Run mediation on a workplace dispute; verify that the mediator report explicitly cites Diffy's `workplace-dispute-resolution` and `nonviolent-communication` playbooks.

---

### GAP-03: Chat Middleware Relies on Voluntary LLM Tool Calling
- **Severity:** **HIGH**
- **Repository:** `llm-main` (`Open WebUI`)
- **File Path:** `backend/open_webui/utils/middleware.py`
- **Class / Function:** `DiffySkillMiddleware.__call__` and `DEFAULT_SKILLS_USER_PROMPT` (lines 2780–2830)
- **Current Behavior:** The middleware appends a system prompt instructing the LLM that `list_skills` and `get_skill` are available as tools. It relies on the LLM deciding on its own to invoke the tool. It does not mention or execute `understand_human_problem` or `route_skills`.
- **Expected Behavior:** The middleware must execute `understand_human_problem` and `route_skills` deterministically *before* passing the request to the LLM. Relevant skill instructions should be directly injected into the LLM context.
- **Root Cause:** Middleware was authored prior to the creation of Phase 1's dynamic problem understanding and skill router.
- **Proposed Solution:** Refactor `DiffySkillMiddleware` to execute a 2-step pre-generation pipeline: (1) Call `understand_human_problem`, (2) Call `route_skills`. Prepend the selected skills to the system prompt.
- **Dependencies:** Diffy FastMCP `understand_human_problem` and `route_skills` tools.
- **Regression Risks:** Adds ~50–80ms to completion start time; must use persistent HTTP connection pooling to prevent latency spikes.
- **Verification Method:** Send a Hindi message: *"Meri beti meri baat nahi sunti"* without requesting tools. Verify that the LLM system prompt includes `parent-child-mediation` and `active-listening` instructions.

---

### GAP-04: Hardcoded 15-Skill Enum in Open WebUI Middleware
- **Severity:** **MEDIUM**
- **Repository:** `llm-main` (`Open WebUI`)
- **File Path:** `backend/open_webui/utils/middleware.py`
- **Variable:** `known_diffy_skills` (lines 2892–2908)
- **Current Behavior:** A hardcoded list of 15 skills is used as the parameter enum for `get_skill`. The 3 skills added in Phase 1 (`intergenerational-joint-family`, `residential-community-harmony`, `civic-dialogue-consensus`) are missing.
- **Expected Behavior:** Skill names must be dynamically loaded from Diffy MCP `list_skills` at startup or refreshed periodically.
- **Root Cause:** Static enum list was hardcoded during initial proof of concept.
- **Proposed Solution:** Replace the static list with a cached call to `list_skills`.
- **Dependencies:** Diffy MCP `list_skills`.
- **Regression Risks:** None.
- **Verification Method:** Inspect the tool schema presented to the model; verify all 18 skills are present.

---

### GAP-05: Voice Pipeline Bypasses Problem Understanding & Safety Routing
- **Severity:** **CRITICAL**
- **Repository:** `ProductSpeaker`
- **File Path:** `backend/core/assistant.py`
- **Class / Function:** `AssistantCore.process_text_input` and `_build_system_instruction` (lines 328–350, 420–470)
- **Current Behavior:** Speech-to-text transcript is passed directly to `gemini_service.generate_response`. System instruction only tells Gemini about `list_skills` and `get_skill`. Neither `understand_human_problem` nor `route_skills` is invoked.
- **Expected Behavior:** Voice transcripts must be analyzed via `understand_human_problem` and `route_skills` prior to generating an audio response. If safety flags are detected, Gemini must be locked into safety safeguarding.
- **Root Cause:** ProductSpeaker integration was not updated after Phase 1 tools were implemented in Diffy.
- **Proposed Solution:** Add an orchestration step in `AssistantCore.process_text_input` that executes `mcp_client.call_tool("understand_human_problem", ...)` and `mcp_client.call_tool("route_skills", ...)`, injecting the resulting guidance into Gemini's prompt.
- **Dependencies:** ProductSpeaker `MCPSkillsClient`.
- **Regression Risks:** Adds ~60–100ms latency to voice response; must be executed asynchronously with connection reuse.
- **Verification Method:** Speak to ESP32: *"Mera beta ghar chhod kar chala gaya"*. Verify Gemini response follows `parent-child-mediation` and `active-listening` protocols.

---

### GAP-06: Silent Fallback on MCP Downtime Bypasses Safety
- **Severity:** **HIGH**
- **Repository:** `ProductSpeaker`
- **File Path:** `backend/core/assistant.py` (lines 200–240), `backend/ai/gemini_service.py` (lines 140–165)
- **Current Behavior:** If Diffy FastMCP is unreachable, `mcp_active` is set to `False` and Gemini responds from general weights without any knowledge base or safety triage.
- **Expected Behavior:** If Diffy MCP is down, the system must engage a lightweight local safety screening fallback (using regex/keyword checks for self-harm and domestic abuse) before calling Gemini. Safety must never be silently bypassed.
- **Root Cause:** Resiliency design prioritized availability over safety adherence.
- **Proposed Solution:** Implement an in-memory emergency rule-engine fallback in `AssistantCore` that catches critical distress keywords even if Diffy MCP is down.
- **Dependencies:** None.
- **Regression Risks:** Minimal; only triggers when Diffy MCP is completely down.
- **Verification Method:** Terminate Diffy MCP process; speak a self-harm prompt into ProductSpeaker; verify assistant still responds with crisis helplines.

---

### GAP-07: Shared Smart Speaker Memory Leaks Private Household Facts
- **Severity:** **HIGH**
- **Repository:** `ProductSpeaker`
- **File Path:** `backend/core/memory.py`
- **Class / Function:** `SQLiteMemoryStore.store_fact`, `retrieve_context` (lines 40–59, 120–135)
- **Current Behavior:** `store_fact` defaults to `uid = user_id or "default_user"`. All people speaking to the speaker write and retrieve facts from the same bucket.
- **Expected Behavior:** Smart speaker memory must be partitioned by session, or require explicit user confirmation before storing facts. Sensitive personal disclosures must never be stored in `user_facts`.
- **Root Cause:** Desktop voice assistant prototype design lacked multi-user voice authentication.
- **Proposed Solution:** Restrict long-term fact storage to explicit opt-in. Implement a privacy filter that blocks storing relational, medical, or legal grievances in `user_facts`.
- **Dependencies:** None.
- **Regression Risks:** None.
- **Verification Method:** Say: *"Mujhe depression ki dawai leni hai"*. Verify this fact is not saved into `user_facts` for `"default_user"`.

---

### GAP-08: Missing MCP Session ID Header Produces HTTP 400 Errors
- **Severity:** **MEDIUM**
- **Repository:** `diffy-main`
- **File Path:** `app.py`, `instruction_api.py`
- **Current Behavior:** FastMCP Streamable HTTP requires `mcp-session-id` on all calls after `initialize`. Clients sending standard JSON-RPC without this header receive HTTP 400 `-32600 "Missing session ID"`.
- **Expected Behavior:** Clients must capture and retain `mcp-session-id` from the handshake response and pass it in subsequent headers.
- **Root Cause:** FastMCP Streamable HTTP protocol specification requirement.
- **Proposed Solution:** Update `MCPSkillsClient` in `ProductSpeaker` and `DiffySkillMiddleware` in `Open WebUI` to persist `mcp-session-id` in their HTTP session pools.
- **Dependencies:** `httpx` / `aiohttp` client session management.
- **Regression Risks:** None.
- **Verification Method:** Execute 10 consecutive tool calls; verify 100% success rate without 400 errors.

---

### GAP-09: FastMCP Streamable HTTP Requires Active ASGI Lifespan Context
- **Severity:** **MEDIUM**
- **Repository:** `diffy-main`
- **File Path:** `app.py`
- **Current Behavior:** Invoking the Starlette ASGI app directly in test scripts without `lifespan_context` triggers `RuntimeError: Task group is not initialized`.
- **Expected Behavior:** When running via Uvicorn or test harnesses, lifespan must be properly entered.
- **Root Cause:** FastMCP's `StreamableHTTPSessionManager` initializes its internal `anyio` task group during ASGI lifespan startup.
- **Proposed Solution:** Ensure all production runners use `uvicorn app:app --lifespan on` and test scripts use `async with app.router.lifespan_context(app):`.
- **Dependencies:** Uvicorn / Starlette.
- **Regression Risks:** None.
- **Verification Method:** Launch server via Uvicorn; send concurrent tool requests; verify no task group errors.

---

### GAP-10: Voice Assistant Does Not Adapt to Hindi / Hinglish Nuances
- **Severity:** **LOW**
- **Repository:** `ProductSpeaker`
- **File Path:** `backend/ai/gemini_service.py`
- **Class / Function:** `GeminiService._prepare_generation_context` (lines 280–310)
- **Current Behavior:** Gemini is instructed with a static English prompt regardless of whether the user speaks Hindi or Hinglish.
- **Expected Behavior:** When the user speaks Hindi or Hinglish, the system prompt should adapt with culturally grounded empathy (e.g. respecting joint family dynamics, elder respect, and colloquial Hindi warmth).
- **Root Cause:** Static system prompt template.
- **Proposed Solution:** Inject language-aware framing into the prompt when `language_detected == "hi"` or `"hinglish"`.
- **Dependencies:** Language detector in `backend/voice/language_detector.py`.
- **Regression Risks:** None.
- **Verification Method:** Speak in Hindi: *"Bahu aur saas me ladaai ho gayi"*; verify response uses culturally appropriate and respectful phrasing.
