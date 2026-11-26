# PHASE 2 — COMPLETE SYSTEM INTEGRATION AUDIT
## Smart Human Problem Understanding & Dynamic Skill Routing Framework
**Project Owner:** Pawan Kumar  
**Audit Date:** November 2026  
**Status:** AUDIT ONLY (Zero Existing Code Modification)  
**Target Systems:**
1. **Diffy MCP** (`c:\Users\pawan\Downloads\diffy-main\diffy-main`)
2. **Open WebUI** (`c:\Users\pawan\Downloads\llm-main\llm-main`)
3. **ProductSpeaker** (`C:\ProductSpeaker`)

---

## 1. EXECUTIVE SUMMARY & AUDIT SCOPE

This comprehensive system audit evaluates the readiness and integration architecture of three standalone repositories to unify them into a single human-centered AI platform:

1. **Diffy FastMCP (`diffy-main`):** Acts as the cognitive engine, knowledge base, human problem classifier, and safety-first skill router.
2. **Open WebUI (`llm-main`):** Provides the multi-user web chat interface, multi-agent mediation workspace (`/api/v1/mediation`), and LLM completion middleware.
3. **ProductSpeaker (`ProductSpeaker`):** Provides the voice AI assistant on ESP32-S3 hardware with STT (Whisper/Faster-Whisper/Groq), Google Gemini AI, Neural TTS (Edge-TTS), and local SQLite persistence.

### High-Level Audit Findings
| System / Boundary | Current Integration Status | Primary Operational Gaps | Safety Compliance |
|---|---|---|---|
| **Diffy MCP Engine** | Operational & Tested (35/35 tests passed) | Requires active ASGI lifespan context and `mcp-session-id` header in HTTP JSON-RPC calls. | **High**: Dynamic safety triage and domestic violence / self-harm lockouts verified. |
| **Open WebUI <-> Diffy MCP** | Partially Connected (Discovery Only) | Middleware only prompts the LLM to call `list_skills` and `get_skill`. `understand_human_problem` and `route_skills` are **never executed**. Hardcoded 15-skill list in middleware ignores 3 Phase 1 skills. | **Critical Risk**: Mediation router (`mediation.py`) has zero Diffy connection; domestic violence scenarios trigger simulated debate between abuser and victim. |
| **ProductSpeaker <-> Diffy MCP** | Partially Connected (Discovery Only) | System prompt only informs Gemini about `list_skills`, `get_skill`, `list_skill_files`. Dynamic problem understanding and skill routing are **never called**. MCP failure silently falls back to ungrounded Gemini responses with zero safety triage. | **High Risk**: Voice queries bypass safety triage; all voice users share a single unpartitioned `default_user` memory store. |

---

## 2. SECTION 1 — AUDIT DIFFY MCP

### 2.1 Component Architecture & Files Audited
- **Core Server:** `main.py`, `app.py`, `config.py`, `instruction_api.py`
- **Dynamic Routing & Taxonomy:** `human_understanding.py`, `skill_router.py`, `taxonomy.py`, `taxonomy.json`, `skills_registry.json`
- **Skill Knowledge Base:** 18 Markdown skill files located in `skills/*/SKILL.md`
- **Test Suite:** `tests/test_phase1_benchmark.py`, `tests/test_server.py`, `tests/test_router.py`

### 2.2 Phase 1 Tool Verification
Runtime verification was performed by spinning up the Starlette ASGI HTTP server on port 7860 and sending raw JSON-RPC 2.0 payloads over the Streamable HTTP transport (`/mcp`):

1. **`understand_human_problem`**:
   - **Input Parameters:**
     ```json
     {
       "text": "My husband hit me yesterday and threatened me if I talk to anyone.",
       "conversation_history": [],
       "metadata": {"channel": "text"}
     }
     ```
   - **Verified Output:**
     ```json
     {
       "domains": ["marriage_and_relationships", "individual_emotional_support"],
       "people_involved": ["spouse_partner"],
       "problem_patterns": ["power_struggle", "escalating_conflict", "abuse_coercion"],
       "emotional_signals": ["fear_terror", "shame_worthlessness"],
       "user_intention": "safety_seeking",
       "severity_level": "CRITICAL",
       "safety_indicators": ["domestic_violence", "threat_immediate_harm"],
       "context_factors": ["trauma_vulnerability", "high_stress_crisis"],
       "clarification_required": false,
       "clarification_questions": [],
       "confidence_score": 0.95
     }
     ```
