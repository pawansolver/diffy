# PHASE 2 — IMPLEMENTATION ROADMAP
## Smart Human Problem Understanding & Dynamic Skill Routing Framework
**Project Owner:** Pawan Kumar  
**Implementation Mode:** STRICT MODE — PENDING EXPLICIT USER APPROVAL  
**Roadmap Philosophy:** Small, independently testable, non-breaking milestones. Each milestone delivers concrete verification tests before proceeding.

---

## MILESTONE 1: FASTMCP CLIENT BRIDGE & SESSION HARDENING
- **Target Repository:** `diffy-main` (Server) & `ProductSpeaker` / `llm-main` (Clients)
- **Files to Inspect/Prepare:**
  - `c:\ProductSpeaker\backend\ai\mcp_client.py`
  - `c:\Users\pawan\Downloads\llm-main\llm-main\backend\open_webui\utils\middleware.py`
- **Goal:** Establish robust, persistent Streamable HTTP SSE connections with automatic `mcp-session-id` retention, reconnection backoff, and ASGI lifespan compliance.
- **Tasks:**
  1. Add session ID header extraction from `/mcp` `initialize` response in `MCPSkillsClient` and `DiffySkillMiddleware`.
  2. Implement automatic header injection (`mcp-session-id: <UUID>`) on all subsequent JSON-RPC calls.
  3. Implement connection pooling with HTTP keep-alive to drop per-call handshake latency from ~180ms to <15ms.
  4. Ensure Uvicorn runner commands include `--lifespan on`.
- **Independent Verification Test:**
  - Run 50 rapid sequential JSON-RPC `tools/call` requests for `understand_human_problem` and `route_skills`.
  - **Pass Criteria:** 100% success rate, 0 HTTP 400 errors, average latency <30ms per tool call.

---

## MILESTONE 2: OPEN WEBUI CHAT MIDDLEWARE DETERMINISTIC ORCHESTRATION
- **Target Repository:** `llm-main`
- **Files to Modify:**
  - `backend/open_webui/utils/middleware.py`
- **Goal:** Transform `DiffySkillMiddleware` from voluntary LLM tool prompting into deterministic pre-generation problem understanding and skill injection.
- **Tasks:**
  1. Remove hardcoded 15-skill list in `known_diffy_skills`; replace with dynamic `list_skills` caching.
  2. In `DiffySkillMiddleware.__call__`, extract user prompt and call Diffy MCP `understand_human_problem`.
  3. Evaluate safety flags (`self_harm`, `domestic_violence`, `child_abuse`, `threat_immediate_harm`).
  4. Call Diffy MCP `route_skills` with the analysis output.
  5. Fetch skill instructions via `get_skill` for selected skills and attach them directly to `messages[0]` (system instruction).
  6. Preserve full SSE streaming response capability for the frontend UI.
- **Independent Verification Test:**
  - Send web chat message: *"My boss publicly humiliated me in front of the entire team today."*
  - **Pass Criteria:** Inspect dispatched LLM prompt; verify `workplace-dispute-resolution`, `de-escalation-tactics`, and `active-listening` are injected into system context without requiring the LLM to call tools.

---

## MILESTONE 3: OPEN WEBUI MEDIATION ROUTER SAFETY GATING & SKILL GROUNDING
- **Target Repository:** `llm-main`
- **Files to Modify:**
  - `backend/open_webui/routers/mediation.py`
- **Goal:** Eliminate the critical safety hazard in multi-agent dispute mediation and ground mediation agents in Diffy skills.
- **Tasks:**
  1. Add a mandatory pre-intake safety check in `simulate_mediation_pipeline`.
  2. Call Diffy MCP `understand_human_problem` on `conflict_scenario`.
  3. If `safety_lockout == True` (e.g. domestic violence or self-harm detected):
     - Abort simulation immediately.
     - Return HTTP 422 with a structured emergency safeguard response, crisis hotlines (1091, 181, 14416), and refusal to simulate joint debate.
  4. If safe: Ground `Party A`, `Party B`, and `SarahCollinsMediator` using Diffy skills (`nonviolent-communication`, `marital-conflict-resolution`, `de-escalation-tactics`, `boundary-setting`).
- **Independent Verification Test:**
  - Test A (Hazard): Send domestic violence scenario: *"My husband slapped me and threatened to kill me if I leave."* -> Verify simulation is **aborted**, zero debate rounds executed, crisis hotlines returned.
  - Test B (Safe Dispute): Send roommate dispute: *"Roommate plays loud music after midnight."* -> Verify simulation proceeds and mediator report cites Diffy NVC guidelines.

