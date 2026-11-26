# PHASE 2 — API CONTRACTS & PROTOCOL SPECIFICATIONS
## Smart Human Problem Understanding & Dynamic Skill Routing Framework
**Project Owner:** Pawan Kumar  
**Specification Version:** 2.0.0  
**Transport Standards:** JSON-RPC 2.0 over FastMCP Streamable HTTP (SSE), REST OpenAPI 3.1, WebSocket, I2S PCM Audio

---

## 1. DIFFY FASTMCP PROTOCOL SPECIFICATION

Diffy FastMCP runs as an ASGI application on port 7860 (`http://127.0.0.1:7860/mcp`). It implements the Model Context Protocol (MCP) using Streamable HTTP (`text/event-stream`).

### 1.1 Session Handshake & Lifecycle
1. **Initialize Handshake (`POST /mcp`):**
   - **Request Headers:**
     ```http
     POST /mcp HTTP/1.1
     Host: 127.0.0.1:7860
     Content-Type: application/json
     Accept: text/event-stream, application/json
     ```
   - **Request Body:**
     ```json
     {
       "jsonrpc": "2.0",
       "id": 1,
       "method": "initialize",
       "params": {
         "protocolVersion": "2024-11-05",
         "capabilities": {},
         "clientInfo": {"name": "UnifiedClient", "version": "1.0.0"}
       }
     }
     ```
   - **Response Headers:**
     ```http
     HTTP/1.1 200 OK
     Content-Type: text/event-stream
     mcp-session-id: 7fa32b0e-4361-419b-a01c-6d8b39414e82
     ```
   - **Response Body (SSE Event):**
     ```
     event: message
     data: {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"serverInfo":{"name":"Diffy Knowledge Base","version":"2.0.0"}}}
     ```

2. **Initialized Notification (`POST /mcp`):**
   - **Mandatory Header:** `mcp-session-id: 7fa32b0e-4361-419b-a01c-6d8b39414e82`
   - **Body:**
     ```json
     {
       "jsonrpc": "2.0",
       "method": "notifications/initialized"
     }
     ```

3. **Subsequent Calls (`tools/list`, `tools/call`):**
   - Must include `mcp-session-id` header in all requests. Missing this header returns HTTP 400 (`-32600 "Bad Request: Missing session ID"`).

---

## 2. FASTMCP TOOL SCHEMAS

### 2.1 Tool: `understand_human_problem`
- **Method:** `tools/call`
- **Name:** `understand_human_problem`
- **Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "text": {
        "type": "string",
        "description": "User message describing their interpersonal, emotional, or life situation"
      },
      "conversation_history": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "role": {"type": "string", "enum": ["user", "assistant", "system"]},
            "content": {"type": "string"}
          },
          "required": ["role", "content"]
        },
        "default": [],
        "description": "Previous turns in the dialogue"
      },
      "metadata": {
        "type": "object",
        "additionalProperties": true,
        "default": {},
        "description": "Optional telemetry (e.g. channel: 'voice' | 'text', locale: 'hi-IN')"
      }
    },
    "required": ["text"]
  }
  ```

- **Output Structure (JSON-RPC `result.content[0].text`):**
  ```json
  {
    "domains": ["marriage_and_relationships", "individual_emotional_support"],
    "people_involved": ["spouse_partner"],
    "problem_patterns": ["communication_breakdown", "defensiveness_stonewalling"],
    "emotional_signals": ["frustration_anger", "loneliness_isolation"],
    "user_intention": "seek_perspective",
    "severity_level": "MODERATE",
    "safety_indicators": [],
    "context_factors": ["ongoing_conflict"],
    "clarification_required": false,
    "clarification_questions": [],
    "confidence_score": 0.88
  }
  ```

### 2.2 Tool: `route_skills`
- **Method:** `tools/call`
- **Name:** `route_skills`
- **Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "problem_analysis": {
        "type": "object",
        "description": "Validated dictionary returned from understand_human_problem",
        "properties": {
          "domains": {"type": "array", "items": {"type": "string"}},
          "people_involved": {"type": "array", "items": {"type": "string"}},
          "problem_patterns": {"type": "array", "items": {"type": "string"}},
          "emotional_signals": {"type": "array", "items": {"type": "string"}},
          "user_intention": {"type": "string"},
          "severity_level": {"type": "string"},
          "safety_indicators": {"type": "array", "items": {"type": "string"}},
          "context_factors": {"type": "array", "items": {"type": "string"}},
          "clarification_required": {"type": "boolean"},
          "clarification_questions": {"type": "array", "items": {"type": "string"}},
          "confidence_score": {"type": "number"}
        },
        "required": ["domains", "severity_level", "safety_indicators"]
      },
      "context": {
        "type": "object",
        "default": {},
        "description": "Optional conversational context factors"
      }
    },
    "required": ["problem_analysis"]
  }
  ```

