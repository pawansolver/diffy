"""Dynamic Skill Routing Engine for Diffy FastMCP.

Chains Tier 1 (Core Conversation), Tier 2 (Domain Knowledge), Tier 3 (Scenario Playbooks),
and Tier 4 (Safety Boundaries) with safety precedence, retrieval budgeting, and traceability.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union

from router.registry import SkillRegistry, get_skill_registry
from router.taxonomy import (
    HumanProblemAnalysis,
    RetrievalMetadata,
    RouteSkillsResponse,
    SelectedSkill,
)

logger = logging.getLogger("diffy.router.skill_router")


class DynamicSkillRouter:
    """Intelligently routes and chains skills based on HumanProblemAnalysis."""

    def __init__(self, registry: Optional[SkillRegistry] = None, max_budget: int = 4):
        self.registry = registry or get_skill_registry()
        self.max_budget = max_budget

    def route(
        self,
        analysis: Union[HumanProblemAnalysis, Dict[str, Any]],
        query_hint: Optional[str] = None,
    ) -> RouteSkillsResponse:
        # Validate schema
        if isinstance(analysis, dict):
            try:
                analysis = HumanProblemAnalysis(**analysis)
            except Exception as e:
                logger.warning(f"Failed parsing analysis dict: {e}")
                # Create fallback analysis
                from router.analyzer import ProblemAnalyzer
                analyzer = ProblemAnalyzer()
                analysis = analyzer.analyze(query_hint or "Unspecified situation")

        selected: List[SelectedSkill] = []
        selected_ids: set[str] = set()
        safety_guidance: List[str] = []
        selection_methods: List[str] = []
        warnings: List[str] = []

        summary = analysis.understanding.summary
        domains = analysis.understanding.domains
        emotions = analysis.understanding.emotional_signals
        patterns = analysis.understanding.problem_patterns
        safety = analysis.safety

        # STEP 1: SAFETY PRECEDENCE (Tier 4)
        if safety.potential_risk:
            selection_methods.append("safety_precedence")
            safety_skill = self.registry.get_skill("misapplication-ethics")
            if safety_skill and safety_skill.enabled:
                selected.append(
                    SelectedSkill(
                        skill_id=safety_skill.skill_id,
                        tier="safety_boundary",
                        selection_reason=f"Mandatory safety protocol activated for risk: {', '.join(safety.risk_categories)}",
                        source_path=safety_skill.source_path,
                        version=safety_skill.version,
                    )
                )
                selected_ids.add(safety_skill.skill_id)

            # Generate explicit, non-coercive safety guidance
            for cat in safety.risk_categories:
                if cat == "domestic_violence":
                    safety_guidance.append(
                        "CRITICAL DOMESTIC SAFETY DIRECTIVE: Do NOT recommend joint mediation or shared "
                        "conflict resolution when domestic abuse or intimidation is reported. Provide private, "
                        "confidential support and encourage consulting trusted local professionals or helplines."
                    )
                elif cat == "self_harm":
                    safety_guidance.append(
                        "CRITICAL CRISIS SUPPORT DIRECTIVE: Listen with calm, non-judgmental empathy. "
                        "Do not debate, judge, or provide superficial cheerleading. Provide immediate crisis "
                        "helpline options (e.g. Tele-MANAS: 14416 / 1800-891-4416 or Vandrevala: 9999 666 555) "
                        "and encourage speaking to a professional or trusted loved one."
                    )
                elif cat == "child_safeguarding":
                    safety_guidance.append(
                        "CHILD SAFEGUARDING DIRECTIVE: Prioritize the immediate physical and psychological safety "
                        "of the minor. Do not justify severe physical punishment or abusive practices."
                    )
                elif cat == "threats_and_immediate_danger":
                    safety_guidance.append(
                        "IMMEDIATE DANGER DIRECTIVE: Refuse to facilitate or encourage violence. "
                        "Encourage physical safety distance and de-escalation."
                    )

            # In acute safety crises, limit further non-essential skill chaining
            if "self_harm" in safety.risk_categories or "domestic_violence" in safety.risk_categories:
                return RouteSkillsResponse(
                    problem_summary=summary,
                    selected_skills=selected,
                    safety_guidance=safety_guidance,
                    clarification_required=False,
                    retrieval_metadata=RetrievalMetadata(
                        total_selected=len(selected),
                        selection_method=selection_methods,
                        warnings=warnings,
                    ),
                )

        # STEP 2: CLARIFICATION CHECK
        if analysis.needs_clarification:
            return RouteSkillsResponse(
                problem_summary=summary,
                selected_skills=[],
                safety_guidance=[],
                clarification_required=True,
                retrieval_metadata=RetrievalMetadata(
                    total_selected=0,
                    selection_method=["clarification_pause"],
                    warnings=["Context insufficient for prescriptive skill selection."],
                ),
            )

        # STEP 3: TIER 3 (SCENARIO PLAYBOOKS) - Direct Scenario Match
        playbooks = self.registry.get_skills_by_tier("scenario_playbook")
        for p in playbooks:
            if len(selected) >= self.max_budget:
                break
            if p.skill_id in selected_ids or not p.enabled:
                continue

            # Match against domains and patterns
            matching_domains = set(p.domains).intersection(set(domains))
            matching_patterns = set(p.problem_patterns).intersection(set(patterns))

            if matching_domains or matching_patterns:
                reason = (
                    f"Selected playbook for domain: {', '.join(matching_domains) or ', '.join(matching_patterns)}"
                )
                selected.append(
                    SelectedSkill(
                        skill_id=p.skill_id,
                        tier="scenario_playbook",
                        selection_reason=reason,
                        source_path=p.source_path,
                        version=p.version,
                    )
                )
                selected_ids.add(p.skill_id)
                selection_methods.append("playbook_match")

        # STEP 4: TIER 2 (DOMAIN KNOWLEDGE SKILLS)
        domain_skills = self.registry.get_skills_by_tier("domain_knowledge")
        for d in domain_skills:
            if len(selected) >= self.max_budget:
                break
            if d.skill_id in selected_ids or not d.enabled:
                continue

            matching_domains = set(d.domains).intersection(set(domains))
            matching_patterns = set(d.problem_patterns).intersection(set(patterns))

            if matching_domains or matching_patterns:
                reason = f"Domain guidance for {', '.join(matching_domains) or ', '.join(matching_patterns)}"
                selected.append(
                    SelectedSkill(
                        skill_id=d.skill_id,
                        tier="domain_knowledge",
                        selection_reason=reason,
                        source_path=d.source_path,
                        version=d.version,
                    )
                )
                selected_ids.add(d.skill_id)
                selection_methods.append("domain_match")

        # STEP 5: TIER 1 (CORE CONVERSATION SKILLS) - Pacing & Validation
        core_skills = self.registry.get_skills_by_tier("core_conversation")
        for c in core_skills:
            if len(selected) >= self.max_budget:
                break
            if c.skill_id in selected_ids or not c.enabled:
                continue

            # Match ETAR for anger/reactive patterns, or context-evaluation for complex situations
            if "defensive_anger" in emotions and c.skill_id == "etar-framework":
                selected.append(
                    SelectedSkill(
                        skill_id=c.skill_id,
                        tier="core_conversation",
                        selection_reason="Cognitive loop deconstruction for anger and emotional reactivity",
                        source_path=c.source_path,
                        version=c.version,
                    )
                )
                selected_ids.add(c.skill_id)
                selection_methods.append("core_conversation_match")
            elif c.skill_id == "context-evaluation-framework" and len(domains) > 1:
                selected.append(
                    SelectedSkill(
                        skill_id=c.skill_id,
                        tier="core_conversation",
                        selection_reason="Multi-layered contextual assessment for compound situation",
                        source_path=c.source_path,
                        version=c.version,
                    )
                )
                selected_ids.add(c.skill_id)
                selection_methods.append("core_conversation_match")

        # STEP 6: FALLBACK HANDLING FOR UNKNOWN / UNCLASSIFIED SITUATIONS
        if not selected:
            selection_methods.append("empathetic_fallback")
            warnings.append("No specialized domain playbook matched. Provided Vyavastha foundational guidance.")
            fallback = self.registry.get_skill("vyavastha-typology-feedback-loops")
            if fallback and fallback.enabled:
                selected.append(
                    SelectedSkill(
                        skill_id=fallback.skill_id,
                        tier="domain_knowledge",
                        selection_reason="Foundational co-existential harmony guidance for unclassified situation",
                        source_path=fallback.source_path,
                        version=fallback.version,
                    )
                )
                selected_ids.add(fallback.skill_id)

        return RouteSkillsResponse(
            problem_summary=summary,
            selected_skills=selected,
            safety_guidance=safety_guidance,
            clarification_required=False,
            retrieval_metadata=RetrievalMetadata(
                total_selected=len(selected),
                selection_method=list(set(selection_methods)),
                warnings=warnings,
            ),
        )


_global_router: Optional[DynamicSkillRouter] = None


def get_dynamic_skill_router() -> DynamicSkillRouter:
    global _global_router
    if _global_router is None:
        _global_router = DynamicSkillRouter()
    return _global_router

