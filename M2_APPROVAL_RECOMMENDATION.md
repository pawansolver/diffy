# PHASE 2 — MILESTONE 2 APPROVAL RECOMMENDATION
**Project:** Smart Human Problem Understanding & Dynamic Skill Routing Framework  
**Sign-off Authorities:** Senior Software Architect, Application Security Auditor, QA Lead  
**Target Systems:** `diffy-main`, `llm-main`, `ProductSpeaker`  
**Date:** November 2026  

---

## 1. FORMAL VERDICT

### **VERDICT: APPROVED AFTER REQUIRED FIXES**

Milestone 1 has successfully established the architectural foundation, FastMCP Streamable HTTP bridge, domestic violence screening guards, household memory privacy protections, and backward compatibility across all 18 core human skills.

However, based on rigorous independent code and runtime verification, **three pre-requisite fixes** must be applied immediately upon transitioning into Milestone 2 to guarantee production reliability, future FastMCP library compatibility, and CI/CD test stability.

---

## 2. AUDIT VERIFICATION EVIDENCE SUMMARY

| Verification Domain | Architectural Criteria | Audit Finding | Status |
|---|---|---|---|
| **FastMCP Bridge** | Connection pooling, session reuse, 5 MCP methods | 11.36ms mean latency across 50 calls; session reused; parameter normalization verified (`text` -> `user_input`). | **SATISFIED** |
| **Mediation Safety** | Strict lockout for domestic violence & coercive control | `/resolve` and `/resolve/stream` intercept abuse before LLM processing; returns HTTP 422 with 3 verified Indian helplines. | **SATISFIED** |
| **Household Privacy** | `default_user` isolation and sensitive fact filtering | Blocks anonymous facts without consent; blocks cross-user reads; filters abuse, trauma, depression, and medical disclosures. | **SATISFIED** |
| **Offline Resilience** | Emergency fallback when Diffy is offline | Regex safety screen covers English, Hindi, and Hinglish; fails closed on unexpected errors. | **SATISFIED** |
| **Regression Safety** | Zero disruption to existing features | All 18 skills intact in `diffy-main/skills`; ProductSpeaker voice/hardware tests pass (15/15). | **SATISFIED** |

---

## 3. MANDATORY PRE-M2 REQUIRED FIXES

Before writing new Milestone 2 feature code, the following three fixes must be executed:

### Fix 1: Resolve FastMCP `sse_read_timeout` Deprecation
- **Location:** `diffy-main/mcp_bridge.py`, `ProductSpeaker/backend/ai/mcp_bridge.py`, `llm-main/backend/open_webui/utils/mcp/bridge.py` line 158.
- **Issue:** Using `sse_read_timeout` emits `FastMCPDeprecationWarning` and will break in upcoming FastMCP versions.
- **Action Required:** Change `sse_read_timeout=self.timeout` to `session_kwargs={"read_timeout_seconds": self.timeout}`.

### Fix 2: Harden `FastMCPBridge.call_tool` Against Concurrency Severance
- **Location:** `mcp_bridge.py` (`call_tool` method).
- **Issue:** If an error occurs in one concurrent coroutine and calls `await self.disconnect()`, other in-flight tool calls immediately fail with `ClientNotConnectedError`.
- **Action Required:** Introduce an active in-flight request counter or condition lock so that `disconnect()` gracefully drains or shields in-flight requests rather than aborting active HTTP sessions.

### Fix 3: Standardize Subprocess Execution in `test_08` for Windows CI/CD
- **Location:** `diffy-main/tests/test_m1_verification.py` line 288.
- **Issue:** `asyncio.create_subprocess_exec` fails under Windows Python 3.14 with `[WinError 50] DuplicateHandle`.
- **Action Required:** Replace `asyncio.create_subprocess_exec` with synchronous `subprocess.run(..., capture_output=True, text=True)` executed via `asyncio.to_thread`.

---

## 4. MILESTONE 2 SCOPE & EXECUTION PLAN

With Milestone 1 validated and the above three fixes defined, Milestone 2 will focus on:

### Objective: Dynamic Human Problem Understanding & Full Skill Routing Integration

1. **Open WebUI Chat Pipeline Integration:**
   - Wire `FastMCPBridge` directly into the chat completion flow.
   - For every incoming user message sharing emotional or interpersonal friction, invoke `understand_human_problem` and `route_skills` before synthesizing responses.
   - Inject Tier 1 (Core Conversation), Tier 2 (Domain Skills), Tier 3 (Playbooks), and Tier 4 (Safety) instructions directly into the system prompt context.

2. **ProductSpeaker Voice Loop Integration:**
   - Integrate `route_skills` into `GeminiService` multi-turn tool-calling loop.
   - Enable the ESP32 speaker to respond with grounded human empathy (acknowledging emotion -> identifying unmet need -> offering gentle coexistence wisdom).
   - Enforce voice compaction to keep spoken answers between 1 to 3 calming, natural sentences without robotic bullet points.

3. **Multi-Tier Skill Chaining:**
   - Support composite routing when problems span multiple life domains (e.g., joint-family stress combined with elder care and financial pressure).
   - Ensure safety skills always supersede domain skills.

4. **Interactive Mediation Agendas:**
   - For non-abusive, mutual disagreements, use the routed skills to structure fair, bilateral perspective-taking agendas in `/resolve/stream`.

---

## 5. SIGN-OFF AUTHORIZATION

- **Senior Software Architect:** APPROVED (Subject to M2 Pre-requisite Fixes)
- **Application Security Auditor:** APPROVED (Safety lockouts and memory barriers verified)
- **QA Lead:** APPROVED (Test logic verified; Windows runner workaround documented)

**Final Determination:** Proceed to Milestone 2 implementation, starting with the three required fixes.
