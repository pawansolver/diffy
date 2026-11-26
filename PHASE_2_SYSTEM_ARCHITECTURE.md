# PHASE 2 — UNIFIED SYSTEM ARCHITECTURE
## Smart Human Problem Understanding & Dynamic Skill Routing Framework
**Project Owner:** Pawan Kumar  
**Architecture Version:** 2.0.0  
**Target Platform:** Unified Human-Centered AI Platform (Diffy MCP + Open WebUI + ProductSpeaker)

---

## 1. ARCHITECTURAL VISION & OBJECTIVES

The objective of the unified architecture is to bring three independent components into a coherent, resilient, and human-centered AI platform:

1. **Diffy FastMCP (`diffy-main`):** The cognitive brain providing taxonomy-based problem understanding, dynamic skill routing, and authoritative safety directives.
2. **Open WebUI (`llm-main`):** The web user interface, multi-agent mediation orchestrator, and multi-user chat workspace.
3. **ProductSpeaker (`ProductSpeaker`):** The voice interface powering ESP32-S3 hardware smart speakers with real-time speech-to-text, neural text-to-speech, and Gemini LLM.

### Fundamental Architectural Rules
1. **Single Cognitive Core:** There is only **one** problem-understanding engine and **one** skill router in the platform: Diffy FastMCP. Text and voice interfaces do not implement separate classifiers.
2. **Deterministic Pre-Generation Orchestration:** Problem understanding and safety evaluation occur **before** the generative LLM produces any output. Safety cannot depend on voluntary LLM tool-calling.
3. **Safety Super-Precedence:** If domestic violence, self-harm, child abuse, or immediate threats are detected, the system immediately locks out conflict mediation and activates protective safeguarding protocols across all modalities.
4. **Multilingual & Compound Extensibility:** The architecture handles complex, multi-domain human problems in English, Hindi, and Hinglish.

---

## 2. END-TO-END UNIFIED REQUEST FLOW

```
+---------------------------------------------------------------------------------------------------------+
|                                           INGESTION LAYER                                               |
|                                                                                                         |
|   [ Open WebUI Client (Browser) ]                          [ ESP32-S3 ProductSpeaker (Hardware) ]       |
|          |                                                               |                              |
|          | HTTP POST /api/v1/chat/completions                            | HTTP POST /api/voice/process |
|          |                                                               v                              |
|          |                                                 [ STT Engine (Whisper/Groq) ]                |
|          |                                                               |                              |
|          v                                                               v                              |
|   [ Open WebUI Chat Pipeline ]                             [ Voice Assistant Core Pipeline ]            |
+---------------------------------------------------------------------------------------------------------+
                                                   |
                                                   v
+---------------------------------------------------------------------------------------------------------+
|                                COMMON CONVERSATION ORCHESTRATOR                                         |
|                                                                                                         |
|   1. Extract Clean User Prompt & Session History (Sanitized, Language Tagged)                           |
|   2. Call Diffy MCP `understand_human_problem(text, history, metadata)`                                 |
|                                                  |                                                      |
|                                                  v                                                      |
|   3. SAFETY-FIRST EVALUATION GATE:                                                                      |
|      - Is Severity HIGH / CRITICAL?                                                                     |
|      - Are Safety Indicators present (DV, suicide, abuse, violence)?                                    |
|      |                                                                                                  |
|      +---[ YES: EMERGENCY / SAFEGUARD DIRECTIVE ]                                                       |
|      |    * Lock out mediation mode immediately.                                                        |
|      |    * Suppress compromise / de-escalation / dispute skills.                                       |
|      |    * Inject crisis hotlines & protective safety boundary skills.                                 |
|      |                                                                                                  |
|      +---[ NO: DYNAMIC SKILL ROUTING ]                                                                  |
|           * Call Diffy MCP `route_skills(problem_analysis, context)`                                    |
|           * Retrieve selected skills (Core + Domain + Playbooks + Boundaries).                          |
|                                                  |                                                      |
|                                                  v                                                      |
|   4. GROUNDED CONTEXT ASSEMBLY:                                                                         |
|      - Fetch instruction Markdown for selected skills via `get_skill`.                                  |
|      - Synthesize Human-Centered Prompt (Active Listening, NVC, Playbook guidance).                     |
|      - Attach to System Instructions or Pre-prompt buffer.                                              |
+---------------------------------------------------------------------------------------------------------+
                                                   |
                                                   v
+---------------------------------------------------------------------------------------------------------+
|                                    LLM GENERATION LAYER                                                 |
|                                                                                                         |
|   [ Open WebUI Model Dispatcher ]                          [ Google Gemini 2.5 Flash / Groq LLM ]       |
|   (Ollama / vLLM / OpenAI / Anthropic)                                                                  |
|          |                                                               |                              |
|          v                                                               v                              |
|   SSE Streaming Response                                   Synthesized Response Text                    |
|          |                                                               |                              |
|          v                                                               v                              |
|   Render in Browser UI                                     [ Neural TTS Engine (Edge-TTS) ]             |
|   (Markdown, Cards, Citations)                                           |                              |
|                                                                          v                              |
|                                                            Stream WAV PCM over HTTP / I2S               |
|                                                                          |                              |
|                                                                          v                              |
|                                                            [ ESP32-S3 I2S Speaker Output ]              |
+---------------------------------------------------------------------------------------------------------+
```