2. **`route_skills`**:
   - **Input Parameters:**
     Passes the structured analysis from `understand_human_problem` with optional context.
   - **Verified Output (Safety Override Triggered):**
     ```json
     {
       "selected_skills": [
         "domestic-violence-safeguard",
         "emotional-safety-triage",
         "boundary-setting",
         "referral-guidance"
       ],
       "core_conversation_skills": ["active-listening", "empathy-validation"],
       "domain_knowledge_skills": [],
       "scenario_playbooks": [],
       "safety_boundary_skills": [
         "domestic-violence-safeguard",
         "emotional-safety-triage",
         "boundary-setting",
         "referral-guidance"
       ],
       "excluded_skills": [
         "marital-conflict-resolution",
         "nonviolent-communication",
         "de-escalation-tactics"
       ],
       "safety_lockout": true,
       "requires_emergency_protocol": true,
       "routing_rationale": "CRITICAL safety flags detected: ['domestic_violence', 'threat_immediate_harm']. Suppressed dispute mediation skills to prevent victim endangerment."
     }
     ```

### 2.3 Existing Skills Inventory (All 18 Skills Verified)
1. `active-listening` (Core Human Conversation)
2. `empathy-validation` (Core Human Conversation)
3. `nonviolent-communication` (Core Human Conversation)
4. `clarification-framework` (Core Human Conversation)
5. `boundary-setting` (Core Human Conversation)
6. `de-escalation-tactics` (Core Human Conversation)
7. `referral-guidance` (Core Human Conversation)
8. `followup-support` (Core Human Conversation)
9. `marital-conflict-resolution` (Domain Knowledge / Playbook)
10. `parent-child-mediation` (Domain Knowledge / Playbook)
11. `workplace-dispute-resolution` (Domain Knowledge / Playbook)
12. `intergenerational-joint-family` (Domain Knowledge / Playbook - Phase 1)
13. `residential-community-harmony` (Domain Knowledge / Playbook - Phase 1)
14. `civic-dialogue-consensus` (Domain Knowledge / Playbook - Phase 1)
15. `emotional-safety-triage` (Safety & Ethical Boundary)
16. `domestic-violence-safeguard` (Safety & Ethical Boundary)
17. `child-protection-safeguard` (Safety & Ethical Boundary)
18. `suicide-crisis-safeguard` (Safety & Ethical Boundary)

### 2.4 Transport Protocol & Runtime Constraints
- **Transport Type:** FastMCP Streamable HTTP (`text/event-stream` SSE) at `http://127.0.0.1:7860/mcp`.
- **Session ID Constraint:** FastMCP issues an `mcp-session-id` UUID header on the `initialize` handshake. Every subsequent JSON-RPC request (`tools/list`, `tools/call`) **must** provide this header. Failure to provide it yields HTTP 400 with JSON-RPC error `-32600` (`"Bad Request: Missing session ID"`).
- **Lifespan Task Group:** The Starlette application must be wrapped in `async with app.router.lifespan_context(app):` or served via Uvicorn so that FastMCP's `StreamableHTTPSessionManager` initializes its internal `anyio.create_task_group()`.

---

## 3. SECTION 2 — AUDIT OPEN WEBUI (`llm-main`)

### 3.1 Architecture & Files Audited
- `backend/open_webui/main.py`: Main application initialization, lifespan, router mounting.
- `backend/open_webui/routers/mediation.py`: Multi-agent dispute mediation system (`/api/v1/mediation`).
- `backend/open_webui/routers/openai.py`: Chat completion endpoint proxying and streaming.
- `backend/open_webui/utils/middleware.py`: `DiffySkillMiddleware`, tool injection, and prompt formatting.

### 3.2 Finding 1: Mediation Router Is Completely Disconnected from Diffy MCP
- **File:** `backend/open_webui/routers/mediation.py` (lines 46-49, 138-165, 300-340)
- **Current State:** The mediation router defines `MultiAgentMediationEngine` with three personas:
  - `Party A` (Aggrieved party)
  - `Party B` (Defensive party)
  - `SarahCollinsMediator` (NVC clinical mediator)
