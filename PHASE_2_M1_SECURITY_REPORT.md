# PHASE 2 — MILESTONE 1 SECURITY & ETHICS REPORT
## Immediate Safety Corrections, Privacy Isolation & Resilient Protection
**Project Owner:** Pawan Kumar  
**Audit Dimension:** Clinical AI Ethics, Physical Safety, Household Privacy, Fail-Closed Resiliency  
**Date:** November 2026  

---

## 1. DOMESTIC VIOLENCE & COERCIVE CONTROL LOCKOUT

### 1.1 Clinical & Legal Standards Applied
Standard X of the *Model Standards of Practice for Family and Divorce Mediation* mandates that a mediator must not conduct mediation when domestic abuse makes it unsafe or inappropriate for a participant. 

In interpersonal domestic violence and coercive control:
- A joint dispute simulation forces the victim into a debate where their physical and emotional trauma is framed as an interpersonal disagreement to be compromised.
- Simulated turns by the abuser provide digital validation of gaslighting, victim-blaming, and coercive intimidation.
- Retaliation risk: Victims in shared households face acute physical danger if abusive partners discover joint mediation logs.

### 1.2 Technical Safeguards Implemented
In `backend/open_webui/routers/mediation.py`:
- **Pre-Execution Interceptor:** Every conflict scenario submitted to `/resolve` or `/resolve/stream` is evaluated by `_screen_conflict_safety` before any persona is instantiated or any LLM inference begins.
- **Lockout Directive:** When physical battery, intimidation, or coercive control is flagged:
  - Dialogue simulation is completely aborted.
  - Zero turns are generated for `Party A` or `Party B`.
  - HTTP 422 Unprocessable Entity is raised with structured payload:
    ```json
    {
      "error": "SAFETY_LOCKOUT",
      "message": "Joint dispute mediation is strictly prohibited in scenarios involving domestic violence, coercive control, abuse, or self-harm.",
      "safety_indicators": ["domestic_violence"],
      "helplines": [
        {"name": "National Domestic Violence Helpline", "number": "1091 / 181"},
        {"name": "Tele-MANAS Mental Health Helpline", "number": "14416"},
        {"name": "Childline Emergency Helpline", "number": "1098"}
      ],
      "guidance": "Joint dispute mediation is strictly prohibited in scenarios involving abuse, coercive control, or physical endangerment."
    }
    ```
  - In Server-Sent Events (`/resolve/stream`), a dedicated `safety_lockout` event is yielded and the stream terminates immediately.

---

## 2. SMART SPEAKER HOUSEHOLD PRIVACY ISOLATION

### 2.1 The Shared Device Vulnerability
In voice-activated smart speakers (ESP32-S3), multiple household members speak into a single physical microphone. Without individual voice biometrics or tenant partitioning, storing user facts under an unauthenticated `default_user` profile risks severe data leakage (e.g. User A discloses a health condition or marital crisis, which is subsequently recalled in answers to User B).

### 2.2 Technical Safeguards Implemented
In `backend/core/memory.py` (`SQLiteMemoryStore` and `InMemoryStore`):
1. **Unauthenticated Storage Guard:**
   - Storing facts for `user_id == "default_user"` (or missing `user_id`) without `consent=True` is strictly rejected:
     ```python
     if not user_id or user_id == "default_user":
         if not consent:
             logger.warning("Refused storing unauthenticated fact for default_user without explicit consent.")
             return False
     ```
2. **Context Retrieval Air-Gap:**
   - `retrieve_context` for `default_user` returns `[]`. Unauthenticated turns cannot retrieve previously stored household facts.
3. **Sensitive Disclosure Blacklist:**
   - Even if explicit consent is passed, facts containing mental health, medication, suicidal ideation, or abuse keywords (`depress`, `suicid`, `abuse`, `medic`, `mental`, `violenc`, `assault`) are blocked from permanent fact storage, keeping sensitive personal disclosures strictly ephemeral to the active session.

---

## 3. OFFLINE SAFETY RESILIENCY: NO SILENT BYPASS

### 3.1 The Fail-Closed Standard
A critical safety flaw identified in prior systems was silent degradation: when an external safety microservice went offline, the system proceeded to generate ungrounded responses.

### 3.2 Technical Safeguards Implemented
In `mcp_bridge.py`:
- `_local_safety_fallback_screen()`: Implements an in-memory, deterministic regex engine covering English, Hindi (Devanagari), and Hinglish (Roman script) distress patterns.
- If Diffy MCP is down, timed out, or raises network exceptions, `understand_human_problem` engages this local screener.
- If suicidal ideation, domestic abuse, or child endangerment is detected while Diffy is offline:
  - `safety_lockout = True` is immediately returned.
  - Emergency protocol is activated.
  - The system provides crisis helpline numbers rather than failing silently or pretending the situation is safe.
- If a complete safety evaluation failure occurs in mediation, the router **fails closed**: it aborts joint simulation with `"Mediation blocked: Unable to verify safety checks. Safety first."`

---

## 4. AUTHENTICATION & TOKEN INTEGRITY
- When `MCP_API_KEY` is configured in Diffy MCP, incoming requests must provide `Authorization: Bearer <token>`.
- `ApiKeyMiddleware` in `diffy-main/main.py` enforces constant-time string comparison (`hmac.compare_digest`) to prevent timing side-channel attacks.
- Verified in automated test `test_05_authentication_failures`: Invalid tokens return HTTP 401 with `WWW-Authenticate: Bearer` and abort request processing immediately.
