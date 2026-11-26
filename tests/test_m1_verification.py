"""Milestone 1 Verification Test Suite.

Tests:
1. Real Tool Execution over FastMCP Streamable HTTP (understand_human_problem, route_skills, list_skills, get_skill, list_skill_files)
2. 50 Consecutive MCP Requests with connection pooling & latency measurement
3. Multiple Simultaneous Sessions (Concurrency)
4. Session Expiration & Automatic Reconnection
5. Authentication Failures
6. Invalid JSON-RPC Requests
7. MCP Server Unavailable (Emergency local safety screening fallback)
8. Safety Gating in Mediation Router (Domestic Violence Lockout)
9. Household Memory Isolation (No default_user leaks, consent-based storage)
10. Backward Compatibility with existing 18 skills
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import httpx
import pytest

DIFFY_DIR = Path(r"c:\Users\pawan\Downloads\diffy-main\diffy-main")
PRODUCT_SPEAKER_DIR = Path(r"C:\ProductSpeaker")
LLM_MAIN_DIR = Path(r"c:\Users\pawan\Downloads\llm-main\llm-main\backend")

sys.path.insert(0, str(DIFFY_DIR))
sys.path.insert(0, str(PRODUCT_SPEAKER_DIR))
sys.path.insert(0, str(LLM_MAIN_DIR))

os.chdir(str(DIFFY_DIR))

from app import app
from mcp_bridge import FastMCPBridge, _local_safety_fallback_screen
from backend.core.memory import InMemoryStore, SQLiteMemoryStore


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


class RealFastMCPRunner:
    """Manages ASGI lifespan and StreamableHttpTransport bridge for real execution."""

    def __init__(self):
        self.app = app
        self._lifespan_ctx = None

    async def __aenter__(self):
        self._lifespan_ctx = self.app.router.lifespan_context(self.app)
        await self._lifespan_ctx.__aenter__()

        self.bridge = FastMCPBridge(
            base_url="http://testserver/mcp",
            timeout=15.0,
            httpx_client_factory=lambda **kwargs: httpx.AsyncClient(
                transport=httpx.ASGITransport(app=self.app),
                base_url="http://testserver",
                **{k: v for k, v in kwargs.items() if k != "transport"},
            ),
        )
        await self.bridge.connect()
        return self.bridge

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, "bridge"):
            await self.bridge.disconnect()
        if self._lifespan_ctx:
            try:
                await self._lifespan_ctx.__aexit__(exc_type, exc_val, exc_tb)
            except Exception:
                pass


@pytest.mark.asyncio
async def test_01_real_tool_execution_all_five_tools():
    """Verify actual execution of all 5 tools over FastMCP Streamable HTTP."""
    async with RealFastMCPRunner() as bridge:
        # 1. list_skills
        skills = await bridge.list_skills()
        assert len(skills) >= 18, f"Expected at least 18 skills, got {len(skills)}"
        skill_names = [s["name"] for s in skills]
        assert "civic-dialogue-consensus" in skill_names
        assert "intergenerational-joint-family" in skill_names
        assert "residential-community-harmony" in skill_names

        # 2. get_skill
        content = await bridge.get_skill("intergenerational-joint-family")
        assert "intergenerational-joint-family" in content.lower()
        assert len(content) > 100

        # 3. list_skill_files
        files = await bridge.list_skill_files("intergenerational-joint-family")
        assert "SKILL.md" in files

        # 4. understand_human_problem
        analysis = await bridge.understand_human_problem("My husband hit me yesterday and threatened me")
        assert isinstance(analysis, dict)
        assert "understanding" in analysis
        # Risk indicators
        safety = analysis.get("safety", {})
        assert safety.get("potential_risk") is True or "threat_immediate_harm" in str(analysis) or "domestic_violence" in str(analysis)

        # 5. route_skills
        routed = await bridge.route_skills(analysis)
        assert isinstance(routed, dict)
        assert "selected_skills" in routed or "problem_summary" in routed


@pytest.mark.asyncio
async def test_02_fifty_consecutive_mcp_requests_and_latency():
    """Execute 50 consecutive requests to measure latency baseline, connection reuse & error rate."""
    latencies = []
    errors = 0

    async with RealFastMCPRunner() as bridge:
        # Warmup
        await bridge.list_skills()

        for i in range(50):
            t0 = time.perf_counter()
            try:
                if i % 3 == 0:
                    res = await bridge.call_tool("list_skills", {})
                    assert len(res) >= 18
                elif i % 3 == 1:
                    res = await bridge.understand_human_problem(f"Test interpersonal inquiry turn {i}")
                    assert "understanding" in res
                else:
                    res = await bridge.get_skill("civic-dialogue-consensus")
                    assert len(res) > 50
                dt = (time.perf_counter() - t0) * 1000
                latencies.append(dt)
            except Exception as e:
                errors += 1

    assert errors == 0, f"Encountered {errors} errors in 50 consecutive calls"
    assert len(latencies) == 50

    latencies.sort()
    min_lat = latencies[0]
    max_lat = latencies[-1]
    mean_lat = sum(latencies) / len(latencies)
    p50_lat = latencies[25]
    p95_lat = latencies[47]

    print(f"\n--- 50 CONSECUTIVE MCP LATENCY BENCHMARK ---")
    print(f"Min: {min_lat:.2f} ms | Max: {max_lat:.2f} ms | Mean: {mean_lat:.2f} ms")
    print(f"P50: {p50_lat:.2f} ms | P95: {p95_lat:.2f} ms | Error Rate: {errors / 50 * 100:.1f}%")

    assert mean_lat < 100.0, f"Mean latency {mean_lat:.2f}ms too high for connection-pooled calls"


@pytest.mark.asyncio
async def test_03_concurrent_simultaneous_sessions():
    """Verify simultaneous requests execute concurrently at 10, 25 and 50 concurrency tiers without deadlocks or state leakage."""
    async with RealFastMCPRunner() as bridge:
        prompts_base = [
            "I feel lonely in this new city",
            "My teenager screams at me when I ask him to study",
            "Neighbor plays loud music all night long",
            "Boss took credit for my project presentation",
            "Mother-in-law criticizes my cooking every day",
            "Husband and I cannot agree on monthly grocery budget",
            "Colleague is spreading rumors about my promotion",
            "Elderly father refuses to visit the eye doctor",
            "Roommate does not clean dishes in the kitchen sink",
            "Feeling overwhelmed by work and parenting demands",
        ]

        for concurrency in (10, 25, 50):
            prompts = [f"{prompts_base[i % len(prompts_base)]} (tier {concurrency} req {i})" for i in range(concurrency)]

            async def worker(idx: int, p: str):
                res = await bridge.understand_human_problem(p)
                assert "understanding" in res
                return idx, res

            t0 = time.perf_counter()
            tasks = [worker(i, p) for i, p in enumerate(prompts)]
            results = await asyncio.gather(*tasks)
            dt_ms = (time.perf_counter() - t0) * 1000

            assert len(results) == concurrency
            for idx, res in results:
                assert isinstance(res, dict)
                assert res.get("understanding") is not None
            print(f"\n[CONCURRENCY {concurrency}] Completed in {dt_ms:.2f}ms (avg {dt_ms/concurrency:.2f}ms per request)")


@pytest.mark.asyncio
async def test_04_session_expiration_and_automatic_reconnection():
    """Verify that when a session expires or is closed, bridge reconnects transparently."""
    async with RealFastMCPRunner() as bridge:
        # Step 1: Normal call
        res1 = await bridge.call_tool("list_skills", {})
        assert len(res1) >= 18

        # Step 2: Invalidate connection state
        bridge._is_connected = False
        bridge._client = None

        # Step 3: Next call must automatically reconnect and succeed
        res2 = await bridge.call_tool("list_skills", {})
        assert len(res2) >= 18
        assert bridge.is_connected


@pytest.mark.asyncio
async def test_05_authentication_failures():
    """Verify unauthorized calls are rejected when API key is required."""
    os.environ["MCP_API_KEY"] = "super_secret_enterprise_token"
    try:
        bad_bridge = FastMCPBridge(
            base_url="http://testserver/mcp",
            api_key="wrong_invalid_key",
            timeout=5.0,
            httpx_client_factory=lambda **kwargs: httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
                **{k: v for k, v in kwargs.items() if k != "transport"},
            ),
        )
        ok = await bad_bridge.connect()
        assert not ok or not bad_bridge.is_connected
    finally:
        os.environ.pop("MCP_API_KEY", None)


@pytest.mark.asyncio
async def test_06_invalid_jsonrpc_requests_handled_cleanly():
    """Verify invalid tool names or malformed arguments do not crash the bridge."""
    async with RealFastMCPRunner() as bridge:
        # Non-existent tool call
        with pytest.raises(Exception):
            await bridge.call_tool("non_existent_tool_xyz", {"foo": "bar"}, retries=0)

        # Bridge must still be operational for valid calls right after
        skills = await bridge.list_skills()
        assert len(skills) >= 18


@pytest.mark.asyncio
async def test_07_mcp_server_unavailable_emergency_safety_fallback():
    """Verify that when Diffy MCP is offline, safety is NEVER silently bypassed."""
    offline_bridge = FastMCPBridge(base_url="http://127.0.0.1:59999/mcp", timeout=0.5)

    # 1. Domestic violence emergency prompt
    dv_prompt = "My husband hit me yesterday and threatened to kill me if I talk to police."
    analysis_dv = await offline_bridge.understand_human_problem(dv_prompt)
    assert analysis_dv.get("safety_lockout") is True
    assert "domestic_violence" in analysis_dv.get("safety", {}).get("risk_categories", [])

    # 2. Suicide emergency prompt
    suicide_prompt = "I want to kill myself tonight, I have pills ready."
    analysis_suicide = await offline_bridge.understand_human_problem(suicide_prompt)
    assert analysis_suicide.get("safety_lockout") is True
    assert "self_harm" in analysis_suicide.get("safety", {}).get("risk_categories", [])

    # 3. Route skills under fallback
    routing = await offline_bridge.route_skills(analysis_suicide)
    assert routing.get("safety_lockout") is True
    assert routing.get("requires_emergency_protocol") is True


@pytest.mark.asyncio
async def test_08_mediation_router_safety_lockout():
    """Verify Open WebUI mediation router blocks domestic violence scenarios with HTTP 422."""
    import subprocess
    venv_python = r"c:\Users\pawan\Downloads\llm-main\llm-main\backend\venv\Scripts\python.exe"
    script = """
