"""FastMCP Skills Provider Server"""

import asyncio
import logging
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from fastmcp import FastMCP
from fastmcp.server.providers.skills import SkillsDirectoryProvider
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
import uvicorn

from config import ConfigLoader, GithubConfig

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SkillsProviderServer:
    """FastMCP Skills Provider Server"""

    def __init__(self, config_file: str = "skills.settings.json"):
        self.config_loader = ConfigLoader(config_file)
        self.mcp = FastMCP("Skills Provider")
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

    async def _fetch_github_skills_list(self) -> List[Dict[str, str]]:
        """Fetch list of skills from GitHub API"""
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
                    # Try to get description from SKILL.md frontmatter
                    desc = await self._fetch_github_skill_description(skill_name)
                    skills.append({"name": skill_name, "description": desc, "source": "github"})
            return skills
        except Exception as e:
            logger.warning(f"GitHub skills fetch failed: {e}")
            return []

    async def _fetch_github_skill_description(self, skill_name: str) -> str:
        """Fetch description from SKILL.md frontmatter in GitHub"""
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
                    # Parse YAML frontmatter for description
                    if content.startswith("---"):
                        end = content.find("---", 3)
                        if end != -1:
                            frontmatter = content[3:end]
                            for line in frontmatter.splitlines():
                                if line.strip().startswith("description:"):
                                    return line.split("description:", 1)[1].strip()
                    # Fallback: use skill name
                    return f"Skill: {skill_name} (from GitHub)"
        except Exception:
            pass
        return f"Skill: {skill_name} (from GitHub)"

    async def _fetch_github_skill_content(self, skill_name: str) -> Optional[str]:
        """Fetch SKILL.md content from GitHub for a specific skill"""
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
                    return content_resp.text
        except Exception as e:
            logger.warning(f"GitHub skill content fetch failed for '{skill_name}': {e}")
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
            """List all available skills from local directories and GitHub.

            Returns a list of all skills from configured local directories
            and optionally from a configured GitHub repository.
            """
            # 1. Get local skills
            resources = await provider.list_resources()
            skills = {}
            res_list = list(resources) if hasattr(resources, "__iter__") else []
            for r in res_list:
                uri = str(r.uri)
                if uri.endswith("/SKILL.md"):
                    skill_name = uri.split("skill://")[1].split("/")[0]
                    skills[skill_name] = {"description": r.description or f"Skill: {skill_name}", "source": "local"}

            # 2. Merge GitHub skills (if enabled)
            if self.github_config.enabled:
                github_skills = await self._fetch_github_skills_list()
                for s in github_skills:
                    if s["name"] not in skills:  # Local takes priority
                        skills[s["name"]] = {"description": s["description"], "source": "github"}

            return [{"name": n, "description": v["description"], "source": v["source"]} for n, v in skills.items()]

        @self.mcp.tool()
        async def get_skill(skill_name: str) -> str:
            """Get skill content by name. Checks local first, then GitHub."""
            # 1. Try local first
            uri = f"skill://{skill_name}/SKILL.md"
            try:
                resource = await provider.get_resource(uri)
                if hasattr(resource, "read"):
                    content = await resource.read()
                    if content:
                        return content
            except Exception:
                pass

            # 2. Try GitHub if enabled
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
            """List all files in a skill (checks local first, then GitHub).

            Args:
                skill_name: The name of the skill
            """
            # 1. Try local
            resources = await provider.list_resources()
            files = []
            res_list = list(resources) if hasattr(resources, "__iter__") else []
            for r in res_list:
                uri = str(r.uri)
                if uri.startswith(f"skill://{skill_name}/"):
                    files.append(uri.split(f"skill://{skill_name}/")[1])

            # 2. If not found locally and GitHub is enabled, try GitHub
            if not files and self.github_config.enabled:
                files = await self._fetch_github_skill_files(skill_name)

            return files

        logger.info("Skills tools added successfully")
        logger.info(f"Registered tools: list_skills, get_skill, list_skill_files")

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
BASE_SYSTEM_INSTRUCTION = """\
You are an intelligent AI assistant with access to a dynamic skills library via MCP tools.

You have 3 tools available:
1. list_skills — Use this to discover all available skills
2. get_skill — Use this to retrieve detailed instructions for a specific skill
3. list_skill_files — Use this to see all files within a skill

## How to use skills:
- When a user asks something that matches a skill topic, FIRST call list_skills to see what skills are available
- Then call get_skill with the relevant skill name to load the full instructions
- Follow the skill's instructions precisely when responding

## Behavior Rules:
- ALWAYS call list_skills before answering ANY question
- If a relevant skill exists, follow its exact instructions and output format
- If get_skill returns SKILL_NOT_FOUND or no skill matches — you are STRICTLY FORBIDDEN from using your general knowledge
- When no skill is found, you MUST reply with ONLY this exact text: i have not record with your answer
- DO NOT add any explanation, apology, or extra text when no skill is found
- Never make up skill names — only use skills returned by list_skills tool
- Always respond in the same language the user is writing in
""".strip()


async def health_endpoint(request: Request):
    """Health check endpoint"""
    return JSONResponse({"status": "ok", "message": "Skills MCP Server is running"})


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

    # Get FastMCP's own Starlette app and inject our custom routes into it
    # This preserves all lifespan handlers that FastMCP sets up internally
    mcp_app = server_instance.mcp.http_app(path="/mcp")

    # Inject custom routes at the front so they take priority
    from starlette.routing import Route as StarletteRoute
    mcp_app.router.routes.insert(0, StarletteRoute("/health", health_endpoint, methods=["GET"]))
    mcp_app.router.routes.insert(1, StarletteRoute("/get-base-instruction", get_base_instruction_endpoint, methods=["GET"]))

    logger.info("Custom routes injected: /health, /get-base-instruction")
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
