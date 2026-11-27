"""Neon PostgreSQL + pgvector Memory & Device Pairing Manager for Diffy Agent API.

Owns all 5 memory tiers in schema `diffy_agent`:
1. Session memory (`sessions`, `messages` tagged with channel: app | speaker | eval)
2. Episodic memory (`episodes` with summary, emotion_trend, pgvector embedding)
3. Semantic memory (`facts` with valid_from / valid_to, pgvector embedding, trauma filter)
4. Procedural memory (`user_strategies` mapping user + mode -> outcome_score)
5. Observer trace (`turn_states` capturing analyzer output, routed skills, safety status)

Also manages per-device identity pairing (`paired_devices`) linking ESP32 devices to canonical user_id.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import math
import os
import re
import secrets
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger("diffy.memory.pg")

EMBEDDING_DIM = 384

_SENSITIVE_DISCLOSURE_PATTERN = re.compile(
    r"(depress|suicid|self.?harm|abuse|medic|mental|violenc|assault|beat|mar.?peet|dahej|आत्महत्या|मारपीट|हिंसा)",
    re.IGNORECASE,
)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _compute_text_embedding(text: str, dim: int = EMBEDDING_DIM) -> List[float]:
    """Deterministic normalized bag-of-ngrams embedding for offline/low-latency pgvector search."""
    vec = [0.0] * dim
    tokens = re.findall(r"[\w\u0900-\u097F]+", (text or "").lower())
    if not tokens:
        return vec
    for tok in tokens:
        # Unigram + character trigram hashing for Hinglish/Hindi robustness
        grams = [tok] + [tok[i : i + 3] for i in range(max(0, len(tok) - 2))]
        for g in grams:
            h = int(hashlib.blake2b(g.encode("utf-8"), digest_size=8).hexdigest(), 16)
            idx = h % dim
            sign = 1.0 if ((h >> 8) & 1) == 0 else -1.0
            vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [round(v / norm, 6) for v in vec]
    return vec


def _vector_literal(vec: List[float]) -> str:
    return "[" + ",".join(f"{v:.6f}" for v in vec) + "]"


class PostgresMemoryManager:
    """Thread-safe Neon PostgreSQL + pgvector memory store for Diffy Agent API."""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = (database_url or os.getenv("DATABASE_URL", "")).strip()
        self._schema_initialized = False
        self._init_lock = asyncio.Lock()
        self._conn_lock = threading.Lock()
        self._shared_conn: Optional[psycopg.Connection] = None

    @property
    def enabled(self) -> bool:
        return bool(self.database_url and self.database_url.startswith(("postgresql://", "postgres://")))

    @contextmanager
    def _connect(self):
        if not self.enabled:
            raise RuntimeError("DATABASE_URL is not configured for PostgresMemoryManager")
        with self._conn_lock:
            if self._shared_conn is None or self._shared_conn.closed:
                # prepare_threshold=None avoids PgBouncer prepared-statement conflicts on Neon -pooler
                self._shared_conn = psycopg.connect(
                    self.database_url,
                    row_factory=dict_row,
                    prepare_threshold=None,
                    connect_timeout=10,
                )
            try:
                yield self._shared_conn
            except psycopg.Error:
                try:
                    self._shared_conn.rollback()
                except Exception:
                    try:
                        self._shared_conn.close()
                    except Exception:
                        pass
                    self._shared_conn = None
                raise

    def ensure_schema_sync(self) -> bool:
        """Create pgvector extension and all diffy_agent tables idempotently."""
        if not self.enabled:
            return False
        if self._schema_initialized:
            return True

        ddl_statements = [
            "CREATE EXTENSION IF NOT EXISTS vector;",
            "CREATE SCHEMA IF NOT EXISTS diffy_agent;",
            """
            CREATE TABLE IF NOT EXISTS diffy_agent.sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                channel TEXT NOT NULL DEFAULT 'app',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS diffy_agent.messages (
                id BIGSERIAL PRIMARY KEY,
                session_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                channel TEXT NOT NULL DEFAULT 'app',
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """,
            "CREATE INDEX IF NOT EXISTS idx_diffy_messages_user_session ON diffy_agent.messages (user_id, session_id, id DESC);",
            """
            CREATE TABLE IF NOT EXISTS diffy_agent.episodes (
                id BIGSERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                session_id TEXT,
                summary TEXT NOT NULL,
                emotion_trend TEXT DEFAULT 'neutral',
                embedding vector(384),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """,
            "CREATE INDEX IF NOT EXISTS idx_diffy_episodes_user ON diffy_agent.episodes (user_id, created_at DESC);",
            """
            CREATE TABLE IF NOT EXISTS diffy_agent.facts (
                id BIGSERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                fact_key TEXT NOT NULL,
                fact_value TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'general',
                valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                valid_to TIMESTAMPTZ,
                embedding vector(384),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE (user_id, fact_key)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS diffy_agent.user_strategies (
                id BIGSERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                strategy_mode TEXT NOT NULL,
                outcome_score DOUBLE PRECISION NOT NULL DEFAULT 0.5,
                sample_count INTEGER NOT NULL DEFAULT 1,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE (user_id, strategy_mode)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS diffy_agent.turn_states (
                id BIGSERIAL PRIMARY KEY,
                session_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                channel TEXT NOT NULL,
                analysis_json JSONB NOT NULL,
                routed_skills_json JSONB NOT NULL,
                safety_status TEXT NOT NULL DEFAULT 'safe',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS diffy_agent.paired_devices (
                device_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                device_token_hash TEXT UNIQUE NOT NULL,
                device_name TEXT NOT NULL DEFAULT 'ESP32 Speaker',
                active BOOLEAN NOT NULL DEFAULT TRUE,
                paired_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """,
        ]

        with self._connect() as conn:
            with conn.cursor() as cur:
                for stmt in ddl_statements:
                    cur.execute(stmt)
            conn.commit()

        self._schema_initialized = True
        logger.info("Neon PostgreSQL schema `diffy_agent` initialized successfully.")
        return True

    async def ensure_schema(self) -> bool:
        if not self.enabled:
            return False
        if self._schema_initialized:
            return True
        async with self._init_lock:
            if not self._schema_initialized:
                return await asyncio.to_thread(self.ensure_schema_sync)
        return True

    # ── Device Pairing (Canonical User Identity) ──────────────────────────

    async def pair_device(
        self,
        device_id: str,
        user_id: str,
        device_name: str = "ESP32 Speaker",
    ) -> Dict[str, Any]:
        """Issue or rotate a unique device token linked to a canonical user_id."""
        if not device_id or not user_id or user_id == "default_user":
            raise ValueError("Valid device_id and non-anonymous user_id are required for pairing.")
        await self.ensure_schema()

        raw_token = f"fluai_dev_{secrets.token_urlsafe(32)}"
        token_hash = _hash_token(raw_token)

        def _op():
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO diffy_agent.paired_devices
                            (device_id, user_id, device_token_hash, device_name, active, paired_at, last_seen_at)
                        VALUES (%s, %s, %s, %s, TRUE, NOW(), NOW())
                        ON CONFLICT (device_id) DO UPDATE SET
                            user_id = EXCLUDED.user_id,
                            device_token_hash = EXCLUDED.device_token_hash,
                            device_name = EXCLUDED.device_name,
                            active = TRUE,
                            paired_at = NOW(),
                            last_seen_at = NOW();
                        """,
                        (device_id.strip(), user_id.strip(), token_hash, device_name.strip()),
                    )
                conn.commit()

        await asyncio.to_thread(_op)
        return {
            "device_id": device_id.strip(),
            "user_id": user_id.strip(),
            "device_name": device_name.strip(),
            "device_token": raw_token,
        }

    async def resolve_device_user(self, device_token: str) -> Optional[Dict[str, Any]]:
        """Resolve canonical user_id from a per-device bearer token."""
        if not self.enabled or not device_token:
            return None
        await self.ensure_schema()
        token_hash = _hash_token(device_token.strip())

        def _op() -> Optional[Dict[str, Any]]:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE diffy_agent.paired_devices
                        SET last_seen_at = NOW()
                        WHERE device_token_hash = %s AND active = TRUE
                        RETURNING device_id, user_id, device_name, paired_at;
                        """,
                        (token_hash,),
                    )
                    row = cur.fetchone()
                conn.commit()
                return dict(row) if row else None

        return await asyncio.to_thread(_op)

    # ── Session & Message Memory ──────────────────────────────────────────

    async def append_message(
        self,
        session_id: str,
        user_id: str,
        channel: str,
        role: str,
        content: str,
    ) -> None:
        if not self.enabled or not content.strip():
            return
        await self.ensure_schema()

        def _op():
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO diffy_agent.sessions (session_id, user_id, channel, updated_at)
                        VALUES (%s, %s, %s, NOW())
                        ON CONFLICT (session_id) DO UPDATE SET updated_at = NOW();
                        """,
                        (session_id, user_id, channel),
                    )
                    cur.execute(
                        """
                        INSERT INTO diffy_agent.messages (session_id, user_id, channel, role, content)
                        VALUES (%s, %s, %s, %s, %s);
                        """,
                        (session_id, user_id, channel, role, content),
                    )
                conn.commit()

        await asyncio.to_thread(_op)

    async def get_recent_messages(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 12,
    ) -> List[Dict[str, Any]]:
        """Fetch recent turns across channels (or scoped session) for canonical user_id."""
        if not self.enabled or not user_id or user_id == "default_user":
            return []
        await self.ensure_schema()

        def _op() -> List[Dict[str, Any]]:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    if session_id:
                        cur.execute(
                            """
                            SELECT role, content, channel, created_at
                            FROM diffy_agent.messages
                            WHERE user_id = %s AND session_id = %s
                            ORDER BY id DESC LIMIT %s;
                            """,
                            (user_id, session_id, limit),
                        )
                    else:
                        cur.execute(
                            """
                            SELECT role, content, channel, created_at
                            FROM diffy_agent.messages
                            WHERE user_id = %s
                            ORDER BY id DESC LIMIT %s;
                            """,
                            (user_id, limit),
                        )
                    rows = cur.fetchall()
            rows.reverse()
            return [dict(r) for r in rows]

        return await asyncio.to_thread(_op)

    # ── Semantic Memory (Facts with Trauma Filter) ────────────────────────

    async def store_fact(
        self,
        user_id: str,
        fact_key: str,
        fact_value: str,
        category: str = "general",
        consent: bool = True,
    ) -> bool:
        if not self.enabled or not user_id or user_id == "default_user" or not consent:
            return False
        if _SENSITIVE_DISCLOSURE_PATTERN.search(f"{fact_key} {fact_value}"):
            logger.warning("Skipped storing sensitive disclosure in semantic facts for user privacy.")
            return False
        await self.ensure_schema()
        vec = _vector_literal(_compute_text_embedding(f"{fact_key}: {fact_value}"))

        def _op():
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO diffy_agent.facts (user_id, fact_key, fact_value, category, valid_from, valid_to, embedding)
                        VALUES (%s, %s, %s, %s, NOW(), NULL, %s::vector)
                        ON CONFLICT (user_id, fact_key) DO UPDATE SET
                            fact_value = EXCLUDED.fact_value,
                            category = EXCLUDED.category,
                            valid_from = NOW(),
                            valid_to = NULL,
                            embedding = EXCLUDED.embedding;
                        """,
                        (user_id, fact_key.strip(), fact_value.strip(), category, vec),
                    )
                conn.commit()

        await asyncio.to_thread(_op)
        return True

    async def retrieve_relevant_facts(self, user_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not self.enabled or not user_id or user_id == "default_user":
            return []
        await self.ensure_schema()
        vec = _vector_literal(_compute_text_embedding(query))

        def _op() -> List[Dict[str, Any]]:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT fact_key, fact_value, category,
                               1 - (embedding <=> %s::vector) AS similarity
                        FROM diffy_agent.facts
                        WHERE user_id = %s AND (valid_to IS NULL OR valid_to > NOW())
                        ORDER BY embedding <=> %s::vector ASC
                        LIMIT %s;
                        """,
                        (vec, user_id, vec, limit),
                    )
                    return [dict(r) for r in cur.fetchall()]

        return await asyncio.to_thread(_op)

    # ── Episodic Memory (Cross-Session Summaries) ─────────────────────────

    async def store_episode(
        self,
        user_id: str,
        session_id: Optional[str],
        summary: str,
        emotion_trend: str = "neutral",
    ) -> None:
        if not self.enabled or not user_id or user_id == "default_user" or not summary.strip():
            return
        if _SENSITIVE_DISCLOSURE_PATTERN.search(summary):
            # Store sanitized thematic marker rather than explicit trauma details
            summary = "Sensitive personal safety check-in occurred."
        await self.ensure_schema()
        vec = _vector_literal(_compute_text_embedding(summary))

        def _op():
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO diffy_agent.episodes (user_id, session_id, summary, emotion_trend, embedding)
                        VALUES (%s, %s, %s, %s, %s::vector);
                        """,
                        (user_id, session_id, summary.strip(), emotion_trend, vec),
                    )
                conn.commit()

        await asyncio.to_thread(_op)

    async def retrieve_relevant_episodes(self, user_id: str, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        if not self.enabled or not user_id or user_id == "default_user":
            return []
        await self.ensure_schema()
        vec = _vector_literal(_compute_text_embedding(query))

        def _op() -> List[Dict[str, Any]]:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT summary, emotion_trend, created_at
                        FROM diffy_agent.episodes
                        WHERE user_id = %s
                        ORDER BY embedding <=> %s::vector ASC
                        LIMIT %s;
                        """,
                        (user_id, vec, limit),
                    )
                    return [dict(r) for r in cur.fetchall()]

        return await asyncio.to_thread(_op)

    # ── Procedural Memory & Observer Trace ────────────────────────────────

    async def update_user_strategy(self, user_id: str, strategy_mode: str, outcome_score: float) -> None:
        if not self.enabled or not user_id or user_id == "default_user":
            return
        await self.ensure_schema()

        def _op():
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO diffy_agent.user_strategies (user_id, strategy_mode, outcome_score, sample_count, updated_at)
                        VALUES (%s, %s, %s, 1, NOW())
                        ON CONFLICT (user_id, strategy_mode) DO UPDATE SET
                            outcome_score = (diffy_agent.user_strategies.outcome_score * diffy_agent.user_strategies.sample_count + EXCLUDED.outcome_score)
                                            / (diffy_agent.user_strategies.sample_count + 1),
                            sample_count = diffy_agent.user_strategies.sample_count + 1,
                            updated_at = NOW();
                        """,
                        (user_id, strategy_mode, max(0.0, min(1.0, float(outcome_score)))),
                    )
                conn.commit()

        await asyncio.to_thread(_op)

    async def get_preferred_strategies(self, user_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        if not self.enabled or not user_id or user_id == "default_user":
            return []
        await self.ensure_schema()

        def _op() -> List[Dict[str, Any]]:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT strategy_mode, outcome_score, sample_count
                        FROM diffy_agent.user_strategies
                        WHERE user_id = %s
                        ORDER BY outcome_score DESC, sample_count DESC
                        LIMIT %s;
                        """,
                        (user_id, limit),
                    )
                    return [dict(r) for r in cur.fetchall()]

        return await asyncio.to_thread(_op)

    async def record_turn_state(
        self,
        session_id: str,
        user_id: str,
        channel: str,
        analysis: Dict[str, Any],
        routed: Dict[str, Any],
        safety_status: str,
    ) -> None:
        if not self.enabled:
            return
        await self.ensure_schema()

        def _op():
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO diffy_agent.turn_states
                            (session_id, user_id, channel, analysis_json, routed_skills_json, safety_status)
                        VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s);
                        """,
                        (
                            session_id,
                            user_id or "anonymous",
                            channel,
                            json.dumps(analysis, ensure_ascii=False),
                            json.dumps(routed, ensure_ascii=False),
                            safety_status,
                        ),
                    )
                conn.commit()

        await asyncio.to_thread(_op)

    async def build_memory_context(self, user_id: str, session_id: Optional[str], query: str) -> Dict[str, Any]:
        """Gather unified context across Session, Semantic, Episodic, and Procedural tiers."""
        if not self.enabled or not user_id or user_id == "default_user":
            return {"history": [], "facts": [], "episodes": [], "strategies": []}

        history, facts, episodes, strategies = await asyncio.gather(
            self.get_recent_messages(user_id=user_id, session_id=session_id, limit=10),
            self.retrieve_relevant_facts(user_id=user_id, query=query, limit=4),
            self.retrieve_relevant_episodes(user_id=user_id, query=query, limit=2),
            self.get_preferred_strategies(user_id=user_id, limit=2),
        )
        return {
            "history": history,
            "facts": facts,
            "episodes": episodes,
            "strategies": strategies,
        }


_memory_manager_singleton: Optional[PostgresMemoryManager] = None


def get_memory_manager() -> PostgresMemoryManager:
    global _memory_manager_singleton
    if _memory_manager_singleton is None:
        _memory_manager_singleton = PostgresMemoryManager()
    return _memory_manager_singleton
