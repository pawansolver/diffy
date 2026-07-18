"""
Instruction API - Simple backend server
Fetches SKILL.md content and returns it as a clean system prompt.
No LLM integration - Dify's own LLM will be used.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("instruction_api")

app = FastAPI(title="Skills Instruction API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SKILLS_DIR = Path(os.getenv("SKILLS_DIR", "./skills")).resolve()


# ─── Base System Instruction ──────────────────────────────────────────────────
# This is the instruction that was previously entered manually in Dify's
# Instructions box. It now lives in the backend — Dify's box stays empty.

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
- Always check available skills before answering complex questions
- If a relevant skill exists, follow its exact instructions and output format
- If no skill matches, answer using your general knowledge
- Never make up skill names — only use skills returned by list_skills tool
- Always respond in the same language the user is writing in
""".strip()


# ─── Request / Response Models ────────────────────────────────────────────────

class InstructionRequest(BaseModel):
    skill: str  # e.g. "documentation-skill"

class InstructionResponse(BaseModel):
    instruction: str   # Clean SKILL.md content (ready to use as system prompt)
    skill: str
    source: str        # "local" or "github"

class BaseInstructionResponse(BaseModel):
    instruction: str   # Full base system prompt that replaces Dify's instruction box


# ─── Skill Loaders ────────────────────────────────────────────────────────────

def load_local_skill(skill_name: str) -> Optional[str]:
    """Read SKILL.md from local ./skills/{skill_name}/SKILL.md"""
    path = SKILLS_DIR / skill_name / "SKILL.md"
    if path.exists():
        logger.info(f"Local skill found: {path}")
        return path.read_text(encoding="utf-8")
    return None


async def load_github_skill(skill_name: str) -> Optional[str]:
    """Fetch SKILL.md from GitHub repository (uses skills.settings.json config)"""
    config_path = Path("skills.settings.json")
    if not config_path.exists():
        return None

    with open(config_path, "r") as f:
        config = json.load(f)

    gh = config.get("github", {})
    if not gh.get("enabled", False):
        return None

    owner  = gh.get("owner", "")
    repo   = gh.get("repo", "")
    path   = gh.get("path", "").strip("/")
    branch = gh.get("branch", "main")
    token  = os.getenv("GITHUB_TOKEN") or gh.get("token")

    if not owner or not repo:
        return None

    # Build the SKILL.md path inside the repo
    skill_path = f"{path}/{skill_name}/SKILL.md" if path else f"{skill_name}/SKILL.md"
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{skill_path}"

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(api_url, params={"ref": branch}, headers=headers)
            if resp.status_code != 200:
                logger.warning(f"GitHub API returned {resp.status_code} for skill '{skill_name}'")
                return None

            download_url = resp.json().get("download_url")
            if not download_url:
                return None

            content_resp = await client.get(download_url)
            if content_resp.status_code == 200:
                logger.info(f"GitHub skill fetched: {skill_name}")
                return content_resp.text
    except Exception as e:
        logger.error(f"GitHub fetch error for '{skill_name}': {e}")

    return None


def clean_frontmatter(content: str) -> str:
    """Strip YAML frontmatter (--- ... ---) from SKILL.md and return clean content"""
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            return content[end + 3:].strip()
    return content.strip()


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "message": "Instruction API is running"}


@app.get("/get-base-instruction", response_model=BaseInstructionResponse)
def get_base_instruction():
    """
    Returns the full base system instruction that was previously entered
    manually in Dify's Instructions box.

    Dify Setup:
      1. Create an HTTP Request node that calls GET /get-base-instruction.
      2. Inject the response `instruction` field into the Agent System Prompt:
             {{#http_node.body.instruction#}}
      3. Leave the Instructions box empty.
    """
    return BaseInstructionResponse(instruction=BASE_SYSTEM_INSTRUCTION)


@app.post("/get-instruction", response_model=InstructionResponse)
async def get_instruction(request: InstructionRequest):
    """
    Provide a skill name → receive the clean SKILL.md content.
    Checks local directory first, then falls back to GitHub.

    Dify Setup:
      Inject the response `instruction` field into the LLM node System Prompt:
          {{#http_node.body.instruction#}}
    """
    skill_name = request.skill.strip()
    source = "local"

    # 1. Try loading from local directory
    content = load_local_skill(skill_name)

    # 2. If not found locally, fall back to GitHub
    if not content:
        content = await load_github_skill(skill_name)
        source = "github"

    if not content:
        raise HTTPException(
            status_code=404,
            detail=f"Skill '{skill_name}' not found — neither locally nor on GitHub."
        )

    # Strip frontmatter and return clean instruction
    clean_instruction = clean_frontmatter(content)

    return InstructionResponse(
        instruction=clean_instruction,
        skill=skill_name,
        source=source,
    )


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("INSTRUCTION_API_PORT", 8001))
    logger.info(f"Starting Instruction API on port {port}")
    uvicorn.run("instruction_api:app", host="0.0.0.0", port=port, reload=True)
