"""Unified Agent Orchestrator for Diffy Agent API (/v1/chat/completions).

Enforces on EVERY turn in code (never optional for the LLM):
1. Canonical user identity resolution (BFF headers / paired device token / eval ID)
2. Mandatory Observer (`ProblemAnalyzer`) + Safety Guard (multilingual + optional model check)
3. Mandatory Policy Engine (`DynamicSkillRouter`) + SKILL.md injection
4. Unified Memory retrieval & persistence via Neon Postgres + pgvector (`diffy_agent` schema)
5. Single centralized LLM execution (Gemini or OpenAI-compatible)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
import uuid
from typing import Any, Awaitable, Callable, Dict, List, Optional

import httpx

from memory.pg_memory import PostgresMemoryManager, get_memory_manager
from router.analyzer import ProblemAnalyzer
from router.registry import get_skill_registry
from router.skill_router import DynamicSkillRouter

logger = logging.getLogger("diffy.agent.orchestrator")

SkillContentLoader = Callable[[str], Awaitable[Optional[str]]]


def _format_safety_response(risk_categories: List[str], user_text: str) -> str:
    """Deterministic crisis-safe human-centered response with verified helplines."""
    is_hi_or_hinglish = bool(re.search(r"[\u0900-\u097F]|\b(hai|hain|mera|meri|mujhe|nahi|karun|kaise|ghar|pati|patni)\b", user_text, re.I))

    if "self_harm" in risk_categories:
        if is_hi_or_hinglish:
            return (
                "Main samajh sakta hoon ki aap abhi bahut gehre dard aur mushkil waqt se guzar rahe hain. "
                "Aap akeli/akele nahi hain, aur aapki suraksha sabse zaroori hai. "
                "Kripya turant kisi bharosemand parivarjan ya trained counselor se baat karein:\n"
                "- **Tele-MANAS (24x7 Govt Helpline):** 14416 ya 1800-891-4416\n"
                "- **Vandrevala Foundation:** 9999 666 555\n"
                "- **Emergency:** 112"
            )
        return (
            "I hear how much pain you are carrying right now, and your safety matters deeply. "
            "You do not have to go through this alone. Please reach out to someone who can support you right now:\n"
            "- **Tele-MANAS (24x7 National Helpline):** 14416 or 1800-891-4416\n"
            "- **Vandrevala Foundation:** 9999 666 555\n"
            "- **Emergency Services:** 112"
        )

    if "domestic_violence" in risk_categories or "threats_and_immediate_danger" in risk_categories:
        if is_hi_or_hinglish:
            return (
                "Jo aapke saath ho raha hai uske liye main dil se chintit hoon. Kisi bhi tarah ki maar-peet, dhamki ya dabav bilkul sahi nahi hai, "
                "aur aisi sthiti mein joint mediation safe nahi hoti. Kripya pehle apni suraksha par dhyan dein aur turant sahayata lein:\n"
                "- **Women Helpline / Domestic Abuse:** 181 ya 1091\n"
                "- **NCW Helpline:** 7827170170\n"
                "- **Emergency Police:** 112"
            )
        return (
            "I am deeply concerned about your safety. Physical harm, intimidation, or threats are never acceptable, "
            "and joint mediation is unsafe in situations involving abuse or coercion. Please prioritize your safety and contact confidential support:\n"
            "- **Women & Domestic Violence Helpline:** 181 or 1091\n"
            "- **NCW 24x7 Helpline:** 7827170170\n"
            "- **Emergency Services:** 112"
        )

    if "child_safeguarding" in risk_categories:
        return (
            "A child's physical and emotional safety comes first. Please reach out immediately for specialized guidance:\n"
            "- **Childline India (24x7):** 1098\n"
            "- **Emergency Services:** 112"
        )

    return (
        "Your safety comes first. Please consider speaking with a trusted person or professional support service:\n"
        "- **Tele-MANAS:** 14416\n"
        "- **Emergency:** 112"
    )


class AgentOrchestrator:
    """Centralized Agent API orchestrator replacing split orchestration in Open WebUI & ProductSpeaker."""

    def __init__(
        self,
        memory_mgr: Optional[PostgresMemoryManager] = None,
        analyzer: Optional[ProblemAnalyzer] = None,
        skill_router: Optional[DynamicSkillRouter] = None,
        skill_loader: Optional[SkillContentLoader] = None,
    ):
        self.memory = memory_mgr or get_memory_manager()
        self.analyzer = analyzer or ProblemAnalyzer()
        self.skill_router = skill_router or DynamicSkillRouter(registry=get_skill_registry())
        self.skill_loader = skill_loader

    def _extract_last_user_message(self, messages: List[Dict[str, Any]]) -> str:
        for msg in reversed(messages or []):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, list):
                    parts = [p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text"]
                    return " ".join(parts).strip()
                return str(content).strip()
        return ""

    async def _load_selected_skills(self, selected_skills: List[Any]) -> List[Dict[str, str]]:
        loaded: List[Dict[str, str]] = []
        for s in selected_skills:
            skill_id = getattr(s, "skill_id", None) or (s.get("skill_id") if isinstance(s, dict) else None)
            if not skill_id:
                continue
            content = None
            if self.skill_loader:
                try:
                    content = await self.skill_loader(skill_id)
                except Exception as e:
                    logger.warning(f"Failed loading skill '{skill_id}': {e}")
            loaded.append(
                {
                    "skill_id": skill_id,
                    "tier": getattr(s, "tier", "") or (s.get("tier", "") if isinstance(s, dict) else ""),
                    "reason": getattr(s, "selection_reason", "") or (s.get("selection_reason", "") if isinstance(s, dict) else ""),
                    "content": (content or "")[:3500],
                }
            )
        return loaded

    def _build_system_prompt(
        self,
        channel: str,
        analysis_dict: Dict[str, Any],
        routed_dict: Dict[str, Any],
        loaded_skills: List[Dict[str, str]],
        memory_ctx: Dict[str, Any],
    ) -> str:
        sections: List[str] = [
            "You are Aether (powered by Diffy Agent API), a warm, emotionally grounded, human-centered AI companion.",
            "Respond in the exact same language and tone the user uses (English, Hindi, or natural Hinglish).",
            "Listen and validate feelings first before offering perspective. Never blame, judge, or use cold robotic bullet lists unless asked.",
        ]

        if channel == "speaker":
            sections.append(
                "CHANNEL DIRECTIVE (VOICE SPEAKER): Keep your reply concise — 1 to 3 warm, natural spoken sentences. "
                "Avoid markdown formatting, asterisks, bullet symbols, or tables so edge-TTS reads smoothly."
            )

        understanding = analysis_dict.get("understanding", {})
        sections.append(
            "MANDATORY PROBLEM ANALYSIS:\n"
            f"- Domains: {', '.join(understanding.get('domains', [])) or 'general'}\n"
            f"- Emotional Signals: {', '.join(understanding.get('emotional_signals', [])) or 'neutral'}\n"
            f"- Patterns: {', '.join(understanding.get('problem_patterns', [])) or 'none'}"
        )

        safety_guidance = routed_dict.get("safety_guidance", [])
        if safety_guidance:
            sections.append("MANDATORY SAFETY GUARDRAILS:\n" + "\n".join(f"- {g}" for g in safety_guidance))

        if routed_dict.get("clarification_required") and analysis_dict.get("clarification_question"):
            sections.append(
                f"CLARIFICATION NEEDED: Context is still incomplete. Gently ask: {analysis_dict['clarification_question']}"
            )

        if loaded_skills:
            skill_blocks = []
            for sk in loaded_skills:
                block = f"### Skill: {sk['skill_id']} ({sk['tier']})\nReason: {sk['reason']}"
                if sk["content"]:
                    block += f"\n{sk['content']}"
                skill_blocks.append(block)
            sections.append("ACTIVE ROUTED SKILLS:\n" + "\n\n".join(skill_blocks))

        # Memory Context
        mem_lines = []
        facts = memory_ctx.get("facts") or []
        if facts:
            mem_lines.append("User Semantic Facts: " + "; ".join(f"{f['fact_key']}={f['fact_value']}" for f in facts))
        episodes = memory_ctx.get("episodes") or []
        if episodes:
            mem_lines.append("Past Session Episodes: " + "; ".join(f"{e['summary']} (mood: {e.get('emotion_trend','neutral')})" for e in episodes))
        strategies = memory_ctx.get("strategies") or []
        if strategies:
            mem_lines.append("Effective Approaches for this User: " + ", ".join(s["strategy_mode"] for s in strategies))
        if mem_lines:
            sections.append("UNIFIED USER MEMORY:\n" + "\n".join(mem_lines))

        return "\n\n".join(sections)

    async def _model_observe_and_safety(self, user_text: str) -> Optional[Dict[str, Any]]:
        """Model-based semantic observer and crisis detector supplementing keyword triage."""
        if os.getenv("DIFFY_MODEL_OBSERVER_ENABLED", "true").lower() != "true":
            return None
        gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not gemini_key or len(user_text.strip()) < 8:
            return None

        prompt = (
            "Analyze this user message for crisis risk (self-harm/suicide, domestic violence/coercive control, "
            "child endangerment, or immediate physical danger), primary life domains, and emotional signals.\n"
            'Return strict JSON only: {"crisis": true|false, "category": "self_harm"|"domestic_violence"|"child_safeguarding"|"threats_and_immediate_danger"|"none", '
            '"domains": ["..."], "emotions": ["..."]}\n'
            f"Message: {user_text[:800]}"
        )
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            resp = await asyncio.to_thread(
                client.models.generate_content,
                model=os.getenv("DIFFY_SAFETY_MODEL", "gemini-3.5-flash-lite"),
                contents=prompt,
            )
            raw = (getattr(resp, "text", "") or "").strip()
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                data = json.loads(m.group(0))
                if isinstance(data, dict):
                    return data
        except Exception as e:
            logger.debug(f"Model observer/safety skipped or unavailable: {e}")
        return None

    async def _call_llm(
        self,
        system_prompt: str,
        messages: List[Dict[str, Any]],
        history_from_db: List[Dict[str, Any]],
        model_hint: Optional[str] = None,
    ) -> str:
        """Execute LLM inference via Gemini or OpenAI-compatible provider configured on Diffy."""
        gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        openai_base = os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1").rstrip("/")

        # Merge recent DB history if caller only sent current turn (e.g. voice gateway)
        convo: List[Dict[str, str]] = []
        if len(messages) <= 1 and history_from_db:
            for h in history_from_db[-8:]:
                if h.get("role") in ("user", "assistant") and h.get("content"):
                    convo.append({"role": h["role"], "content": h["content"]})
        for m in messages:
            if m.get("role") in ("user", "assistant"):
                c = m.get("content", "")
                if isinstance(c, list):
                    c = " ".join(p.get("text", "") for p in c if isinstance(p, dict))
                if str(c).strip():
                    convo.append({"role": m["role"], "content": str(c).strip()})

        # Prefer Gemini when configured (with verified 3.5-flash / 3.5-flash-lite fallback)
        if gemini_key:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=gemini_key)
            gemini_contents = [
                types.Content(
                    role="model" if m["role"] == "assistant" else "user",
                    parts=[types.Part.from_text(text=m["content"])],
                )
                for m in convo
            ]
            primary_model = os.getenv("DIFFY_GEMINI_MODEL", "gemini-3.5-flash")
            if model_hint and model_hint.startswith("gemini"):
                primary_model = model_hint
            candidate_models = [primary_model]
            if primary_model != "gemini-3.5-flash-lite":
                candidate_models.append("gemini-3.5-flash-lite")

            for target_model in candidate_models:
                try:
                    resp = await asyncio.to_thread(
                        client.models.generate_content,
                        model=target_model,
                        contents=gemini_contents,
                        config=types.GenerateContentConfig(
                            system_instruction=system_prompt,
                            temperature=0.7,
                        ),
                    )
                    text = (getattr(resp, "text", "") or "").strip()
                    if text:
                        return text
                except Exception as e:
                    logger.warning(f"Gemini model '{target_model}' failed: {e}")

        if openai_key:
            try:
                target_model = os.getenv("DIFFY_OPENAI_MODEL", "gpt-4o-mini")
                if model_hint and model_hint not in ("diffy-agent", "default"):
                    if not model_hint.startswith("gemini"):
                        target_model = model_hint
                payload = {
                    "model": target_model,
                    "messages": [{"role": "system", "content": system_prompt}] + convo,
                    "temperature": 0.7,
                }
                async with httpx.AsyncClient(timeout=45.0) as client:
                    r = await client.post(
                        f"{openai_base}/chat/completions",
                        headers={"Authorization": f"Bearer {openai_key}"},
                        json=payload,
                    )
                    r.raise_for_status()
                    data = r.json()
                    return data["choices"][0]["message"]["content"].strip()
            except Exception as e:
                logger.warning(f"OpenAI inference failed: {e}")

        # Safe empathetic fallback if no upstream LLM credentials are configured
        return (
            "I am here listening with you. Please share a little more about what feels hardest right now "
            "so we can think through it gently together."
        )

    async def handle_chat_completion(
        self,
        payload: Dict[str, Any],
        user_id: str,
        session_id: str,
        channel: str = "app",
    ) -> Dict[str, Any]:
        """Run mandatory Observer -> Safety -> Router -> Memory -> LLM -> Persist pipeline."""
        messages = payload.get("messages") or []
        user_text = self._extract_last_user_message(messages)
        model_name = payload.get("model") or "diffy-agent"

        if not user_text:
            reply = "Hello, I am listening. How can I support you today?"
            return self._openai_response(reply, model_name, {"user_id": user_id, "channel": channel})

        # 1. Fetch unified memory context (non-blocking empty if anonymous/disabled)
        memory_ctx = await self.memory.build_memory_context(user_id=user_id, session_id=session_id, query=user_text)

        # 2. Mandatory Observer (`ProblemAnalyzer`) + Model Observer & Safety Triage
        analysis = self.analyzer.analyze(user_text, memory_ctx.get("history") or [])
        if not analysis.safety.potential_risk:
            model_obs = await self._model_observe_and_safety(user_text)
            if model_obs:
                cat = model_obs.get("category")
                if model_obs.get("crisis") is True and cat in (
                    "self_harm",
                    "domestic_violence",
                    "child_safeguarding",
                    "threats_and_immediate_danger",
                ):
                    analysis.safety.potential_risk = True
                    analysis.safety.requires_safe_followup = True
                    if cat not in analysis.safety.risk_categories:
                        analysis.safety.risk_categories.append(cat)
                    analysis.safety.reason = "Model-based safety guard detected crisis indicator."

                # Enrich domains & emotional signals when model observer detects nuances
                for dom in (model_obs.get("domains") or [])[:2]:
                    if isinstance(dom, str) and dom.strip() and dom not in analysis.understanding.domains:
                        if analysis.understanding.domains == ["other_or_unknown"]:
                            analysis.understanding.domains = [dom.strip()]
                        else:
                            analysis.understanding.domains.append(dom.strip())
                for emo in (model_obs.get("emotions") or [])[:2]:
                    if isinstance(emo, str) and emo.strip() and emo not in analysis.understanding.emotional_signals:
                        analysis.understanding.emotional_signals.append(emo.strip())
        analysis_dict = analysis.model_dump()

        # 3. Mandatory Policy Engine (`DynamicSkillRouter`)
        routed = self.skill_router.route(analysis, query_hint=user_text)
        routed_dict = routed.model_dump()

        # 4. Acute safety crisis fast-path (fail-closed, never enters mediation)
        acute_cats = {"self_harm", "domestic_violence", "child_safeguarding", "threats_and_immediate_danger"}
        if analysis.safety.potential_risk and any(c in acute_cats for c in analysis.safety.risk_categories):
            reply_text = _format_safety_response(analysis.safety.risk_categories, user_text)
            await self._persist_turn(
                session_id=session_id,
                user_id=user_id,
                channel=channel,
                user_text=user_text,
                reply_text=reply_text,
                analysis_dict=analysis_dict,
                routed_dict=routed_dict,
                safety_status="crisis_lockout",
            )
            return self._openai_response(
                reply_text,
                model_name,
                {
                    "user_id": user_id,
                    "channel": channel,
                    "safety_lockout": True,
                    "routed_skills": [s["skill_id"] for s in routed_dict.get("selected_skills", [])],
                },
            )

        # 5. Load routed SKILL.md content & call centralized LLM
        loaded_skills = await self._load_selected_skills(routed.selected_skills)
        system_prompt = self._build_system_prompt(
            channel=channel,
            analysis_dict=analysis_dict,
            routed_dict=routed_dict,
            loaded_skills=loaded_skills,
            memory_ctx=memory_ctx,
        )
        reply_text = await self._call_llm(
            system_prompt=system_prompt,
            messages=messages,
            history_from_db=memory_ctx.get("history") or [],
            model_hint=model_name,
        )

        # 6. Persist unified memory & observer trace in Neon Postgres
        await self._persist_turn(
            session_id=session_id,
            user_id=user_id,
            channel=channel,
            user_text=user_text,
            reply_text=reply_text,
            analysis_dict=analysis_dict,
            routed_dict=routed_dict,
            safety_status="safe",
        )

        return self._openai_response(
            reply_text,
            model_name,
            {
                "user_id": user_id,
                "channel": channel,
                "safety_lockout": False,
                "routed_skills": [s["skill_id"] for s in routed_dict.get("selected_skills", [])],
            },
        )

    async def _persist_turn(
        self,
        session_id: str,
        user_id: str,
        channel: str,
        user_text: str,
        reply_text: str,
        analysis_dict: Dict[str, Any],
        routed_dict: Dict[str, Any],
        safety_status: str,
    ) -> None:
        if not self.memory.enabled:
            return
        try:
            tasks = [
                self.memory.append_message(session_id, user_id, channel, "user", user_text),
                self.memory.append_message(session_id, user_id, channel, "assistant", reply_text),
                self.memory.record_turn_state(session_id, user_id, channel, analysis_dict, routed_dict, safety_status),
            ]
            # Update episodic summary periodically for real authenticated users
            if user_id and user_id not in ("anonymous", "default_user"):
                emotions = analysis_dict.get("understanding", {}).get("emotional_signals") or ["neutral"]
                summary = analysis_dict.get("understanding", {}).get("summary") or ""
                if summary and safety_status == "safe":
                    tasks.append(self.memory.store_episode(user_id, session_id, summary, emotions[0]))

                # Extract simple safe preference if explicitly stated (name / preferred language)
                name_match = re.search(r"\b(?:my name is|mera naam)\s+([A-Za-z\u0900-\u097F]{2,25})\b", user_text, re.I)
                if name_match:
                    tasks.append(self.memory.store_fact(user_id, "preferred_name", name_match.group(1), category="profile", consent=True))

                for sk in routed_dict.get("selected_skills", [])[:1]:
                    tasks.append(self.memory.update_user_strategy(user_id, sk["skill_id"], 0.75))

            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.warning(f"Memory persistence warning (non-fatal): {e}")

    def _openai_response(self, content: str, model: str, meta: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:16]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "diffy_meta": meta,
        }


_orchestrator_singleton: Optional[AgentOrchestrator] = None


def get_agent_orchestrator(skill_loader: Optional[SkillContentLoader] = None) -> AgentOrchestrator:
    global _orchestrator_singleton
    if _orchestrator_singleton is None:
        _orchestrator_singleton = AgentOrchestrator(skill_loader=skill_loader)
    elif skill_loader is not None and _orchestrator_singleton.skill_loader is None:
        _orchestrator_singleton.skill_loader = skill_loader
    return _orchestrator_singleton