- **Gap:** The router attempts to load knowledge via `Knowledges.get_knowledge_by_id(db, knowledge_id)` from Open WebUI's local Chroma vector DB. It has **no connection** to Diffy FastMCP tools, `understand_human_problem`, or `route_skills`.
- **Critical Safety Risk:** When a user inputs a domestic violence or severe abuse scenario into `/api/v1/mediation/simulate`, the engine proceeds to simulate rounds where Party A attacks and Party B defends ("you overreacted, my behavior was justified by stress"), followed by Sarah Collins proposing a compromise. In intimate partner violence, joint mediation creates lethal risk and re-victimizes the vulnerable party.

### 3.3 Finding 2: Normal Chat Middleware Relies on Voluntary LLM Tool-Calling
- **File:** `backend/open_webui/utils/middleware.py` (lines 2780-2807, 2892-2908)
- **Current State:** `DiffySkillMiddleware` defines `DEFAULT_SKILLS_USER_PROMPT`:
  ```
  You have access to a specialized skill knowledge base via the following tools:
  - list_skills: Returns a list of all available skill names.
  - get_skill: Fetches the full instruction set and guidelines for a specific skill.
  ```
- **Gaps:**
  1. The prompt does not mention `understand_human_problem` or `route_skills`.
  2. The middleware relies entirely on the LLM's voluntary decision to execute a tool. If the LLM produces a direct text response, **zero problem understanding and zero safety routing occur**.
  3. Lines 2892–2908 hardcode an enum list of only 15 skills:
     ```python
     known_diffy_skills = [
         "active-listening", "empathy-validation", "nonviolent-communication",
         "emotional-safety-triage", "domestic-violence-safeguard",
         "child-protection-safeguard", "suicide-crisis-safeguard",
         "marital-conflict-resolution", "parent-child-mediation",
         "workplace-dispute-resolution", "clarification-framework",
         "de-escalation-tactics", "boundary-setting", "referral-guidance",
         "followup-support"
     ]
     ```
     The 3 new skills added in Phase 1 (`intergenerational-joint-family`, `residential-community-harmony`, `civic-dialogue-consensus`) are omitted from this enum.

### 3.4 Finding 3: User Session & Multi-Turn Context Isolation
- **Authentication:** Open WebUI uses JWT tokens and isolates chats via `user.id` and `chat_id` stored in SQLite/PostgreSQL.
- **Mediation State:** The mediation router does not persist sessions to the database; it generates a transient UUID session and streams turns directly.
- **Context Passing:** Chat history is passed as OpenAI-compatible `messages: [{"role": "user", ...}, {"role": "assistant", ...}]`. If Diffy skills are injected, they are prepended to the system prompt, which preserves multi-turn context correctly.

---

## 4. SECTION 3 — AUDIT PRODUCTSPEAKER (`C:\ProductSpeaker`)

### 4.1 Architecture & Files Audited
- `backend/core/assistant.py`: Central voice assistant orchestration pipeline.
- `backend/api/routes.py`: FastAPI endpoints (`/api/voice/process-audio`, `/api/chat`, `/health/ready`).
- `backend/ai/mcp_client.py`: FastMCP client connecting to Diffy over `StreamableHttpTransport`.
- `backend/ai/gemini_service.py`: Google Gemini 2.5 Flash LLM integration.
- `backend/core/memory.py`: In-memory and SQLite storage for facts and session messages.
- `backend/core/session.py`: Session TTL and active dialogue tracking.
- `backend/voice/speech_to_text.py`: Whisper / Faster-Whisper / Groq STT.
- `backend/voice/text_to_speech.py`: Edge-TTS neural speech synthesis.
- `ESP32_VoiceSpeaker/ESP32_VoiceSpeaker.ino`: ESP32-S3 I2S audio streaming firmware.

### 4.2 Finding 1: ProductSpeaker Discovers Tools but Only Instructs Legacy Calls
- **File:** `backend/core/assistant.py` (lines 328-350)
- **Current Behavior:** `_build_system_instruction` checks `mcp_client.is_connected`. If true, it adds:
  ```
  DIFFY KNOWLEDGE BASE EXTENSION:
  You have live access to specialized communication skills via an MCP server.
  Tools available:
    - list_skills(): Returns all available skill names.
    - get_skill(skill_name): Retrieves the exact instructions and guidelines for that skill.
    - list_skill_files(skill_name): Lists associated reference files.
  ```