import sys, asyncio, json
sys.path.insert(0, r'c:\\Users\\pawan\\Downloads\\llm-main\\llm-main\\backend')
from open_webui.routers.mediation import MultiAgentMediationEngine
from unittest.mock import MagicMock

async def run():
    engine = MultiAgentMediationEngine(request=MagicMock(), user=MagicMock())
    dv_check = await engine._screen_conflict_safety('My husband beat me with a belt and locked me in the room.')
    safe_check = await engine._screen_conflict_safety('Roommate leaves dirty dishes in the kitchen sink.')
    print(json.dumps({
        'dv_lockout': dv_check.get('safety_lockout'),
        'helplines_count': len(dv_check.get('helplines', [])),
        'safe_lockout': safe_check.get('safety_lockout')
    }))

asyncio.run(run())
"""
    def _run():
        return subprocess.run(
            [venv_python, "-c", script],
            capture_output=True,
            text=True,
            check=False,
        )

    res = await asyncio.to_thread(_run)
    assert res.returncode == 0, f"Process failed: {res.stderr}"
    stdout = res.stdout
    # Extract the JSON line
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            output = json.loads(line)
            assert output["dv_lockout"] is True, "Domestic violence must trigger safety lockout"
            assert output["helplines_count"] >= 2, "Helplines must be provided"
            assert output["safe_lockout"] is False, "Safe dispute must not trigger lockout"
            return
    pytest.fail(f"Could not parse JSON output from mediation check: {stdout}")


@pytest.mark.asyncio
async def test_09_household_memory_isolation_and_consent(tmp_path):
    """Verify smart speaker memory prevents default_user leaks and enforces consent."""
    db_file = tmp_path / "test_memory.db"
    store = SQLiteMemoryStore(str(db_file))

    # Test A: Storing for default_user without consent is rejected
    saved_no_consent = await store.store_fact("favorite_dish", "Biryani", user_id="default_user", consent=False)
    assert saved_no_consent is False

    # Test B: Retrieving context for default_user returns empty list (no leakage across household)
    ctx_default = await store.retrieve_context("food", user_id="default_user")
    assert ctx_default == []

    # Test C: Sensitive mental health / trauma disclosure is never stored
    saved_sensitive = await store.store_fact("health_issue", "Severe clinical depression and suicidal thoughts", user_id="user_alice", consent=True)
    assert saved_sensitive is False

    # Test D: Explicit authenticated user with non-sensitive fact succeeds
    saved_auth = await store.store_fact("preferred_city", "Bangalore", user_id="user_alice", consent=True)
    assert saved_auth is True

    # Test E: Authenticated context retrieves isolated user facts
    ctx_alice = await store.retrieve_context("city", user_id="user_alice")
    assert any("Bangalore" in c for c in ctx_alice)

    # Test F: User Bob cannot see Alice's facts
    ctx_bob = await store.retrieve_context("city", user_id="user_bob")
    assert ctx_bob == []

    store.close()


@pytest.mark.asyncio
async def test_10_backward_compatibility_existing_skills():
    """Verify all 18 skills in the repository are registered and accessible."""
    async with RealFastMCPRunner() as bridge:
        skills = await bridge.list_skills()
        names = {s["name"] for s in skills}

        expected_18 = [
            "adaptive-authoritative-style",
            "child-development-sequence",
            "civic-dialogue-consensus",
            "context-evaluation-framework",
            "dimensional-decision-making",
            "dimensional-loops",
            "dimensional-principle-of-solution-design",
            "dimensional-stability-index",
            "documentation-skill",
            "etar-framework",
            "example-skill",
            "feminine-masculine-dimensional-dynamics",
            "gendered-communication-personalization",
            "intergenerational-joint-family",
            "misapplication-ethics",
            "residential-community-harmony",
            "resilience-scoring-system",
            "vyavastha-typology-feedback-loops",
        ]

        for s_name in expected_18:
            assert s_name in names, f"Skill {s_name} missing from registered catalog"
