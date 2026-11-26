"""Unit tests for Human Problem Understanding Engine, Dynamic Skill Router, and MCP tools."""

import asyncio
import json
import unittest

from main import SkillsProviderServer
from router.analyzer import ProblemAnalyzer, understand_human_problem
from router.skill_router import DynamicSkillRouter, route_skills
from router.taxonomy import HumanProblemAnalysis, RouteSkillsResponse


class TestProblemUnderstandingEngine(unittest.TestCase):
    """Verifies multilingual understanding, compound domains, emotions, intentions, and safety."""

    def setUp(self):
        self.analyzer = ProblemAnalyzer()

    def test_english_marital_conflict(self):
        text = "My wife and I have been constantly arguing about finances and household responsibilities."
        analysis = self.analyzer.analyze(text)
        self.assertIsInstance(analysis, HumanProblemAnalysis)
        self.assertIn("marriage_and_relationships", analysis.understanding.domains)
        self.assertIn("spouse_partner", analysis.understanding.people_involved)
        self.assertFalse(analysis.safety.potential_risk)
        self.assertFalse(analysis.needs_clarification)

    def test_hindi_joint_family_conflict(self):
        text = "मेरी सास और मेरी पत्नी के बीच में बहुत झगड़ा हो रहा है, मैं बीच में पिस रहा हूँ और बहुत परेशान हूँ।"
        analysis = self.analyzer.analyze(text)
        self.assertIsInstance(analysis, HumanProblemAnalysis)
        # Should identify joint_family or marriage
        self.assertTrue(
            "joint_family" in analysis.understanding.domains
            or "marriage_and_relationships" in analysis.understanding.domains
        )
        self.assertTrue(
            "anxious_overwhelm" in analysis.understanding.emotional_signals
            or "helpless_exhaustion" in analysis.understanding.emotional_signals
            or "defensive_anger" in analysis.understanding.emotional_signals
        )
        self.assertFalse(analysis.safety.potential_risk)

    def test_hinglish_workplace_toxicity(self):
        text = "Office me boss bahut toxic behave kar raha hai, promotion cancel kar diya aur sabke samne insult kiya."
        analysis = self.analyzer.analyze(text)
        self.assertIsInstance(analysis, HumanProblemAnalysis)
        self.assertIn("workplace_relationships", analysis.understanding.domains)
        self.assertIn("coworkers_boss", analysis.understanding.people_involved)
        self.assertTrue(
            "defensive_anger" in analysis.understanding.emotional_signals
            or "unacknowledged_hurt" in analysis.understanding.emotional_signals
        )

    def test_compound_domain_detection(self):
        text = (
            "My teenage child is failing school and getting aggressive with gaming, "
            "and my husband blames me completely while our savings are running out."
        )
        analysis = self.analyzer.analyze(text)
        domains = analysis.understanding.domains
        self.assertGreaterEqual(len(domains), 2, "Compound scenario must detect at least two life domains")
        self.assertTrue("parenting" in domains or "parent_child_conflicts" in domains)
        self.assertTrue("marriage_and_relationships" in domains or "financial_and_social_pressure" in domains)

    def test_intention_differentiation(self):
        vent_text = "I don't need any solutions or advice right now, I just really need someone to listen to me vent."
        analysis_vent = self.analyzer.analyze(vent_text)
        self.assertIn("venting_and_containment", analysis_vent.understanding.user_intention)

        action_text = "What is the exact step-by-step strategy and legal procedure to handle this boundary dispute?"
        analysis_action = self.analyzer.analyze(action_text)
        self.assertTrue(
            "concrete_action_strategy" in analysis_action.understanding.user_intention
            or "seeking_clarity" in analysis_action.understanding.user_intention
        )

    def test_brief_ambiguous_input_triggers_clarification(self):
        vague_inputs = [
            "I feel so bad",
            "kuch theek nahi lag raha",
            "Help me",
            "Everything is falling apart",
        ]
        for inp in vague_inputs:
            analysis = self.analyzer.analyze(inp)
            self.assertTrue(analysis.needs_clarification, f"Expected clarification for vague input: {inp}")
            self.assertIsNotNone(analysis.clarification_question)
            self.assertGreater(len(analysis.uncertainty), 0)

    def test_self_harm_safety_flag(self):
        text = "I can't take this pain anymore, I feel like ending my life tonight."
        analysis = self.analyzer.analyze(text)
        self.assertTrue(analysis.safety.potential_risk)
        self.assertIn("self_harm", analysis.safety.risk_categories)
        self.assertTrue(analysis.safety.requires_safe_followup)

    def test_domestic_violence_safety_flag(self):
        text = "My husband hit me yesterday, threw things at me, and threatened to hurt me if I talk to anyone."
        analysis = self.analyzer.analyze(text)
        self.assertTrue(analysis.safety.potential_risk)
        self.assertIn("domestic_violence", analysis.safety.risk_categories)
        self.assertTrue(analysis.safety.requires_safe_followup)

    def test_child_safeguarding_safety_flag(self):
        text = "A neighbor is brutally beating their 7 year old child with a belt every evening."
        analysis = self.analyzer.analyze(text)
        self.assertTrue(analysis.safety.potential_risk)
        self.assertIn("child_safeguarding", analysis.safety.risk_categories)


