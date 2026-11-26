"""Unit tests for Human Problem Taxonomy configuration, data models, and Skill Registry."""

import json
import unittest
from pathlib import Path

from router.registry import SkillMetadata, SkillRegistry, get_skill_registry
from router.taxonomy import (
    ConfidenceMetrics,
    HumanProblemAnalysis,
    ProblemUnderstanding,
    RetrievalMetadata,
    RouteSkillsResponse,
    SafetyAssessment,
    SelectedSkill,
)


class TestTaxonomyModelsAndConfig(unittest.TestCase):
    """Verifies taxonomy schemas, data validation, and configuration file integrity."""

    def setUp(self):
        self.config_path = Path(__file__).resolve().parent.parent / "router" / "taxonomy_config.json"

    def test_taxonomy_config_structure(self):
        self.assertTrue(self.config_path.is_file(), f"Taxonomy config missing at {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        required_keys = [
            "life_domains",
            "people_involved",
            "problem_patterns",
            "emotional_signals",
            "user_intentions",
            "safety_indicators",
        ]
        for key in required_keys:
            self.assertIn(key, config, f"Missing required top-level key '{key}' in taxonomy config")
            self.assertIsInstance(config[key], dict)
            self.assertGreater(len(config[key]), 0, f"Section '{key}' must have at least one entry")

        # Verify keywords exist for life domains
        for domain, d_data in config["life_domains"].items():
            if domain != "other_or_unknown":
                self.assertIn("keywords", d_data)
                self.assertGreater(len(d_data["keywords"]), 0)

    def test_pydantic_problem_understanding(self):
        understanding = ProblemUnderstanding(
            summary="User reports marital conflict",
            domains=["marriage_and_relationships"],
            people_involved=["spouse"],
            problem_patterns=["communication_breakdown"],
            emotional_signals=["frustration", "sadness"],
            user_intention=["seeking_guidance"],
            contextual_factors=["stressful_work"],
        )
        self.assertEqual(understanding.summary, "User reports marital conflict")
        self.assertEqual(len(understanding.domains), 1)
        self.assertEqual(understanding.domains[0], "marriage_and_relationships")
        d = understanding.model_dump()
        self.assertIn("summary", d)
        self.assertIn("emotional_signals", d)

    def test_pydantic_safety_assessment(self):
        safe = SafetyAssessment()
        self.assertFalse(safe.potential_risk)
        self.assertEqual(len(safe.risk_categories), 0)

        risk = SafetyAssessment(
            potential_risk=True,
            risk_categories=["self_harm"],
            requires_safe_followup=True,
            reason="Explicit crisis indicator",
        )
        self.assertTrue(risk.potential_risk)
        self.assertIn("self_harm", risk.risk_categories)
        self.assertTrue(risk.requires_safe_followup)

    def test_pydantic_confidence_bounds(self):
        c = ConfidenceMetrics(overall=0.85, classification=0.90)
        self.assertAlmostEqual(c.overall, 0.85)

        # Invalid bounds should raise ValidationError
        with self.assertRaises(Exception):
            ConfidenceMetrics(overall=1.5, classification=0.5)
        with self.assertRaises(Exception):
            ConfidenceMetrics(overall=-0.1, classification=0.5)

    def test_pydantic_route_skills_response(self):
        resp = RouteSkillsResponse(
            problem_summary="Test problem",
            selected_skills=[
                SelectedSkill(
                    skill_id="misapplication-ethics",
                    tier="safety_boundary",
                    selection_reason="Safety protocol",
                    source_path="skills/misapplication-ethics/SKILL.md",
                    version="1.0.0",
                )
            ],
            safety_guidance=["Provide crisis contacts"],
            clarification_required=False,
            retrieval_metadata=RetrievalMetadata(
                total_selected=1,
                selection_method=["safety_precedence"],
                warnings=[],
            ),
        )
        self.assertEqual(resp.problem_summary, "Test problem")
        self.assertEqual(len(resp.selected_skills), 1)
        self.assertEqual(resp.selected_skills[0].skill_id, "misapplication-ethics")
        self.assertEqual(resp.retrieval_metadata.total_selected, 1)


