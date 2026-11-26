"""Pydantic validated data models for Human Problem Taxonomy, Understanding and Skill Routing."""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProblemUnderstanding(BaseModel):
    summary: str = Field(..., description="Neutral factual summary of the user's presented situation")
    domains: List[str] = Field(default_factory=list, description="Relevant life domains identified (can be multiple)")
    people_involved: List[str] = Field(default_factory=list, description="Parties and relational roles involved")
    problem_patterns: List[str] = Field(default_factory=list, description="Relational and cognitive patterns detected")
    emotional_signals: List[str] = Field(default_factory=list, description="Explicit and implicit affective states")
    user_intention: List[str] = Field(default_factory=list, description="Pragmatic communication intent of the user")
    contextual_factors: List[str] = Field(default_factory=list, description="Temporal, living, or structural constraints")


class SafetyAssessment(BaseModel):
    potential_risk: bool = Field(default=False, description="Flag indicating potential physical or psychiatric risk")
    risk_categories: List[str] = Field(default_factory=list, description="Categories of risk (self_harm, domestic_violence, etc.)")
    requires_safe_followup: bool = Field(default=False, description="Mandates specialized supportive response protocol")
    reason: Optional[str] = Field(default=None, description="Conservative explanation of detected risk indicators")


class ConfidenceMetrics(BaseModel):
    overall: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall understanding reliability index")
    classification: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence in primary domain classification")


class HumanProblemAnalysis(BaseModel):
    """Complete structured output contract for understand_human_problem."""
    understanding: ProblemUnderstanding
    safety: SafetyAssessment
    confidence: ConfidenceMetrics
    uncertainty: List[str] = Field(default_factory=list, description="Explicit points of ambiguity or incomplete data")
    needs_clarification: bool = Field(default=False, description="Whether clarifying question is required before action")
    clarification_question: Optional[str] = Field(default=None, description="Gentle, non-judgmental exploratory question")


class SelectedSkill(BaseModel):
    skill_id: str = Field(..., description="Unique kebab-case identifier of the selected skill")
    tier: str = Field(..., description="Logical tier: core_conversation, domain_knowledge, scenario_playbook, safety_boundary")
    selection_reason: str = Field(..., description="Transparent rationale explaining why this skill was selected")
    source_path: str = Field(..., description="File path or virtual source of the skill instructions")
    version: str = Field(default="1.0.0", description="Semantic version of the skill metadata")


class RetrievalMetadata(BaseModel):
    total_selected: int = Field(default=0, ge=0, description="Number of skills chained in this response")
    selection_method: List[str] = Field(default_factory=list, description="Methods used (taxonomy_match, safety_precedence, etc.)")
    warnings: List[str] = Field(default_factory=list, description="Operational warnings (budget exceeded, fallback used, etc.)")


class RouteSkillsResponse(BaseModel):
    """Complete structured output contract for route_skills."""
    problem_summary: str = Field(..., description="Summary of the analyzed human problem")
    selected_skills: List[SelectedSkill] = Field(default_factory=list, description="Ordered chained skills for execution")
    safety_guidance: List[str] = Field(default_factory=list, description="Specialized safety directives taking precedence")
    clarification_required: bool = Field(default=False, description="Whether response should pause for user clarification")
    retrieval_metadata: RetrievalMetadata