class TestDynamicSkillRouter(unittest.TestCase):
    """Verifies safety precedence, playbook selection, budget enforcement, and fallback."""

    def setUp(self):
        self.analyzer = ProblemAnalyzer()
        self.router = DynamicSkillRouter(max_budget=4)

    def test_safety_precedence_domestic_violence(self):
        text = "My husband physically hit me and threatened to kill me if I ask for a divorce."
        analysis = self.analyzer.analyze(text)
        route_resp = self.router.route(analysis)

        self.assertIsInstance(route_resp, RouteSkillsResponse)
        # Must include misapplication-ethics
        skill_ids = [s.skill_id for s in route_resp.selected_skills]
        self.assertIn("misapplication-ethics", skill_ids)

        # Must include explicit non-joint-mediation safety guidance
        has_dv_directive = any("Do NOT recommend joint mediation" in g for g in route_resp.safety_guidance)
        self.assertTrue(has_dv_directive, "Safety guidance must explicitly forbid joint mediation in DV cases")

    def test_safety_precedence_self_harm(self):
        text = "Mujhe lagta hai mai mar jau, koi meri kadar nahi karta, I want to kill myself."
        analysis = self.analyzer.analyze(text)
        route_resp = self.router.route(analysis)

        skill_ids = [s.skill_id for s in route_resp.selected_skills]
        self.assertIn("misapplication-ethics", skill_ids)
        # Check helpline directive
        has_helpline = any("helpline" in g.lower() or "tele-manas" in g.lower() for g in route_resp.safety_guidance)
        self.assertTrue(has_helpline, "Safety guidance must include helpline references for crisis")

    def test_residential_community_playbook_routing(self):
        text = "Our housing society residents are fighting over basement parking allocations and maintenance dues."
        analysis = self.analyzer.analyze(text)
        route_resp = self.router.route(analysis)

        skill_ids = [s.skill_id for s in route_resp.selected_skills]
        self.assertIn("residential-community-harmony", skill_ids)
        # Core conversation tier should be included
        tiers = [s.tier for s in route_resp.selected_skills]
        self.assertIn("core_conversation", tiers)

    def test_civic_dialogue_playbook_routing(self):
        text = "Local political party workers in our municipal ward are shouting during the public townhall meeting."
        analysis = self.analyzer.analyze(text)
        route_resp = self.router.route(analysis)

        skill_ids = [s.skill_id for s in route_resp.selected_skills]
        self.assertIn("civic-dialogue-consensus", skill_ids)

    def test_budget_enforcement(self):
        # A complex compound scenario that touches multiple domains
        text = (
            "In our joint family, my in-laws interfere with my marriage, our residential society committee "
            "is penalizing us for parking, my son is failing school, and our political ward leader is threatening us."
        )
        analysis = self.analyzer.analyze(text)
        route_resp = self.router.route(analysis)

        self.assertLessEqual(
            len(route_resp.selected_skills),
            4,
            f"Skill count {len(route_resp.selected_skills)} exceeded budget limit 4",
        )
        self.assertEqual(route_resp.retrieval_metadata.total_selected, len(route_resp.selected_skills))

    def test_unknown_domain_fallback(self):
        analysis = self.analyzer.analyze("Subatomic tachyon fluctuations inside the quantum vacuum reactor are collapsing my hyperdrive.")
        # When unclassified and ambiguous, clarification is appropriately required
        if analysis.needs_clarification:
            route_resp = self.router.route(analysis)
            self.assertTrue(route_resp.clarification_required)

        # When evaluated for execution without clarification, falls back to Vyavastha
        analysis.needs_clarification = False
        route_resp = self.router.route(analysis)
        skill_ids = [s.skill_id for s in route_resp.selected_skills]
        self.assertIn("vyavastha-typology-feedback-loops", skill_ids)
        self.assertIn("fallback_to_vyavastha", route_resp.retrieval_metadata.selection_method)