- **Gap:** Neither `understand_human_problem` nor `route_skills` is registered in Gemini's system instructions. Gemini only knows about `list_skills` and `get_skill`.

### 4.3 Finding 2: Zero Pre-Generation Problem Understanding in Voice Pipeline
- **File:** `backend/core/assistant.py` (lines 400-475)
- **Current Flow:**
  `ESP32 Audio` -> STT -> `assistant.process_text_input` -> `gemini_service.generate_response` -> TTS -> `ESP32 Speaker`.
- **Gap:** The text input is sent directly to Gemini. Diffy is never called before generation. If Gemini does not proactively trigger tool calling, Diffy is completely bypassed.

### 4.4 Finding 3: Silent Safety Bypass on Diffy MCP Failure
- **File:** `backend/core/assistant.py` (lines 200-240) and `gemini_service.py` (lines 140-165)
- **Current Behavior:** If Diffy MCP is down or times out, `mcp_active` is flagged `False`, and the request proceeds to Gemini without Diffy tools.
- **Safety Risk:** In high-stakes situations (domestic abuse, suicide crisis), an MCP network failure allows Gemini to generate ungrounded, generic, or potentially dangerous advice without any local safety fallback.

### 4.5 Finding 4: Multi-User Isolation Gap on Voice Device
- **File:** `backend/core/memory.py` (lines 40-59, 120-135)
- **Current Behavior:** `SQLiteMemoryStore.store_fact` and `retrieve_context` fall back to `uid = user_id or "default_user"`.
- **Privacy Risk:** Because the ESP32 hardware transmits audio without voice biometrics or per-user credentials, all household members speaking to the smart speaker write to and read from the single `default_user` profile in `sessions.db`. Sensitive disclosures by one person could be recalled in responses to another.

### 4.6 Hardware & Firmware Audit (ESP32-S3)
- **Firmware:** `ESP32_VoiceSpeaker.ino` runs on ESP32-S3 with INMP441 I2S microphone and MAX98357A I2S amplifier DAC.
- **Audio Format:** 16kHz, 16-bit mono PCM.
- **Protocol:** HTTP POST to `/api/voice/process-audio` with header `Accept: audio/wav`. Server synthesizes TTS and streams WAV bytes back with HTTP headers `X-AI-Response`, `X-Prompt`, `X-Session-ID`.
- **Network Resilience:** Firmware implements Wi-Fi auto-reconnect and audio pre-buffering (8KB threshold) before I2S playback to prevent stuttering.

---

## 5. AUDIT SUMMARY MATRIX

| Domain / Dimension | Diffy FastMCP (`diffy-main`) | Open WebUI (`llm-main`) | ProductSpeaker (`ProductSpeaker`) | Unified Target Architecture |
|---|---|---|---|---|
| **Problem Taxonomy** | Configurable `taxonomy.json` (10 domains) | None (ad-hoc NVC prompts) | None (Gemini general prompt) | Diffy MCP Taxonomy as authoritative source |
| **Skill Registry** | 18 skills in `skills_registry.json` | Hardcoded 15-skill enum | Uninstructed discovery | Dynamic registry sync via FastMCP |
| **Problem Understanding** | `understand_human_problem` operational | Unused (bypassed) | Unused (bypassed) | Deterministic pre-generation orchestration |
| **Dynamic Skill Routing** | `route_skills` operational | Unused (bypassed) | Unused (bypassed) | Deterministic pre-generation routing |
| **Safety Precedence** | Immediate lockout on DV/Self-Harm | Joint mediation attempted in DV | Silent bypass on MCP down | Strict safety lockout across text & voice |
| **Multi-Agent Mediation** | Excluded in high-risk scenarios | Unchecked 3-party simulation | N/A (voice assistant mode) | Safety-gated mediation with Diffy grounding |
| **Session & Memory** | Stateless JSON-RPC tool server | PostgreSQL/SQLite per web user | SQLite `default_user` shared | Tenant-isolated session federation |
| **Multilingual Support** | English + Hindi Devanagari regex tested | Model-dependent (Ollama/OpenAI) | Whisper STT + Edge-TTS (hi-IN) | Unified Hindi, English, Hinglish handling |