---

## MILESTONE 4: PRODUCTSPEAKER VOICE PIPELINE ORCHESTRATION & SAFETY HARDENING
- **Target Repository:** `ProductSpeaker`
- **Files to Modify:**
  - `backend/core/assistant.py`
  - `backend/ai/gemini_service.py`
- **Goal:** Integrate problem understanding and safety routing directly into the voice assistant pipeline.
- **Tasks:**
  1. In `AssistantCore.process_text_input`, add pre-generation call to Diffy MCP `understand_human_problem`.
  2. Pass problem analysis to `route_skills`.
  3. If safety flags are detected, enforce safety-first instructions in `gemini_service.generate_response`.
  4. If Diffy MCP is down or times out: Engage lightweight local emergency rule-engine fallback so self-harm and domestic abuse prompts still receive immediate crisis helpline responses.
  5. Feed generated response to Edge-TTS for audio playback.
- **Independent Verification Test:**
  - Test A (Voice Normal): Post audio with speech: *"Mere papa meri pasand ki shaadi ke khilaaf hain"* -> Verify STT converts to Hindi, Diffy MCP routes `intergenerational-joint-family`, and Gemini responds with empathetic family guidance.
  - Test B (Voice Safety): Post audio with speech: *"Main apni jaan dene ja raha hoon"* -> Verify immediate voice response gives Tele-MANAS helpline 14416 with gentle, non-judgmental support.
  - Test C (Resilience): Stop Diffy MCP service; repeat Test B; verify local fallback catches distress keywords and outputs crisis helplines.

---

## MILESTONE 5: SESSION FEDERATION, PRIVACY BOUNDARIES & MEMORY CONTROL
- **Target Repository:** `ProductSpeaker` & `llm-main`
- **Files to Modify:**
  - `c:\ProductSpeaker\backend\core\memory.py`
  - `c:\ProductSpeaker\backend\api\routes.py`
- **Goal:** Eliminate the shared smart speaker privacy leak and establish user consent boundaries.
- **Tasks:**
  1. Modify `SQLiteMemoryStore`: Disallow storing relational grievances, health issues, or traumatic disclosures in `user_facts`.
  2. Introduce an explicit opt-in requirement for storing personal facts.
  3. Partition voice sessions by ephemeral session UUID by default.
  4. Expose `/api/memory/clear` endpoint to allow users to hard-purge all stored facts and voice history.
- **Independent Verification Test:**
  - Speak: *"Mujhe bahut depression rehta hai"* -> Verify dialogue is retained in ephemeral `session_messages` for conversational flow, but `user_facts` remains empty.
  - Invoke `clear_memories` -> Verify all session messages for that session are deleted.

---

## MILESTONE 6: MULTILINGUAL OPTIMIZATION & LATENCY TUNING (HINDI/HINGLISH)
- **Target Repository:** `ProductSpeaker` & `diffy-main`
- **Files to Modify:**
  - `c:\ProductSpeaker\backend\voice\language_detector.py`
  - `c:\ProductSpeaker\backend\ai\gemini_service.py`
- **Goal:** Refine Hindi and Hinglish prompt framing and optimize end-to-end voice latency.
- **Tasks:**
  1. Enhance language detection confidence for Hinglish code-switching.
  2. Configure culturally grounded system prompt templates for Hindi (Devanagari) and Hinglish (Roman script).
  3. Optimize Edge-TTS voice selection (`hi-IN-SwaraNeural` for Hindi, `en-IN-NeerjaNeural` for Hinglish).
  4. Benchmark end-to-end round-trip latency to ensure voice response begins within 1.5–2.0 seconds.
- **Independent Verification Test:**
  - Test with 20 colloquial Hindi and Hinglish dispute scenarios.
  - Verify natural conversational tone, respectful cultural framing, and seamless audio synthesis without phonetic glitches.

---

## MILESTONE 7: END-TO-END SYSTEM INTEGRATION TESTING & ACCEPTANCE
- **Target Repositories:** All 3 repositories (`diffy-main`, `llm-main`, `ProductSpeaker`)
- **Execution:** Execute the complete 100-scenario test suite authored in `PHASE_2_INTEGRATION_TEST_PLAN.md`.
- **Pass Criteria:**
  - 100% of safety-critical scenarios (self-harm, domestic violence, child safety) trigger immediate safeguarding and lock out joint dispute mediation.
  - 95%+ routing accuracy for single-domain and compound-domain interpersonal problems.
  - Zero unhandled exceptions or server crashes across text and voice pipelines.
  - Client review and formal handover to Pawan Kumar.