---

## 3. SUBSYSTEM RESPONSIBILITIES & BOUNDARIES

### 3.1 Diffy FastMCP (`diffy-main`)
- **Role:** Central Knowledge & Cognitive Intelligence Service.
- **Port / Transport:** ASGI Streamable HTTP (`text/event-stream` SSE) on `http://127.0.0.1:7860/mcp`.
- **Tools Provided:**
  - `understand_human_problem(text, conversation_history, metadata)` -> Evaluates taxonomy dimensions, emotional signals, intention, and safety risks.
  - `route_skills(problem_analysis, context)` -> Determines which skills to activate, which to exclude, and sets safety lockout flags.
  - `list_skills()` -> Returns full catalog of registered skills with metadata.
  - `get_skill(skill_name)` -> Returns complete instruction Markdown and behavioral constraints.
  - `list_skill_files(skill_name)` -> Returns reference playbooks and documentation assets.

### 3.2 Open WebUI (`llm-main`)
- **Role:** Web Chat Platform, Multi-User Session Management, Multi-Agent Mediation Workspace.
- **Components:**
  - **`DiffySkillMiddleware`:** Intercepts incoming user chat requests in `backend/open_webui/utils/middleware.py`. Calls Diffy MCP deterministically, injects required skills, and excludes ungrounded responses.
  - **Mediation Router (`routers/mediation.py`):** Multi-agent simulation workspace. Gated strictly by Diffy's safety triage. If safe, grounds `PartyAAgent`, `PartyBAgent`, and `SarahCollinsMediator` in Diffy's Nonviolent Communication and conflict resolution skills.

### 3.3 ProductSpeaker (`ProductSpeaker`)
- **Role:** Voice Assistant Hardware, Edge Audio Ingestion, Real-Time Audio Streaming.
- **Components:**
  - **FastAPI Core (`backend/core/assistant.py`):** Coordinates STT -> Orchestrator -> Gemini -> TTS.
  - **`MCPSkillsClient` (`backend/ai/mcp_client.py`):** Maintains persistent Streamable HTTP SSE session with Diffy FastMCP.
  - **`GeminiService` (`backend/ai/gemini_service.py`):** Executes LLM generation with Diffy-grounded system prompts.
  - **`SQLiteMemoryStore` (`backend/core/memory.py`):** Persistent multi-turn dialogue history and user consent facts.
  - **ESP32-S3 Firmware:** Streams 16kHz WAV audio over Wi-Fi and drives I2S speaker with pre-buffering.

---

## 4. SAFETY-FIRST GATING ARCHITECTURE

Safety is not an optional feature or an advisory score; it is a **hard gate**:

```
                       [ Incoming User Utterance ]
                                    |
                                    v
                     Diffy MCP `understand_human_problem`
                                    |
                                    v
                       [ Safety Triage Evaluation ]
                                    |
      +-----------------------------+-----------------------------+
      |                                                           |
 [ Flags: `self_harm`, `domestic_violence`,                 [ Flags: Clean / Low ]
   `child_abuse`, `threat_immediate_harm` ]                       |
      |                                                           v
      v                                                Diffy MCP `route_skills`
 [ Safety Lockout Triggered ]                                     |
      - Set `safety_lockout = True`                               v
      - Set `requires_emergency_protocol = True`       Normal Multi-Domain Assembly
      - Suppress all dispute/mediation skills          (Active Listening, Marital,
      - Select ONLY Safeguard Skills                   Parenting, Workplace, etc.)
        (`suicide-crisis-safeguard`,                              |
         `domestic-violence-safeguard`,                           v
         `emotional-safety-triage`,                    Standard LLM Generation
         `referral-guidance`)
      |
      v
 [ Emergency Protective Response Generated ]
   - Validate emotional pain without judgment.
   - Immediate crisis helpline numbers (KIRAN, 1091, 1098).
   - Practical, discreet safety planning.
   - ZERO provocation, compromise, or dispute debate.
```

