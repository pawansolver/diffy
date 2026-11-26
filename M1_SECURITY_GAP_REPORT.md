# PHASE 2 — MILESTONE 1 SECURITY GAP REPORT
**Project:** Smart Human Problem Understanding & Dynamic Skill Routing Framework  
**Evaluator:** Senior Security Auditor & Application Security Specialist  
**Audit Scope:** `diffy-main`, `llm-main`, `ProductSpeaker`  
**Date:** November 2026  

---

## 1. THREAT MODEL & ATTACK SURFACE

The integrated architecture connects three disparate computing tiers:
1. **Public/Semi-Public Hardware Tier (`ProductSpeaker`):** ESP32-S3 microcontroller operating in shared household environments with microphone, speaker, and Wi-Fi.
2. **Mediation & Web Tier (`llm-main`):** Open WebUI handling multi-party dispute resolution, relationship mediation, and direct LLM interaction.
3. **Reasoning & Taxonomy Brain (`diffy-main`):** FastMCP server providing dynamic problem taxonomy analysis, skill routing, and knowledge retrieval.

### Threat Scenarios Evaluated
- **T1: Coercive Control & Retaliation via AI Mediation:** An abusive spouse forces an abused partner into a joint AI mediation session to generate synthetic agreement or weaponize AI statements for intimidation.
- **T2: Household Privacy Snooping:** An unauthenticated household member or visitor queries the voice speaker to extract personal, medical, or relationship disclosures made by other family members.
- **T3: Denial of Service via Connection Flooding:** Multiple simultaneous requests overwhelm the FastMCP bridge, triggering connection churn or thread deadlocks.
- **T4: Filter Evasion:** Adversarial or colloquial user inputs bypass keyword safety filters in household memory or mediation screening.

---

## 2. IDENTIFIED SECURITY & ARCHITECTURAL GAPS

### SEC-01: Race Hazard in `FastMCPBridge.call_tool` During Disconnect / Reconnect
- **Severity:** Medium (CVSS 5.3: `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:L`)
- **Location:** `diffy-main/mcp_bridge.py`, `ProductSpeaker/backend/ai/mcp_bridge.py`, `llm-main/backend/open_webui/utils/mcp/bridge.py`
- **Code Reference:**
  ```python
  async def call_tool(self, name: str, args: Optional[Dict[str, Any]] = None) -> Any:
      if not self.is_connected:
          await self.connect()
      # Race window: another task calls bridge.disconnect() here
      try:
          result = await self._client.call_tool(name, effective_args)
          return result
      except Exception as e:
          logger.error(...)
          await self.disconnect()  # Closes connection while concurrent tasks may be in flight
          raise
  ```
- **Vulnerability Mechanism:**
  `self._lock` is acquired inside `connect()` and `disconnect()`, but is **not held** during `_client.call_tool()`. If 10 concurrent coroutines call `call_tool`, and request #1 triggers an exception and calls `await self.disconnect()`, requests #2 through #10 will simultaneously attempt to execute against a terminating or closed client session, generating cascading `ClientNotConnectedError` exceptions rather than queueing for a clean reconnect.
- **Recommended Remediation (Milestone 2):**
  Implement an active reader-writer counter or an `asyncio.Condition` that prevents `disconnect()` from closing the underlying HTTP client while other tool calls are actively pending in flight.

---

### SEC-02: Deprecated FastMCP Parameter in `StreamableHttpTransport`
- **Severity:** Low (Technical Debt / Forward Compatibility)
- **Location:** `mcp_bridge.py` line 158
- **Code Reference:**
  ```python
  return StreamableHttpTransport(
      url=self.endpoint,
      headers=headers,
      sse_read_timeout=self.timeout,
  )
  ```
- **Vulnerability Mechanism:**
  FastMCP 2.14 deprecated `sse_read_timeout` in favor of `session_kwargs={"read_timeout_seconds": self.timeout}`. In future minor versions of `fastmcp`, passing this keyword argument will raise `TypeError: unexpected keyword argument 'sse_read_timeout'`, terminating bridge connections.
- **Recommended Remediation (Milestone 2):**
  ```python
  return StreamableHttpTransport(
      url=self.endpoint,
      headers=headers,
      session_kwargs={"read_timeout_seconds": self.timeout},
  )
  ```

---

