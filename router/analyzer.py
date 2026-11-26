"""Human Problem Understanding Engine for Diffy FastMCP.

Analyzes user input across 7 dimensions (Life domains, People involved, Problem patterns,
Emotional signals, User intentions, Severity/Safety, and Context) with multilingual support
(English, Hindi, Hinglish), compound problem handling, and uncertainty preservation.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from router.taxonomy import (
    ConfidenceMetrics,
    HumanProblemAnalysis,
    ProblemUnderstanding,
    SafetyAssessment,
)

logger = logging.getLogger("diffy.router.analyzer")
TAXONOMY_CONFIG_PATH = Path(__file__).resolve().parent / "taxonomy_config.json"


class ProblemAnalyzer:
    """Understands human problems deterministically using multilingual pattern analysis."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or TAXONOMY_CONFIG_PATH
        self.config: Dict[str, Any] = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.is_file():
            logger.error(f"Taxonomy config missing at {self.config_path}")
            return {}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading taxonomy config: {e}")
            return {}

    def _normalize_text(self, text: str) -> str:
        t = text.lower().strip()
        t = re.sub(r"[^\w\s\u0900-\u097F]", " ", t)
        return " " + re.sub(r"\s+", " ", t) + " "

    def analyze(
        self,
        user_input: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> HumanProblemAnalysis:
        raw_text = (user_input or "").strip()
        norm_text = self._normalize_text(raw_text)

        # 1. Safety Triage (Precedence Step)
        safety = self._assess_safety(norm_text)

        # 2. People Involved
        people = self._extract_people(norm_text)

        # 3. Life Domains (Compound Detection)
        domains, domain_scores = self._extract_domains(norm_text, people)

        # 4. Problem Patterns
        patterns = self._extract_patterns(norm_text)

        # 5. Emotional Signals
        emotions = self._extract_emotions(norm_text)

        # 6. User Intention
        intentions = self._extract_intentions(norm_text, safety)

        # 7. Contextual Factors
        context = self._extract_context(norm_text, raw_text, conversation_history)

        # 8. Ambiguity & Clarification Assessment
        needs_clarification, clarification_question, uncertainty = self._evaluate_clarification(
            raw_text, norm_text, domains, emotions, safety
        )

        # 9. Confidence Calculation
        confidence = self._compute_confidence(
            raw_text, domains, domain_scores, emotions, needs_clarification
        )

        # 10. Neutral Objective Summary
        summary = self._generate_neutral_summary(raw_text, domains, people, emotions)

        understanding = ProblemUnderstanding(
            summary=summary,
            domains=domains,
            people_involved=people,
            problem_patterns=patterns,
            emotional_signals=emotions,
            user_intention=intentions,
            contextual_factors=context,
        )

        return HumanProblemAnalysis(
            understanding=understanding,
            safety=safety,
            confidence=confidence,
            uncertainty=uncertainty,
            needs_clarification=needs_clarification,
            clarification_question=clarification_question,
        )

    def _assess_safety(self, norm_text: str) -> SafetyAssessment:
        safety_cfg = self.config.get("safety_indicators", {})
        risk_categories = []
        reasons = []

        for category, details in safety_cfg.items():
            keywords = details.get("keywords", [])
            for kw in keywords:
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, norm_text):
                    if category not in risk_categories:
                        risk_categories.append(category)
                        reasons.append(f"Detected safety indicator matching '{kw}'")
                    break

        if risk_categories:
            return SafetyAssessment(
                potential_risk=True,
                risk_categories=risk_categories,
                requires_safe_followup=True,
                reason="; ".join(reasons),
            )

        return SafetyAssessment(
            potential_risk=False,
            risk_categories=[],
            requires_safe_followup=False,
            reason=None,
        )

    def _extract_domains(self, norm_text: str, people: List[str]) -> Tuple[List[str], Dict[str, int]]:
        domains_cfg = self.config.get("life_domains", {})
        scores: Dict[str, int] = {}

        for domain, info in domains_cfg.items():
            if domain == "other_or_unknown":
                continue
            count = 0
            for kw in info.get("keywords", []):
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, norm_text):
                    count += 1
            if count > 0:
                scores[domain] = count

        # Contextual domain inferences based on entities
        if "spouse_partner" in people and "marriage_and_relationships" not in scores:
            scores["marriage_and_relationships"] = scores.get("marriage_and_relationships", 0) + 1
        if "child_teenager" in people and "parent_child_conflicts" not in scores and "parenting" not in scores:
            scores["parent_child_conflicts"] = scores.get("parent_child_conflicts", 0) + 1
        if "in_laws" in people and "joint_family" not in scores:
            scores["joint_family"] = scores.get("joint_family", 0) + 1
        if "neighbors_community" in people and "residential_communities" not in scores:
            scores["residential_communities"] = scores.get("residential_communities", 0) + 1

        if not scores:
            return ["other_or_unknown"], {}

        # Sort by match score
        sorted_domains = sorted(scores.keys(), key=lambda d: scores[d], reverse=True)
        # Support compound domains (keep domains with score >= 1 up to top 3)
        top_domains = [d for d in sorted_domains if scores[d] >= 1][:3]
        return top_domains, scores

    def _extract_people(self, norm_text: str) -> List[str]:
        people_cfg = self.config.get("people_involved", {})
        results = []
        for role, kws in people_cfg.items():
            for kw in kws:
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, norm_text):
                    if role not in results:
                        results.append(role)
                    break
        if not results:
            results.append("self_individual")
        return results

    def _extract_patterns(self, norm_text: str) -> List[str]:
        patterns_cfg = self.config.get("problem_patterns", {})
        results = []
        for pattern_id, info in patterns_cfg.items():
            for kw in info.get("keywords", []):
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, norm_text):
                    if pattern_id not in results:
                        results.append(pattern_id)
                    break
        return results

    def _extract_emotions(self, norm_text: str) -> List[str]:
        emotions_cfg = self.config.get("emotional_signals", {})
        results = []
        for emotion, kws in emotions_cfg.items():
            for kw in kws:
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, norm_text):
                    if emotion not in results:
                        results.append(emotion)
                    break
        return results

    def _extract_intentions(self, norm_text: str, safety: SafetyAssessment) -> List[str]:
        if safety.potential_risk:
            return ["crisis_support"]

        intentions_cfg = self.config.get("user_intentions", {})
        results = []
        for intent, kws in intentions_cfg.items():
            for kw in kws:
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, norm_text):
                    if intent not in results:
                        results.append(intent)
                    break

        if not results:
            results.append("seeking_clarity")
        return results

    def _extract_context(
        self,
        norm_text: str,
        raw_text: str,
        history: Optional[List[Dict[str, Any]]],
    ) -> List[str]:
        factors = []
        if any(w in norm_text for w in [" aaj ", " today ", " right now ", " kal ", " yesterday "]):
            factors.append("acute_temporal_trigger")
        if any(w in norm_text for w in [" hamesha ", " always ", " roz roz ", " years ", " mahino se "]):
            factors.append("chronic_recurring_friction")
        if any(w in norm_text for w in [" flat ", " society ", " ghar ", " room ", " pados "]):
            factors.append("shared_physical_proximity")
        if any(w in norm_text for w in [" paisa ", " debt ", " property ", " batwara "]):
            factors.append("financial_interdependence")
        if history and len(history) > 1:
            factors.append(f"multi_turn_history_available ({len(history)} turns)")
        return factors

    def _evaluate_clarification(
        self,
        raw_text: str,
        norm_text: str,
        domains: List[str],
        emotions: List[str],
        safety: SafetyAssessment,
    ) -> Tuple[bool, Optional[str], List[str]]:
        uncertainty = []

        # If safety risk is acute, prioritize direct safety protocol over open-ended clarification
        if safety.potential_risk:
            return False, None, ["safety_protocol_precedence"]

        word_count = len(raw_text.split())
        is_very_brief = word_count <= 4
        is_unknown_domain = "other_or_unknown" in domains

        if is_very_brief:
            uncertainty.append("input_is_extremely_brief")
        if is_unknown_domain:
            uncertainty.append("specific_life_domain_unclear")
        if not emotions:
            uncertainty.append("emotional_affect_not_explicitly_stated")

        if is_very_brief or (is_unknown_domain and not emotions):
            clarification = (
                "Main aapki baat ko theek se samajhna chahta hoon. "
                "Kya aap thoda aur bata sakte hain ki kya hua aur isse aap par kya asar pad raha hai?"
            )
            return True, clarification, uncertainty

        return False, None, uncertainty

    def _compute_confidence(
        self,
        raw_text: str,
        domains: List[str],
        domain_scores: Dict[str, int],
        emotions: List[str],
        needs_clarification: bool,
    ) -> ConfidenceMetrics:
        if needs_clarification:
            return ConfidenceMetrics(overall=0.35, classification=0.30)

        if "other_or_unknown" in domains:
            return ConfidenceMetrics(overall=0.50, classification=0.40)

        top_score = max(domain_scores.values()) if domain_scores else 0
        classification_conf = min(0.95, 0.60 + (top_score * 0.10))
        overall_conf = classification_conf if emotions else max(0.55, classification_conf - 0.15)

        return ConfidenceMetrics(
            overall=round(overall_conf, 2),
            classification=round(classification_conf, 2),
        )

    def _generate_neutral_summary(
        self,
        raw_text: str,
        domains: List[str],
        people: List[str],
        emotions: List[str],
    ) -> str:
        domain_str = ", ".join(d.replace("_", " ") for d in domains)
        people_str = ", ".join(p.replace("_", " ") for p in people)
        emotion_str = f" with feelings of {', '.join(emotions)}" if emotions else ""

        if "other_or_unknown" in domains:
            return f"User described a personal situation: '{raw_text[:80]}...' requiring contextual exploration."

        return f"User reports interpersonal friction involving {people_str} in domain of {domain_str}{emotion_str}."