---

## 5. MULTI-DOMAIN & COMPOUND PROBLEM ARCHITECTURE

Real human crises rarely fit into a single textbook bucket. For example:
> *"I lost my job last month, my wife is constantly yelling at me about money, and yesterday I felt like ending it all."*

### Compound Problem Breakdown:
1. **Life Domains Identified:** `financial_and_social_pressure`, `workplace_relationships`, `marriage_and_relationships`, `individual_emotional_support`.
2. **Emotional Signals:** `shame_worthlessness`, `hopelessness_despair`, `anxiety_dread`.
3. **Safety Risk:** `CRITICAL` (Indicator: `self_harm`).
4. **Routing Strategy:**
   - **Emergency Rule:** Self-harm signal triggers immediate lockout of marital blame and financial advice.
   - **Primary Skill:** `suicide-crisis-safeguard` + `emotional-safety-triage`.
   - **Secondary Grounding:** `active-listening` + `empathy-validation`.
   - **Suppressed:** `marital-conflict-resolution` (must not debate marital grievances while user is in active suicidal ideation).

When safety risk is LOW (e.g., job stress causing arguments with an elder parent), the router merges multiple relevant playbooks:
- `workplace-dispute-resolution` + `intergenerational-joint-family` + `nonviolent-communication`.

---

## 6. STREAMING & VOICE LATENCY ARCHITECTURE

In voice systems, end-to-end latency directly impacts user perception. The architecture optimizes the round-trip pipeline:

| Phase | Target Latency (Voice) | Optimization Mechanism |
|---|---|---|
| **Audio Ingestion (ESP32)** | ~100–250 ms | 16kHz mono streaming, HTTP chunked transfer. |
| **Speech-to-Text (STT)** | ~300–600 ms | Groq Cloud Whisper / Local Faster-Whisper with VAD segmentation. |
| **Diffy Problem Understanding** | ~40–80 ms | In-memory taxonomy matching, compiled regex, persistent HTTP session. |
| **Diffy Skill Routing** | ~10–25 ms | Pre-indexed in-memory skill registry. |
| **LLM Generation (TTFT)** | ~400–700 ms | Gemini 2.5 Flash / Groq LLaMA 3.3 70B with prompt caching. |
| **Neural TTS (Edge-TTS)** | ~250–500 ms | Streaming audio chunk synthesis, chunked HTTP transfer to ESP32. |
| **Audio Pre-Buffering** | ~100 ms | ESP32 8KB ring buffer before I2S DAC output. |
| **Total Voice Round-Trip** | **~1.2 – 2.2 seconds** | Fully acceptable for conversational smart speaker dialogue. |

---

## 7. SHARED CONVERSATION & MEMORY TOPOLOGY

```
+-----------------------------------------------------------------------------------------+
|                               CONVERSATION REPOSITORIES                                 |
|                                                                                         |
|   [ Open WebUI Database ]                                  [ ProductSpeaker SQLite ]    |
|   - Engine: PostgreSQL / SQLite                            - File: `sessions.db`        |
|   - Identity: `user.id` (JWT Authenticated)                - Identity: `device_id` +    |
|   - Chat Entity: `chat_id` (UUID Thread)                     `session_id` + `voice_id`  |
|   - Consent Facts: User Profile KV Store                   - Consent Facts: `user_facts`|
+-----------------------------------------------------------------------------------------+
                                             |
                                             v
+-----------------------------------------------------------------------------------------+
|                               SESSION SYNCHRONIZATION BUS                               |
|                                                                                         |
|   - Device Pairing: Web UI account pairs with ESP32 Device UUID via QR / 6-digit code.  |
|   - Partitioned Memories: Facts stored on ProductSpeaker require explicit user consent. |
|   - Multi-User Voice Tagging: Requests carry `X-Device-ID` and optional `X-Voice-ID`.   |
|   - Deletion Compliance: `clear_memories` purges data across both web and voice stores.  |
+-----------------------------------------------------------------------------------------+
```
