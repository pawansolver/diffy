"""End-to-end verification tests for Diffy Agent API, Neon Postgres + pgvector memory, and per-device pairing."""

from __future__ import annotations

import os
import sys
import time
import uuid
from pathlib import Path

import httpx
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv(ROOT_DIR / ".env")

import main as diffy_main
from main import SkillsProviderServer, build_http_app
from app import app as asgi_entry_app
from memory.pg_memory import PostgresMemoryManager


@pytest.mark.asyncio
async def test_neon_pgvector_schema_and_cross_channel_memory():
    """Verify Neon Postgres connection, pgvector search, trauma filter, and app+speaker shared user memory."""
    mem = PostgresMemoryManager()
    assert mem.enabled, "DATABASE_URL must be configured for Neon verification"

    ready = await mem.ensure_schema()
    assert ready is True

    test_uid = f"e2e_user_{uuid.uuid4().hex[:8]}"
    test_dev = f"esp32_test_{uuid.uuid4().hex[:8]}"

    # 1. Device pairing & resolution
    paired = await mem.pair_device(device_id=test_dev, user_id=test_uid, device_name="Test Living Room Speaker")
    assert paired["device_token"].startswith("fluai_dev_")
    resolved = await mem.resolve_device_user(paired["device_token"])
    assert resolved is not None
    assert resolved["user_id"] == test_uid

    # 2. App + Speaker messages share same canonical user_id
    await mem.append_message(f"{test_uid}:app", test_uid, "app", "user", "Mera naam Aarav hai aur mujhe ghar mein shanti chahiye.")
    await mem.append_message(f"{test_uid}:speaker", test_uid, "speaker", "user", "Kal jo baat hui thi uspar aage kya karun?")
    recent = await mem.get_recent_messages(user_id=test_uid, limit=10)
    channels = {m["channel"] for m in recent}
    assert {"app", "speaker"}.issubset(channels)

    # 3. Semantic memory + trauma filter + pgvector retrieval
    ok_safe = await mem.store_fact(test_uid, "preferred_name", "Aarav", category="profile", consent=True)
    ok_trauma = await mem.store_fact(test_uid, "health_note", "severe clinical depression and abuse", category="health", consent=True)
    assert ok_safe is True
    assert ok_trauma is False

    facts = await mem.retrieve_relevant_facts(test_uid, "What is Aarav name?", limit=3)
    assert any(f["fact_key"] == "preferred_name" and f["fact_value"] == "Aarav" for f in facts)
    assert not any(f["fact_key"] == "health_note" for f in facts)

    # 4. Anonymous / default_user isolation
    anon_facts = await mem.retrieve_relevant_facts("default_user", "Aarav", limit=3)
    assert anon_facts == []

    # Cleanup test rows so Neon stays clean
    def _cleanup():
        with mem._connect() as conn:
            with conn.cursor() as cur:
                for tbl in ("messages", "sessions", "facts", "episodes", "user_strategies", "turn_states", "paired_devices"):
                    cur.execute(f"DELETE FROM diffy_agent.{tbl} WHERE user_id = %s;", (test_uid,))
            conn.commit()
    _cleanup()