class TestSkillRegistry(unittest.TestCase):
    """Verifies SkillRegistry scanning, tier mapping, and fallback behavior."""

    def setUp(self):
        self.registry = get_skill_registry()

    def test_all_18_skills_loaded(self):
        skills = self.registry.list_skills(enabled_only=False)
        self.assertGreaterEqual(len(skills), 18, f"Expected at least 18 skills, found {len(skills)}")

    def test_tier_distribution(self):
        # Tier 1: Core Conversation
        t1 = self.registry.get_skills_by_tier("tier_1_core_conversation")
        t1_ids = {s.skill_id for s in t1}
        self.assertIn("documentation-skill", t1_ids)
        self.assertIn("context-evaluation-framework", t1_ids)
        self.assertIn("etar-framework", t1_ids)
        self.assertIn("gendered-communication-personalization", t1_ids)

        # Tier 2: Domain Knowledge
        t2 = self.registry.get_skills_by_tier("tier_2_domain_knowledge")
        t2_ids = {s.skill_id for s in t2}
        self.assertIn("vyavastha-typology-feedback-loops", t2_ids)
        self.assertIn("child-development-sequence", t2_ids)
        self.assertIn("feminine-masculine-dimensional-dynamics", t2_ids)

        # Tier 3: Scenario Playbooks
        t3 = self.registry.get_skills_by_tier("tier_3_scenario_playbooks")
        t3_ids = {s.skill_id for s in t3}
        self.assertIn("residential-community-harmony", t3_ids)
        self.assertIn("intergenerational-joint-family", t3_ids)
        self.assertIn("civic-dialogue-consensus", t3_ids)

        # Tier 4: Safety & Ethical Boundaries
        t4 = self.registry.get_skills_by_tier("tier_4_safety_boundaries")
        t4_ids = {s.skill_id for s in t4}
        self.assertIn("misapplication-ethics", t4_ids)
        safety_skill = self.registry.get_skill("misapplication-ethics")
        self.assertIsNotNone(safety_skill)
        self.assertTrue(safety_skill.safety_critical)

    def test_domain_filtering(self):
        marriage_skills = self.registry.get_skills_for_domain("marriage_and_relationships")
        marriage_ids = {s.skill_id for s in marriage_skills}
        self.assertIn("feminine-masculine-dimensional-dynamics", marriage_ids)

        family_skills = self.registry.get_skills_for_domain("joint_family")
        family_ids = {s.skill_id for s in family_skills}
        self.assertIn("intergenerational-joint-family", family_ids)

        community_skills = self.registry.get_skills_for_domain("residential_communities")
        community_ids = {s.skill_id for s in community_skills}
        self.assertIn("residential-community-harmony", community_ids)

    def test_source_path_files_exist(self):
        root = Path(__file__).resolve().parent.parent
        for s in self.registry.list_skills():
            file_path = root / s.source_path
            self.assertTrue(file_path.is_file(), f"Skill file for {s.skill_id} does not exist at {file_path}")

    def test_missing_metadata_graceful_fallback(self):
        # Create a temporary empty registry with non-existent metadata file
        dummy_meta_path = Path(__file__).resolve().parent / "dummy_empty_meta.json"
        reg = SkillRegistry(metadata_path=dummy_meta_path)
        # Should have scanned skills and defaulted them without failing
        skills = reg.list_skills()
        self.assertGreaterEqual(len(skills), 18)
        self.assertGreater(len(reg.get_missing_metadata_warnings()), 0)
        # Ensure default tier is domain_knowledge
        first = skills[0]
        self.assertEqual(first.tier, "domain_knowledge")


if __name__ == "__main__":
    unittest.main()
