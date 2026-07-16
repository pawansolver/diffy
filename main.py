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

            return f"Skill '{skill_name}' not found locally or on GitHub."

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


def run_http_server(config_file: str, port: int, gateway_url: str = None):
    """Run MCP server with HTTP transport for gateway"""
    server_instance = SkillsProviderServer(config_file)

    logger.info(f"Starting FastMCP Skills Provider with sse transport")
    logger.info(f"Port: {port}")
    logger.info(f"Endpoint: http://localhost:{port}/sse")
    logger.info(f"Tools configured:")
    logger.info(f"  - list_skills: List all available skills")
    logger.info(f"  - get_skill: Get skill content by name")
    logger.info(f"  - list_skill_files: List all files in a skill")
    logger.info(
        f"Register with gateway: transport=streamable-http, url=http://localhost:{port}/mcp"
    )

    # Start heartbeat thread to keep server visible to gateway
    config_loader = ConfigLoader(config_file)
    gateway_config = config_loader.get_gateway_config()
    if gateway_config.enabled:
        gateway_host = gateway_config.host or "localhost"
        gateway_port = gateway_config.port or 8000
        server_name = gateway_config.name or "skills-provider"

        def heartbeat_loop():
            """Send periodic heartbeats to the gateway"""
            gateway_url = f"http://{gateway_host}:{gateway_port}/heartbeat"
            while True:
                try:
                    # Send heartbeat every 15 seconds (well under 30 second timeout)
                    response = httpx.get(
                        gateway_url, params={"server_name": server_name}, timeout=5.0
                    )
                    if response.status_code == 200:
                        logger.debug(f"Heartbeat sent to gateway ({server_name})")
                    else:
                        logger.warning(
                            f"Gateway heartbeat failed: {response.status_code}"
                        )
                except Exception as e:
                    logger.warning(f"Heartbeat error: {e}")
                finally:
                    time.sleep(15)  # Send heartbeat every 15 seconds

        # Start heartbeat thread as daemon so it doesn't block server shutdown
        heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        logger.info(
            f"Heartbeat thread started (gateway: {gateway_host}:{gateway_port}, server: {server_name})"
        )

    # Use streamable-http transport which is compatible with MCP gateways
    server_instance.mcp.run(transport="streamable-http", host="0.0.0.0", port=port)


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