@pytest.mark.asyncio
async def test_diffy_agent_api_end_to_end():
    """Verify /v1/models, /v1/devices/pair, /v1/chat/completions, mandatory safety lockout, and cache TTL."""
    server = SkillsProviderServer("skills.settings.json")
    app = build_http_app(server)

    test_uid = f"e2e_api_{uuid.uuid4().hex[:8]}"
    test_dev = f"esp32_api_{uuid.uuid4().hex[:8]}"

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=30.0) as client:
        # 1. Health & /v1/models
        h = await client.get("/health")
        assert h.status_code == 200
        assert h.json()["postgres_configured"] is True

        m = await client.get("/v1/models")
        assert m.status_code == 200
        model_ids = [item["id"] for item in m.json()["data"]]
        assert "diffy-agent" in model_ids

        # 2. Pair device via HTTP
        pr = await client.post("/v1/devices/pair", json={"device_id": test_dev, "user_id": test_uid, "device_name": "Kitchen Speaker"})
        assert pr.status_code == 200
        dev_token = pr.json()["device_token"]

        # 3. Chat completion from Open WebUI App channel (canonical X-OpenWebUI-User-Id)
        app_resp = await client.post(
            "/v1/chat/completions",
            headers={"X-OpenWebUI-User-Id": test_uid, "X-OpenWebUI-Chat-Id": f"{test_uid}:chat1"},
            json={
                "model": "diffy-agent",
                "messages": [{"role": "user", "content": "Mera naam Rohan hai aur mere papa aur bete mein argument ho gaya hai."}],
            },
        )
        assert app_resp.status_code == 200
        app_data = app_resp.json()
        assert app_data["diffy_meta"]["user_id"] == test_uid
        assert app_data["diffy_meta"]["channel"] == "app"
        assert app_data["diffy_meta"]["safety_lockout"] is False
        assert len(app_data["choices"][0]["message"]["content"]) > 10

        # 4. Follow-up from Paired Speaker channel (uses X-Device-Token -> resolves same test_uid!)
        spk_resp = await client.post(
            "/v1/chat/completions",
            headers={"X-Device-Token": dev_token},
            json={
                "model": "diffy-agent",
                "messages": [{"role": "user", "content": "Main unse pyaar se kaise baat shuru karun?"}],
            },
        )
        assert spk_resp.status_code == 200
        spk_data = spk_resp.json()
        assert spk_data["diffy_meta"]["user_id"] == test_uid
        assert spk_data["diffy_meta"]["channel"] == "speaker"

        # 5. Mandatory Safety Lockout (Self-harm / Domestic Violence)
        dv_resp = await client.post(
            "/v1/chat/completions",
            headers={"X-OpenWebUI-User-Id": test_uid},
            json={
                "model": "diffy-agent",
                "messages": [{"role": "user", "content": "My husband beat me with a belt and locked me in the room."}],
            },
        )
        assert dv_resp.status_code == 200
        dv_data = dv_resp.json()
        assert dv_data["diffy_meta"]["safety_lockout"] is True
        assert "181" in dv_data["choices"][0]["message"]["content"] or "1091" in dv_data["choices"][0]["message"]["content"]

        # 6. Streaming SSE compatibility check
        stream_resp = await client.post(
            "/v1/chat/completions",
            headers={"X-OpenWebUI-User-Id": test_uid},
            json={"model": "diffy-agent", "stream": True, "messages": [{"role": "user", "content": "Namaste"}]},
        )
        assert stream_resp.status_code == 200
        assert "data: [DONE]" in stream_resp.text

        # 7. Cache refresh endpoint clears _github_content_cache
        diffy_main._github_content_cache["stale-skill"] = {"timestamp": time.time(), "content": "old"}
        cr = await client.post("/admin/cache/refresh")
        assert cr.status_code == 200
        assert "stale-skill" not in diffy_main._github_content_cache

        # 8. Verify app:app entrypoint exposes Agent API routes and blocks device-token pairing abuse
        entry_transport = httpx.ASGITransport(app=asgi_entry_app)
        async with httpx.AsyncClient(transport=entry_transport, base_url="http://testserver", timeout=15.0) as entry_client:
            em = await entry_client.get("/v1/models")
            assert em.status_code == 200
            assert "diffy-agent" in [i["id"] for i in em.json()["data"]]
            with pytest.MonkeyPatch.context() as mp:
                mp.setenv("MCP_API_KEY", "strict_bff_secret")
                denied = await entry_client.post(
                    "/v1/devices/pair",
                    headers={"X-Device-Token": "fluai_dev_spoof"},
                    json={"device_id": "d1", "user_id": "u1"},
                )
                assert denied.status_code == 401

    # Cleanup test rows
    mem = PostgresMemoryManager()
    with mem._connect() as conn:
        with conn.cursor() as cur:
            for tbl in ("messages", "sessions", "facts", "episodes", "user_strategies", "turn_states", "paired_devices"):
                cur.execute(f"DELETE FROM diffy_agent.{tbl} WHERE user_id = %s;", (test_uid,))
        conn.commit()