- **Output Structure (JSON-RPC `result.content[0].text`):**
  ```json
  {
    "selected_skills": [
      "active-listening",
      "empathy-validation",
      "marital-conflict-resolution",
      "nonviolent-communication"
    ],
    "core_conversation_skills": [
      "active-listening",
      "empathy-validation"
    ],
    "domain_knowledge_skills": [
      "marital-conflict-resolution"
    ],
    "scenario_playbooks": [
      "nonviolent-communication"
    ],
    "safety_boundary_skills": [],
    "excluded_skills": [],
    "safety_lockout": false,
    "requires_emergency_protocol": false,
    "routing_rationale": "Activated core active listening and marital conflict playbook for moderate relational friction."
  }
  ```

### 2.3 Legacy Knowledge Tools (Preserved for Backward Compatibility)
- `list_skills()` -> `{"skills": [{"name": "...", "description": "...", "category": "..."}]}`
- `get_skill(skill_name: string)` -> `{"name": "...", "content": "# Markdown content...", "files": [...]}`
- `list_skill_files(skill_name: string)` -> `{"files": ["SKILL.md", "references/..."]}`

---

## 3. OPEN WEBUI API CONTRACTS

### 3.1 Chat Completion Endpoint (`/api/v1/chat/completions`)
- **Protocol:** HTTP POST, supports Server-Sent Events (`stream: true`).
- **Headers:**
  - `Authorization: Bearer <JWT_TOKEN>`
  - `Content-Type: application/json`
- **Request Body (OpenAI Standard with Metadata Extension):**
  ```json
  {
    "model": "llama3.1:latest",
    "messages": [
      {"role": "system", "content": "You are a human-centered AI assistant."},
      {"role": "user", "content": "My mother-in-law keeps criticizing my cooking and my husband says nothing."}
    ],
    "stream": true,
    "temperature": 0.7
  }
  ```
- **Middleware Injection Contract:**
  Before passing to the underlying model, `DiffySkillMiddleware` executes `understand_human_problem` and `route_skills`. It prepends the selected skill guidelines to `messages[0]` (system instruction) as structured markdown:
  ```markdown
  ### ACTIVE HUMAN-CENTERED SKILLS:
  - active-listening
  - empathy-validation
  - intergenerational-joint-family
  - boundary-setting

  [SKILL GUIDELINES: intergenerational-joint-family]
  - Acknowledge cultural hierarchy without invalidating individual boundaries.
  - Bridge generational expectations using NVC observations.
  ```

### 3.2 Mediation Simulation Endpoint (`/api/v1/mediation/simulate`)
- **Protocol:** HTTP POST
- **Request Body:**
  ```json
  {
    "conflict_scenario": "Employee complains of arbitrary overtime; manager points to client obligations.",
    "model_id": "llama3.1:latest",
    "rounds": 2,
    "temperature": 0.7
  }
  ```