class TestFastMCPIntegrationAndBackwardCompatibility(unittest.TestCase):
    """Verifies FastMCP tools, JSON contracts, and backward compatibility."""

    def setUp(self):
        self.server = SkillsProviderServer()

    def test_understand_human_problem_tool(self):
        # 1. Test standalone helper
        analysis = understand_human_problem(
            user_input="My husband and I are having severe arguments over household expenses.",
            conversation_history=[],
        )
        self.assertIsInstance(analysis, HumanProblemAnalysis)
        self.assertIn("marriage_and_relationships", analysis.understanding.domains)

        # 2. Test FastMCP tool invocation
        tool_res = asyncio.run(
            self.server.mcp.call_tool(
                "understand_human_problem",
                {"user_input": "My husband and I are having severe arguments over household expenses."}
            )
        )
        self.assertIsNotNone(tool_res.structured_content)
        self.assertIn("understanding", tool_res.structured_content)
        self.assertIn("safety", tool_res.structured_content)

    def test_route_skills_tool(self):
        analysis = understand_human_problem(
            user_input="Joint family elders constantly criticize how we raise our daughter.",
        )
        # 1. Test standalone helper
        routed = route_skills(analysis=analysis)
        self.assertIsInstance(routed, RouteSkillsResponse)
        self.assertGreater(len(routed.selected_skills), 0)

        # 2. Test FastMCP tool invocation
        tool_res = asyncio.run(
            self.server.mcp.call_tool(
                "route_skills",
                {"analysis": analysis.model_dump()}
            )
        )
        self.assertIsNotNone(tool_res.structured_content)
        self.assertIn("problem_summary", tool_res.structured_content)
        self.assertIn("selected_skills", tool_res.structured_content)

    def test_backward_compatibility_list_skills(self):
        result = asyncio.run(self.server.mcp.call_tool("list_skills"))
        text_out = str(result)
        self.assertTrue("documentation-skill" in text_out or any("documentation-skill" in str(c) for c in result.content))

    def test_backward_compatibility_get_skill(self):
        result = asyncio.run(self.server.mcp.call_tool("get_skill", {"skill_name": "residential-community-harmony"}))
        text = result.content[0].text if result.content else ""
        self.assertIn("residential-community-harmony", text)

    def test_backward_compatibility_missing_skill_prefix(self):
        # ProductSpeaker depends on "SKILL_NOT_FOUND:" prefix
        result = asyncio.run(self.server.mcp.call_tool("get_skill", {"skill_name": "non-existent-skill-xyz"}))
        text = result.content[0].text if result.content else ""
        self.assertTrue(text.startswith("SKILL_NOT_FOUND:"))
        self.assertIn("non-existent-skill-xyz", text)


if __name__ == "__main__":
    unittest.main()
