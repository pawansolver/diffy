"""FastMCP Skills Provider Server"""

import asyncio
import hmac
import json
import logging
import os
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

import httpx
from fastmcp import FastMCP
from fastmcp.server.providers.skills import SkillsDirectoryProvider
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, StreamingResponse
import uvicorn
from starlette.middleware.base import BaseHTTPMiddleware

from agent.orchestrator import get_agent_orchestrator
from config import ConfigLoader, GithubConfig
from memory.pg_memory import get_memory_manager
from router.analyzer import ProblemAnalyzer
from router.registry import get_skill_registry
from router.skill_router import DynamicSkillRouter

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Protect HTTP MCP, Agent API, and instruction routes when MCP_API_KEY is configured."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)

        expected_key = os.getenv("MCP_API_KEY", "").strip()
        if not expected_key:
            return await call_next(request)

        # Allow per-device paired tokens (`fluai_dev_...`) only on chat/models Agent API endpoints
        device_token = request.headers.get("x-device-token", "").strip()
        authorization = request.headers.get("authorization", "")
        if request.url.path in ("/v1/chat/completions", "/v1/models") and (
            device_token.startswith("fluai_dev_")
            or authorization.startswith("Bearer fluai_dev_")
        ):
            return await call_next(request)

        expected_header = f"Bearer {expected_key}"
        if not hmac.compare_digest(authorization, expected_header):
            return JSONResponse(
                {"error": "unauthorized", "message": "A valid bearer token is required"},
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
        return await call_next(request)


BASE_SYSTEM_INSTRUCTION = """\
You are an intelligent, empathetic, and human-centered AI assistant with access to a dynamic skills library via MCP tools.

You have MCP tools available:
1. understand_human_problem — Understand the user's situation across life domains, emotions, patterns, intentions, and safety indicators.
2. route_skills — Dynamically select and chain relevant skills based on the problem analysis.
3. list_skills — Discover all available skills.
4. get_skill — Retrieve detailed instructions for a specific skill.
5. list_skill_files — See all files within a skill.

## Human-Centered Conversation Principles:
- Listen before advising: Always acknowledge and validate the user's expressed feelings with warmth and patience.
- Understand context before proposing solutions; ask a clarifying question when situation details are missing.
- Never judge, criticize, or blame any party involved.
- Never pretend to literally feel human emotions, and never claim to be a licensed therapist, doctor, lawyer, or emergency service.
- When safety risks (self-harm, domestic violence, child endangerment, immediate danger) are indicated, prioritize safe, non-judgmental support and official helpline options; NEVER suggest joint mediation where physical abuse or intimidation is present.

## Safe Fallback Strategy:
- When a user query does not match any specialized domain skill, provide compassionate foundational human support and thoughtful exploratory clarification. Do NOT invent missing knowledge or make up false skills.
- Always respond in the same language the user is writing in (English, Hindi, or Hinglish).
""".strip()


_github_skills_cache = {"timestamp": 0.0, "data": []}
_github_content_cache: Dict[str, Dict[str, Any]] = {}
GITHUB_CONTENT_CACHE_TTL = int(os.getenv("GITHUB_SKILL_CACHE_TTL", "300"))

class SkillsProviderServer:
    """FastMCP Skills Provider Server"""

    def __init__(self, config_file: str = "skills.settings.json"):
        self.config_loader = ConfigLoader(config_file)
        self.mcp = FastMCP("Skills Provider", instructions=BASE_SYSTEM_INSTRUCTION)
        self._setup_providers()

    def _setup_providers(self):
        directories = self.config_loader.get_directories()
        reload_mode = self.config_loader.get_reload_mode()
        supporting_files = self.config_loader.get_supporting_files_mode()

        logger.info(f"Setting up SkillsDirectoryProvider")
        logger.info(f"  Directories: {[str(d) for d in directories]}")
        logger.info(f"  Reload mode: {reload_mode}")
        logger.info(f"  Supporting files mode: {supporting_files}")

        provider = SkillsDirectoryProvider(
            roots=directories, reload=reload_mode, supporting_files=supporting_files
        )

        self.mcp.add_provider(provider)
        logger.info("SkillsDirectoryProvider added successfully")

        # Store github config for use in tools
        self.github_config = self.config_loader.get_github_config()
        # Read GitHub token from environment variable if not set in config (more secure for cloud)
        if not self.github_config.token:
            env_token = os.environ.get("GITHUB_TOKEN")
            if env_token:
                self.github_config.token = env_token
                logger.info("GitHub token loaded from GITHUB_TOKEN environment variable")
        if self.github_config.enabled:
            logger.info(f"GitHub integration enabled: {self.github_config.owner}/{self.github_config.repo}")
        self._setup_tools(provider)
        self._provider = provider

    async def load_skill_markdown(self, skill_name: str) -> Optional[str]:
        """Load SKILL.md content preferring GitHub (with TTL cache), falling back to local unless strict."""
        if self.github_config.enabled:
            content = await self._fetch_github_skill_content(skill_name)
            if content:
                return content

        if os.getenv("DIFFY_GITHUB_ONLY_SKILLS", "false").lower() == "true":
            return None

        for root_dir in [
            Path(__file__).parent / "skills",
            Path("./skills"),
            Path("/app/skills"),
            Path("/home/ubuntu/fluai-stack/diffy/skills"),
        ]:
            skill_file = root_dir / skill_name / "SKILL.md"
            if skill_file.is_file():
                try:
                    return skill_file.read_text(encoding="utf-8")
                except Exception:
                    pass
        return None

    async def _fetch_github_skills_list(self) -> List[Dict[str, str]]:
        """Fetch list of skills from GitHub API (with 1h cache)"""
        import time
        now = time.time()
        if _github_skills_cache["data"] and (now - _github_skills_cache["timestamp"] < 3600):
            return _github_skills_cache["data"]

        gh = self.github_config
        api_url = f"https://api.github.com/repos/{gh.owner}/{gh.repo}/contents/{gh.path}"
        params = {"ref": gh.branch}
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if gh.token:
            headers["Authorization"] = f"Bearer {gh.token}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(api_url, params=params, headers=headers)
                resp.raise_for_status()
                items = resp.json()

            skills = []
            for item in items:
                if item.get("type") == "dir":
                    skill_name = item["name"]
                    skills.append({"name": skill_name, "description": f"Skill: {skill_name} (from GitHub)", "source": "github"})
            _github_skills_cache["timestamp"] = now
            _github_skills_cache["data"] = skills
            return skills
        except Exception as e:
            logger.warning(f"GitHub skills fetch failed: {e}")
            return _github_skills_cache["data"] or []

    async def _fetch_github_skill_content(self, skill_name: str) -> Optional[str]:
        """Fetch SKILL.md content from GitHub for a specific skill (TTL-cached)."""
        now = time.time()
        cached_entry = _github_content_cache.get(skill_name)
        if cached_entry and (now - cached_entry.get("timestamp", 0.0) < GITHUB_CONTENT_CACHE_TTL):
            return cached_entry.get("content")

        gh = self.github_config
        api_url = f"https://api.github.com/repos/{gh.owner}/{gh.repo}/contents/{gh.path}/{skill_name}/SKILL.md"
        params = {"ref": gh.branch}
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if gh.token:
            headers["Authorization"] = f"Bearer {gh.token}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(api_url, params=params, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                download_url = data.get("download_url", "")
                if download_url:
                    content_resp = await client.get(download_url)
                    content = content_resp.text
                    _github_content_cache[skill_name] = {"timestamp": now, "content": content}
                    return content
        except Exception as e:
            logger.warning(f"GitHub skill content fetch failed for '{skill_name}': {e}")
            if cached_entry:
                return cached_entry.get("content")
        return None

    async def _fetch_github_skill_files(self, skill_name: str) -> List[str]:
        """Fetch file list for a skill from GitHub"""
        gh = self.github_config
        api_url = f"https://api.github.com/repos/{gh.owner}/{gh.repo}/contents/{gh.path}/{skill_name}"
        params = {"ref": gh.branch}
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if gh.token:
            headers["Authorization"] = f"Bearer {gh.token}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(api_url, params=params, headers=headers)
                resp.raise_for_status()
                items = resp.json()
                return [item["name"] for item in items if item.get("type") == "file"]
        except Exception as e:
            logger.warning(f"GitHub skill files fetch failed for '{skill_name}': {e}")
        return []

    def _setup_tools(self, provider):
        @self.mcp.tool()
        async def list_skills() -> List[Dict[str, str]]:
            """List all available skills from local directories and GitHub."""
            skills = {}
            SKILL_DIRS = [
                Path(__file__).parent / "skills",
                Path("./skills"),
                Path("/app/skills"),
                Path("/home/ubuntu/fluai-stack/diffy/skills"),
                Path("C:/Users/pawan/Downloads/diffy-main/diffy-main/skills"),
                Path("C:/Users/pawan/Downloads/diffy-main/skills"),
            ]
            for root_dir in SKILL_DIRS:
                if root_dir.is_dir():
                    for item in root_dir.iterdir():
                        if item.is_dir() and (item / "SKILL.md").is_file():
                            name = item.name
                            desc = f"Skill: {name}"
                            try:
                                txt = (item / "SKILL.md").read_text(encoding="utf-8")
                                if txt.startswith("---"):
                                    end = txt.find("---", 3)
                                    if end != -1:
                                        for line in txt[3:end].splitlines():
                                            if line.strip().startswith("description:"):
                                                desc = line.split("description:", 1)[1].strip()
                                                break
                            except Exception:
                                pass
                            skills[name] = {"description": desc, "source": "local"}

            try:
                resources = await provider.list_resources()
                res_list = list(resources) if hasattr(resources, "__iter__") else []
                for r in res_list:
                    uri = str(r.uri)
                    if uri.endswith("/SKILL.md"):
                        skill_name = uri.split("skill://")[1].split("/")[0]
                        if skill_name not in skills:
                            skills[skill_name] = {"description": r.description or f"Skill: {skill_name}", "source": "local"}
            except Exception as e:
                logger.warning(f"Error querying provider resources: {e}")

            if self.github_config.enabled:
                github_skills = await self._fetch_github_skills_list()
                for s in github_skills:
                    if s["name"] not in skills:
                        skills[s["name"]] = {"description": s["description"], "source": "github"}

            return [{"name": n, "description": v["description"], "source": v["source"]} for n, v in skills.items()]

        @self.mcp.tool()
        async def get_skill(skill_name: str) -> str:
            """Get skill content by name. Checks local first, then GitHub."""
            for root_dir in [
                Path(__file__).parent / "skills",
                Path("./skills"),
                Path("/app/skills"),
                Path("/home/ubuntu/fluai-stack/diffy/skills"),
                Path("C:/Users/pawan/Downloads/diffy-main/diffy-main/skills"),
                Path("C:/Users/pawan/Downloads/diffy-main/skills"),
            ]:
                skill_file = root_dir / skill_name / "SKILL.md"
                if skill_file.is_file():
                    try:
                        return skill_file.read_text(encoding="utf-8")
                    except Exception:
                        pass

            uri = f"skill://{skill_name}/SKILL.md"
            try:
                resource = await provider.get_resource(uri)
                if hasattr(resource, "read"):
                    content = await resource.read()
                    if content:
                        return content
            except Exception:
                pass

            if self.github_config.enabled:
                content = await self._fetch_github_skill_content(skill_name)
                if content:
                    return content

            return (
                f"SKILL_NOT_FOUND: '{skill_name}' does not exist in local or GitHub. "
                "STOP HERE. Do NOT answer from your general knowledge. "
                "Reply to the user with exactly this message: i have not record with your answer"
            )

        @self.mcp.tool()
        async def list_skill_files(skill_name: str) -> List[str]:
            """List all files in a skill (checks local first, then GitHub)."""
            for root_dir in [
                Path(__file__).parent / "skills",
                Path("./skills"),
                Path("/app/skills"),
                Path("/home/ubuntu/fluai-stack/diffy/skills"),
                Path("C:/Users/pawan/Downloads/diffy-main/diffy-main/skills"),
                Path("C:/Users/pawan/Downloads/diffy-main/skills"),
            ]:
                skill_dir = root_dir / skill_name
                if skill_dir.is_dir():
                    try:
                        return [p.name for p in skill_dir.iterdir() if p.is_file()]
                    except Exception:
                        pass

            try:
                resources = await provider.list_resources()
                files = []
                res_list = list(resources) if hasattr(resources, "__iter__") else []
                for r in res_list:
                    uri = str(r.uri)
                    if uri.startswith(f"skill://{skill_name}/"):
                        files.append(uri.split(f"skill://{skill_name}/")[1])
                if files:
                    return files
            except Exception:
                pass

            if self.github_config.enabled:
                return await self._fetch_github_skill_files(skill_name)

            return []

        analyzer = ProblemAnalyzer()
        skill_router = DynamicSkillRouter(registry=get_skill_registry())

        @self.mcp.tool()
        async def understand_human_problem(
            user_input: str,
            conversation_history: Optional[List[Dict[str, Any]]] = None,
        ) -> Dict[str, Any]:
            """Understand the user's human situation across multiple dimensions (domains, emotions, patterns, intentions, safety) before selecting skills."""
            analysis = analyzer.analyze(user_input, conversation_history)
            return analysis.model_dump()

        @self.mcp.tool()
        async def route_skills(
            analysis: Dict[str, Any],
            query_hint: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Intelligently route and chain relevant skills (Tier 1 core conversation, Tier 2 domain knowledge, Tier 3 playbooks, Tier 4 safety) based on problem analysis."""
            routed = skill_router.route(analysis, query_hint)
            return routed.model_dump()

        logger.info("Skills tools added successfully")
        logger.info(
            "Registered tools: list_skills, get_skill, list_skill_files, understand_human_problem, route_skills"
        )

    def run(self):
        logger.info("Starting FastMCP Skills Provider Server")
        try:
            self.mcp.run()
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)
            sys.exit(1)


# ─── Base System Instruction (served via /get-base-instruction) ───────────────
DEFAULT_SKILLS_USER_PROMPT = """\
[INSTRUCTION: You have access to a dynamic skills library via MCP tools (list_skills, get_skill, list_skill_files). For every user request, first discover available skills with list_skills, select relevant skills, and retrieve instructions with get_skill before answering. If no skill matches or get_skill returns SKILL_NOT_FOUND, reply strictly with: "i have not record with your answer". Never answer from general knowledge when no skill matches.]
""".strip()


BASE_SYSTEM_INSTRUCTION = """\
You are an intelligent, empathetic, and human-centered AI assistant with access to a dynamic skills library via MCP tools.

You have MCP tools available:
1. understand_human_problem — Understand the user's situation across life domains, emotions, patterns, intentions, and safety indicators.
2. route_skills — Dynamically select and chain relevant skills based on the problem analysis.
3. list_skills — Discover all available skills.
4. get_skill — Retrieve detailed instructions for a specific skill.
5. list_skill_files — See all files within a skill.

## Human-Centered Conversation Principles:
- Listen before advising: Always acknowledge and validate the user's expressed feelings with warmth and patience.
- Understand context before proposing solutions; ask a clarifying question when situation details are missing.
- Never judge, criticize, or blame any party involved.
- Never pretend to literally feel human emotions, and never claim to be a licensed therapist, doctor, lawyer, or emergency service.
- When safety risks (self-harm, domestic violence, child endangerment, immediate danger) are indicated, prioritize safe, non-judgmental support and official helpline options; NEVER suggest joint mediation where physical abuse or intimidation is present.

## Safe Fallback Strategy:
- When a user query does not match any specialized domain skill, provide compassionate foundational human support and thoughtful exploratory clarification. Do NOT invent missing knowledge or make up false skills.
- Always respond in the same language the user is writing in (English, Hindi, or Hinglish).
""".strip()


async def health_endpoint(request: Request):
    """Health check endpoint reporting server + Neon Postgres memory readiness."""
    mem = get_memory_manager()
    return JSONResponse({
        "status": "ok",
        "message": "Diffy Agent API & Skills MCP Server is running",
        "postgres_configured": mem.enabled,
    })


async def cache_refresh_endpoint(request: Request):
    """Invalidate GitHub skill caches so updated skills load immediately."""
    _github_skills_cache["timestamp"] = 0.0
    _github_skills_cache["data"] = []
    _github_content_cache.clear()
    return JSONResponse({"status": "ok", "message": "GitHub skill caches cleared"})


def _resolve_request_identity(request: Request, payload: Dict[str, Any], resolved_device: Optional[Dict[str, Any]] = None) -> tuple[str, str, str]:
    """Resolve canonical (user_id, session_id, channel) from BFF/gateway headers only."""
    if resolved_device:
        user_id = resolved_device["user_id"]
        channel = "speaker"
        session_id = request.headers.get("x-session-id") or payload.get("session_id") or f"{user_id}:speaker"
        return user_id, str(session_id), channel

    webui_uid = request.headers.get("x-openwebui-user-id", "").strip()
    if webui_uid:
        chat_id = request.headers.get("x-openwebui-chat-id", "").strip()
        session_id = chat_id or payload.get("session_id") or f"{webui_uid}:app"
        return webui_uid, str(session_id), "app"

    eval_uid = request.headers.get("x-eval-user-id", "").strip()
    if eval_uid:
        session_id = request.headers.get("x-session-id") or payload.get("session_id") or f"{eval_uid}:eval"
        return eval_uid, str(session_id), "eval"

    channel = request.headers.get("x-channel", "").strip() or payload.get("channel") or "app"
    raw_user = str(payload.get("user") or "").strip()
    if raw_user and raw_user != "default_user" and channel == "eval":
        return raw_user, str(payload.get("session_id") or f"{raw_user}:eval"), "eval"

    return "anonymous", str(payload.get("session_id") or f"anon:{uuid.uuid4().hex[:8]}"), str(channel)


def build_http_app(server_instance: SkillsProviderServer):
    """Build the unified Starlette app serving /mcp + Agent API (/v1/*) + /health."""
    mem = get_memory_manager()
    orchestrator = get_agent_orchestrator(skill_loader=server_instance.load_skill_markdown)

    async def v1_models_endpoint(request: Request):
        return JSONResponse({
            "object": "list",
            "data": [
                {
                    "id": "diffy-agent",
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "diffy-agent",
                    "name": "Aether Human-Centered Agent (Diffy)",
                }
            ],
        })

    async def v1_chat_completions_endpoint(request: Request):
        try:
            payload = await request.json()
        except Exception:
            return JSONResponse({"error": {"message": "Invalid JSON body"}}, status_code=400)

        resolved_device = None
        dev_token = request.headers.get("x-device-token", "").strip()
        auth_hdr = request.headers.get("authorization", "").strip()
        if not dev_token and auth_hdr.startswith("Bearer fluai_dev_"):
            dev_token = auth_hdr[7:].strip()

        if dev_token:
            resolved_device = await mem.resolve_device_user(dev_token)
            if not resolved_device:
                return JSONResponse({"error": {"message": "Invalid or revoked device token"}}, status_code=401)

        user_id, session_id, channel = _resolve_request_identity(request, payload, resolved_device=resolved_device)
        result = await orchestrator.handle_chat_completion(
            payload=payload,
            user_id=user_id,
            session_id=session_id,
            channel=channel,
        )

        if payload.get("stream"):
            content = result["choices"][0]["message"]["content"]
            cmpl_id = result["id"]
            created = result["created"]
            model = result["model"]

            async def sse_gen():
                chunk = {
                    "id": cmpl_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model,
                    "choices": [{"index": 0, "delta": {"role": "assistant", "content": content}, "finish_reason": None}],
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                stop_chunk = {
                    "id": cmpl_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                }
                yield f"data: {json.dumps(stop_chunk)}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(sse_gen(), media_type="text/event-stream")

        return JSONResponse(result)

    async def v1_devices_pair_endpoint(request: Request):
        try:
            payload = await request.json()
        except Exception:
            return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

        device_id = str(payload.get("device_id") or "").strip()
        user_id = str(payload.get("user_id") or request.headers.get("x-openwebui-user-id", "")).strip()
        device_name = str(payload.get("device_name") or "ESP32 Speaker").strip()
        if not device_id or not user_id or user_id == "default_user":
            return JSONResponse({"error": "device_id and authenticated user_id are required"}, status_code=400)
        try:
            paired = await mem.pair_device(device_id=device_id, user_id=user_id, device_name=device_name)
            return JSONResponse({"status": "paired", **paired})
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    async def v1_devices_resolve_endpoint(request: Request):
        try:
            payload = await request.json()
        except Exception:
            return JSONResponse({"error": "Invalid JSON body"}, status_code=400)
        token = str(payload.get("device_token") or request.headers.get("x-device-token", "")).strip()
        if not token:
            return JSONResponse({"error": "device_token required"}, status_code=400)
        resolved = await mem.resolve_device_user(token)
        if not resolved:
            return JSONResponse({"error": "Unknown or inactive device token"}, status_code=401)
        return JSONResponse({"status": "ok", **resolved, "paired_at": str(resolved.get("paired_at", ""))})

    mcp_app = server_instance.mcp.http_app(path="/mcp")
    from starlette.routing import Route as StarletteRoute

    mcp_route = next((r for r in mcp_app.router.routes if getattr(r, "path", "") == "/mcp"), None)
    if mcp_route:
        mcp_app.router.routes.append(
            StarletteRoute("/mcp/", endpoint=mcp_route.endpoint, methods=["GET", "POST", "DELETE", "HEAD", "OPTIONS"])
        )
    custom_routes = [
        StarletteRoute("/health", health_endpoint, methods=["GET"]),
        StarletteRoute("/get-base-instruction", get_base_instruction_endpoint, methods=["GET"]),
        StarletteRoute("/get-default-user-prompt", get_default_user_prompt_endpoint, methods=["GET"]),
        StarletteRoute("/admin/cache/refresh", cache_refresh_endpoint, methods=["POST"]),
        StarletteRoute("/v1/models", v1_models_endpoint, methods=["GET"]),
        StarletteRoute("/v1/chat/completions", v1_chat_completions_endpoint, methods=["POST"]),
        StarletteRoute("/v1/devices/pair", v1_devices_pair_endpoint, methods=["POST"]),
        StarletteRoute("/v1/devices/resolve", v1_devices_resolve_endpoint, methods=["POST"]),
    ]
    for idx, rt in enumerate(custom_routes):
        mcp_app.router.routes.insert(idx, rt)

    mcp_app.add_middleware(ApiKeyMiddleware)
    return mcp_app


async def get_default_user_prompt_endpoint(request: Request):
    """Returns the default user prompt prefix as plain text for appending to user queries."""
    return PlainTextResponse(DEFAULT_SKILLS_USER_PROMPT)


async def get_base_instruction_endpoint(request: Request):
    """Returns the full base system instruction as plain text for Dify's system prompt.
    Dify HTTP node calls GET /get-base-instruction.
    Select {x}body in the LLM SYSTEM prompt — it directly contains the instruction text.
    """
    return PlainTextResponse(BASE_SYSTEM_INSTRUCTION)


def run_http_server(config_file: str, port: int, gateway_url: str = None):
    """Run MCP server with HTTP transport for gateway.
    Also serves /health and /get-base-instruction for Dify integration.
    """
    server_instance = SkillsProviderServer(config_file)

    logger.info(f"Starting FastMCP Skills Provider with streamable-http transport")
    logger.info(f"Port: {port}")
    logger.info(f"Endpoint: http://0.0.0.0:{port}/mcp")
    logger.info(f"Instruction API: http://0.0.0.0:{port}/get-base-instruction")
    logger.info(f"Health check:    http://0.0.0.0:{port}/health")

    # Start heartbeat thread to keep server visible to gateway
    config_loader = ConfigLoader(config_file)
    gateway_config = config_loader.get_gateway_config()
    if gateway_config.enabled:
        gateway_host = gateway_config.host or "localhost"
        gateway_port_num = gateway_config.port or 8000
        server_name = gateway_config.name or "skills-provider"

        def heartbeat_loop():
            """Send periodic heartbeats to the gateway"""
            gw_url = f"http://{gateway_host}:{gateway_port_num}/heartbeat"
            while True:
                try:
                    response = httpx.get(
                        gw_url, params={"server_name": server_name}, timeout=5.0
                    )
                    if response.status_code == 200:
                        logger.debug(f"Heartbeat sent to gateway ({server_name})")
                    else:
                        logger.warning(f"Gateway heartbeat failed: {response.status_code}")
                except Exception as e:
                    logger.warning(f"Heartbeat error: {e}")
                finally:
                    time.sleep(15)

        heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        logger.info(f"Heartbeat thread started (gateway: {gateway_host}:{gateway_port_num})")

    mcp_app = build_http_app(server_instance)
    logger.info("Custom routes injected: /health, /v1/models, /v1/chat/completions, /v1/devices/pair")
    if os.getenv("MCP_API_KEY", "").strip():
        logger.info("HTTP bearer authentication enabled")
    else:
        logger.warning("MCP_API_KEY is not set; HTTP endpoints are unauthenticated")
    uvicorn.run(mcp_app, host="0.0.0.0", port=port)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="FastMCP Skills Provider Server")
    parser.add_argument("--config", default="skills.settings.json")
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--http", action="store_true")
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args()

    if args.init:
        ConfigLoader.create_default_config(args.config)
        sys.exit(0)

    try:
        config_loader = ConfigLoader(args.config)
        use_http = args.http
        if not use_http and config_loader.get_gateway_config().enabled:
            logger.info("Gateway enabled in config - switching to HTTP transport")
            use_http = True

        # Use provided port, OR environment PORT (for cloud platforms), OR fall back to config port
        env_port = os.environ.get("PORT")
        if env_port and not args.port:
            http_port = int(env_port)
        else:
            http_port = args.port or config_loader.get_http_config().port

        if use_http:
            run_http_server(args.config, http_port)
        else:
            server = SkillsProviderServer(args.config)
            server.run()
    except FileNotFoundError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