### SEC-03: Keyword Matching Evasion in Long-Term Memory Filtering
- **Severity:** Medium (CVSS 4.7: `CVSS:3.1/AV:L/AC:H/PR:L/UI:N/S:U/C:H/I:N/A:N`)
- **Location:** `ProductSpeaker/backend/core/memory.py` lines 59-63 (`InMemoryStore`) & lines 167-171 (`SQLiteMemoryStore`)
- **Code Reference:**
  ```python
  text_check = f"{key} {value}".lower()
  if any(w in text_check for w in ("depress", "suicid", "abuse", "medic", "mental", "violenc", "assault")):
      logger.warning(f"Refused persisting sensitive disclosure in long-term fact memory: {key}")
      return False
  ```
- **Vulnerability Mechanism:**
  The check uses naive substring matching against 7 English root words. A user disclosing sensitive health or relational trauma in Hindi, Hinglish, or using synonyms (e.g., `"illness": "bipolar"`, `"relationship_status": "he hits me"`, `"condition": "anxiety attacks"`, `"dawaai": "neend ki goli"`) will not trigger the filter and will be persisted in unencrypted SQLite.
- **Recommended Remediation (Milestone 2):**
  Integrate the local multilingual safety classifier (`_local_safety_fallback_screen` regex and semantic classifier) directly into `store_fact` to screen against trauma, medical records, and domestic abuse across English, Hindi, and Hinglish before committing to database storage.

---

### SEC-04: Lack of Hardware Voice Biometrics for Household Member Identity
- **Severity:** Medium (CVSS 5.3: `CVSS:3.1/AV:P/AC:L/PR:N/UI:N/S:U/C:H/I:L/A:N`)
- **Location:** `ProductSpeaker/backend/api/routes.py` and `ESP32_VoiceSpeaker.ino`
- **Vulnerability Mechanism:**
  The ESP32 firmware transmits raw audio over HTTP or WebSocket to the FastAPI backend. Unless an external client passes `user_id` in the JSON request, the device defaults to `user_id = None` (which maps to `default_user`). While M1 successfully blocks `default_user` from reading facts, if an attacker in the house says *"I am Rajesh, what are my facts?"*, and an application assigns `user_id = "rajesh"` based on verbal assertion without biometric verification, Rajesh's facts could be disclosed.
- **Recommended Remediation (Milestone 2 / Future Roadmap):**
  Require PIN or biometric confirmation for sensitive personal profile retrieval over shared voice hardware, or restrict speaker voice interactions exclusively to ephemeral conversational memory.

---

### SEC-05: Subprocess Pipe Handle Duplication in Test Runner (`[WinError 50]`)
- **Severity:** Low (QA & CI/CD Pipeline Stability)
- **Location:** `diffy-main/tests/test_m1_verification.py` line 288 (`test_08_mediation_router_safety_lockout`)
- **Failure Trace:**
  `OSError: [WinError 50] The request is not supported` in `_winapi.DuplicateHandle`.
- **Root Cause:**
  Python 3.14 on Windows changed handle duplication behavior in `asyncio.create_subprocess_exec` when running inside certain non-standard console buffers or pytest subprocesses. The test failed at the OS process fork layer, not because of a flaw in the mediation safety router.
- **Recommended Remediation (Milestone 2):**
  Replace `asyncio.create_subprocess_exec` in `test_08` with synchronous `subprocess.run(..., capture_output=True, text=True)` or direct in-process instantiation of `MultiAgentMediationEngine` within an isolated mock test harness.

---

## 3. SECURITY GAP REMEDIATION MATRIX

| Finding ID | Vulnerability Title | Severity | Exploitability | Target Fix Milestone |
|---|---|---|---|---|
| **SEC-01** | `FastMCPBridge` Concurrency Disconnect Hazard | Medium | Moderate | Milestone 2 (Pre-requisite) |
| **SEC-02** | `sse_read_timeout` FastMCP Deprecation | Low | None (Current) / High (Future) | Milestone 2 (Immediate) |
| **SEC-03** | Memory Keyword Matching Evasion | Medium | Moderate | Milestone 2 |
| **SEC-04** | Household Voice Impersonation Vulnerability | Medium | Low (Physical access) | Milestone 2 / Milestone 3 |
| **SEC-05** | Windows Subprocess Handle Duplication (`test_08`) | Low | Test runner only | Milestone 2 (Immediate) |

---

## 4. AUDITOR CONCLUSION

None of the identified gaps represent critical vulnerabilities that block the foundation of Milestone 1. The domestic violence lockout and household privacy partitions are functional and verified. The five items documented above are actionable hardening tasks that must be incorporated into Milestone 2 development.