- **Safety Lockout Response (HTTP 403 Forbidden / 422 Unprocessable):**
  If `understand_human_problem` detects `domestic_violence` or `self_harm`:
  ```json
  {
    "error": "SAFETY_LOCKOUT",
    "detail": "Joint mediation is strictly prohibited in scenarios involving abuse, coercive control, or self-harm.",
    "safety_directive": {
      "safety_lockout": true,
      "requires_emergency_protocol": true,
      "helplines": [
        {"name": "National Domestic Violence Helpline", "number": "1091 / 181"},
        {"name": "Tele-MANAS Mental Health Helpline", "number": "14416"}
      ],
      "recommended_action": "Individual emotional safety planning only."
    }
  }
  ```

---

## 4. PRODUCTSPEAKER API CONTRACTS

### 4.1 Audio Processing Endpoint (`/api/voice/process-audio`)
- **Protocol:** HTTP POST `multipart/form-data`
- **Headers:**
  - `X-Device-API-Key: <DEVICE_SECRET_KEY>`
  - `Accept: audio/wav` (requests binary PCM stream) OR `application/json`
- **Form Data:**
  - `file`: Binary audio file (16kHz WAV or WebM mono)
  - `session_id`: (Optional string) Client conversation UUID
- **Binary Audio Response (ESP32 Mode):**
  - **Status:** HTTP 200 OK
  - **Content-Type:** `audio/wav`
  - **Headers:**
    - `X-Prompt: <Sanitized single-line ASCII transcript of user audio>`
    - `X-AI-Response: <Sanitized single-line ASCII summary of AI answer>`
    - `X-Session-ID: <UUID>`
    - `X-Safety-Lockout: <true|false>`
  - **Body:** Binary WAV audio stream synthesized by Edge-TTS.

- **JSON Response (`AudioProcessResponse`):**
  ```json
  {
    "success": true,
    "prompt": "Mujhe bahut akelepan me ghabrahat ho rahi hai",
    "response": "Aapka akelapan aur ghabrahat bilkul samajh sakti hoon. Main aapke saath hoon, batayein kya mehsoos ho raha hai.",
    "session_id": "9c12a871-6789-4bce-921a-ef0982341234",
    "audio_filename": "tts_a912e78f.wav",
    "generation_id": "gen_81920",
    "latency_ms": 1340.5,
    "metadata": {
      "language_detected": "hi",
      "domains": ["individual_emotional_support"],
      "skills_used": ["empathy-validation", "active-listening"],
      "safety_lockout": false
    }
  }
  ```

### 4.2 Assistant Text Chat Endpoint (`/api/chat`)
- **Protocol:** HTTP POST `application/json`
- **Headers:** `X-Device-API-Key: <KEY>`
- **Request Body (`ChatRequest`):**
  ```json
  {
    "message": "Kal se meri mummy mujhse baat nahi kar rahi hain",
    "session_id": "9c12a871-6789-4bce-921a-ef0982341234",
    "speak": false,
    "language": "hi",
    "model": "gemini-2.5-flash"
  }
  ```
- **Response Body (`ChatResponse`):**
  ```json
  {
    "success": true,
    "prompt": "Kal se meri mummy mujhse baat nahi kar rahi hain",
    "response": "Jab maa baat karna band kar deti hain toh dil par bahut bojh padta hai. Kya aap batana chahenge ki kis baat par naarazgi hui?",
    "session_id": "9c12a871-6789-4bce-921a-ef0982341234",
    "audio_url": null,
    "execution_time": 0.62,
    "generation_id": "gen_81921"
  }
  ```

### 4.3 Readiness Probe (`/health/ready`)
- **Response Body (`HealthResponse`):**
  ```json
  {
    "status": "ready",
    "ready": true,
    "details": {
      "gemini_connected": true,
      "has_api_key": true,
      "mcp_connected": true,
      "mcp_mode": "remote",
      "device_state": "READY",
      "stt_engine": "groq",
      "tts_voice": "hi-IN-SwaraNeural"
    }
  }
  ```
