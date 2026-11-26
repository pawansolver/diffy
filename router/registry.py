"""Skill Registry for Diffy FastMCP.

Loads and organizes existing skills into 4 logical tiers without physically moving folders:
- Tier 1: Core Conversation Skills
- Tier 2: Domain Knowledge Skills
- Tier 3: Scenario Playbooks
- Tier 4: Safety & Ethical Boundary Skills
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("diffy.router.registry")

ROOT_DIR = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT_DIR / "skills"
METADATA_FILE = Path(__file__).resolve().parent / "skills_metadata.json"


class SkillMetadata(BaseModel):
    skill_id: str = Field(..., description="Unique kebab-case identifier")
    name: str = Field(..., description="Human-readable title")
    description: str = Field(..., description="Summary of skill purpose and methods")
    tier: str = Field(default="domain_knowledge", description="core_conversation | domain_knowledge | scenario_playbook | safety_boundary")
    domains: List[str] = Field(default_factory=list, description="Associated life domains")
    people_involved: List[str] = Field(default_factory=list, description="Parties/relationships addressed")
    problem_patterns: List[str] = Field(default_factory=list, description="Interpersonal patterns addressed")
    emotional_signals: List[str] = Field(default_factory=list, description="Target emotional states")
    supported_languages: List[str] = Field(default_factory=lambda: ["en", "hi", "hinglish"])
    applicability: str = Field(default="", description="When to activate this skill")
    contraindications: str = Field(default="", description="When NOT to activate this skill")
    safety_critical: bool = Field(default=False, description="Flag for mandatory safety protocols")
    priority: int = Field(default=50, description="Selection priority score (1-100)")
    source_path: str = Field(default="", description="Path to SKILL.md file on disk")
    version: str = Field(default="1.0.0", description="Skill version")
    enabled: bool = Field(default=True, description="Whether skill is active")


class SkillRegistry:
    """Thread-safe, non-invasive registry for all local FastMCP skills."""

    def __init__(self, metadata_path: Optional[Path] = None, skills_dir: Optional[Path] = None):
        self.metadata_path = metadata_path or METADATA_FILE
        self.skills_dir = skills_dir or SKILLS_DIR
        self._skills: Dict[str, SkillMetadata] = {}
        self._missing_metadata_warnings: List[str] = []
        self._load_registry()

    def _load_registry(self) -> None:
        raw_metadata: Dict[str, Any] = {}
        if self.metadata_path.is_file():
            try:
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    raw_metadata = data.get("skills", {})
            except Exception as e:
                logger.error(f"Failed loading metadata from {self.metadata_path}: {e}")

        # Scan all existing skill folders on disk
        if self.skills_dir.is_dir():
            for folder in self.skills_dir.iterdir():
                if folder.is_dir() and (folder / "SKILL.md").is_file():
                    skill_id = folder.name
                    skill_file = folder / "SKILL.md"

                    if skill_id in raw_metadata:
                        entry = raw_metadata[skill_id]
                        entry["source_path"] = str(skill_file.relative_to(ROOT_DIR)).replace("\\", "/")
                        self._skills[skill_id] = SkillMetadata(**entry)
                    else:
                        # Extract description from frontmatter if possible
                        desc = f"Skill: {skill_id}"
                        try:
                            txt = skill_file.read_text(encoding="utf-8")
                            if txt.startswith("---"):
                                end = txt.find("---", 3)
                                if end != -1:
                                    for line in txt[3:end].splitlines():
                                        if line.strip().startswith("description:"):
                                            desc = line.split("description:", 1)[1].strip()
                                            break
                        except Exception:
                            pass

                        warning_msg = f"Skill '{skill_id}' missing in metadata. Loaded with backward-compatible defaults."
                        self._missing_metadata_warnings.append(warning_msg)
                        logger.warning(warning_msg)

                        self._skills[skill_id] = SkillMetadata(
                            skill_id=skill_id,
                            name=skill_id.replace("-", " ").title(),
                            description=desc,
                            tier="domain_knowledge",
                            domains=["other_or_unknown"],
                            source_path=str(skill_file.relative_to(ROOT_DIR)).replace("\\", "/"),
                            version="1.0.0",
                            enabled=True,
                        )

    def get_skill(self, skill_id: str) -> Optional[SkillMetadata]:
        return self._skills.get(skill_id)

    def list_skills(
        self,
        tier: Optional[str] = None,
        domain: Optional[str] = None,
        enabled_only: bool = True,
    ) -> List[SkillMetadata]:
        results = []
        for s in self._skills.values():
            if enabled_only and not s.enabled:
                continue
            if tier and s.tier != tier:
                continue
            if domain and domain not in s.domains and "other_or_unknown" not in s.domains:
                continue
            results.append(s)
        return sorted(results, key=lambda x: x.priority, reverse=True)

    def get_skills_by_tier(self, tier: str) -> List[SkillMetadata]:
        return self.list_skills(tier=tier)

    def get_skills_by_domain(self, domain: str) -> List[SkillMetadata]:
        return self.list_skills(domain=domain)

    def get_skill_content(self, skill_id: str) -> Optional[str]:
        skill = self._skills.get(skill_id)
        if not skill:
            return None
        full_path = ROOT_DIR / skill.source_path
        if full_path.is_file():
            try:
                return full_path.read_text(encoding="utf-8")
            except Exception as e:
                logger.error(f"Error reading skill file {full_path}: {e}")
                return None
        return None

    @property
    def total_count(self) -> int:
        return len(self._skills)

    @property
    def missing_metadata_warnings(self) -> List[str]:
        return list(self._missing_metadata_warnings)


_global_registry: Optional[SkillRegistry] = None


def get_skill_registry() -> SkillRegistry:
    global _global_registry
    if _global_registry is None:
        _global_registry = SkillRegistry()
    return _global_registry

