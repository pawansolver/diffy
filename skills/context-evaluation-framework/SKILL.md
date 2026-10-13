---
name: context-evaluation-framework
description: Applies the Context Evaluation Framework (v4) to assess the relevance, appropriateness, and effectiveness of interventions, programs, or systems across four structured dimensions: Context, Need, Response, and Impact.
---

# Purpose

The Context Evaluation Framework (v4) is a structured assessment tool for evaluating whether an intervention, program, policy, or system is contextually relevant and effective. It uses four dimensions — Context, Need, Response, and Impact — to determine whether a given action or system correctly addresses an identified need within its environment and whether its outcomes are constructive or harmful.

The AI agent applying this skill must use this framework to produce structured evaluations that are evidence-grounded, contextually specific, and actionable. The output must help decision-makers understand whether an intervention is appropriate, whether it addresses the actual need, and whether its outcomes are aligned with the intended purpose.

---

# Scope

This skill applies to scenarios requiring:

- Evaluation of the relevance and fit of an educational, social, healthcare, or organizational intervention
- Assessment of whether a program or policy is addressing the actual need of the target population
- Diagnosis of why an intervention is failing or producing unintended consequences
- Design review of proposed systems or programs before implementation
- Post-implementation review of outcomes against intended goals
- Answering prompts that reference the Context Evaluation Framework by name

This skill does not apply to financial auditing, clinical diagnosis, or legal assessment.

---

# When to Use

Activate this skill when the user request involves:

- Evaluating whether a community program, educational initiative, or organizational system is working
- Identifying why an intervention is not achieving its intended outcome
- Assessing the fit between an identified need and the response deployed
- Designing evaluation criteria for a new or existing program
- Comparing two or more interventions on their contextual relevance and impact
- Answering prompts that ask to "apply the Contextual Evaluation Framework" or reference CEF v4

---

# When NOT to Use

Do not activate this skill when:

- The request is about individual-level behavioral analysis (use the ETAR Framework skill)
- The request requires certified program evaluation methodology with licensed measurement tools
- The intervention being evaluated has no described characteristics
- The user is asking about a theoretical or hypothetical intervention with no context provided
- The context is legal, forensic, or requires certified professional judgment

---

# Inputs

**Required:**
- A description of the intervention, program, policy, or system being evaluated
- A description of the environment or situation in which the intervention operates (Context)
- A description of the need the intervention is intended to address

**Expected context:**
- The population being served
- The goals of the intervention
- Any observed or reported outcomes

**Optional:**
- Existing data on outcomes or effectiveness
- Description of prior interventions in the same context
- Stakeholder perspectives or concerns
- Comparator interventions or alternative approaches

---

# Preconditions

Before executing this skill, verify the following:

1. The subject of evaluation is an intervention, program, policy, or system — not an individual person.
2. Sufficient information is available to describe at least the Context and Need dimensions.
3. The evaluation goal is constructive: improving effectiveness, identifying gaps, or guiding design.
4. Findings will not be used to defund, terminate, or penalize programs without acknowledgment of systemic factors.
5. No evaluation conclusion will be presented as definitive without qualification based on available information.

If any precondition fails, state which is unmet and what information is required.

---

# Core Concepts

## Dimension 1: Context

**Definition:** Context is the specific environment, situation, or set of conditions within which the intervention operates. It includes the physical setting, cultural dynamics, relational structures, historical background, power dynamics, and systemic factors that shape how the intervention is received and what constraints or enablers are present.

**Assessment criteria:**
- Is the environment safe or hostile for the intervention?
- What cultural, linguistic, or relational factors affect how the intervention is received?
- What historical patterns are relevant to understanding the current situation?
- What systemic constraints or enablers are present?
- What power dynamics are operating within the context?

**AI instruction:** Do not treat context as a neutral backdrop. Context is an active variable that determines whether an intervention can function as designed. A misread context is the most common cause of intervention failure.

---

## Dimension 2: Need

**Definition:** Need is the specific unmet requirement, gap, or emerging challenge that the intervention is designed to address. Need must be assessed at the level of the actual population being served, not at the level of organizational assumptions or theoretical projections.

**Assessment criteria:**
- Is the stated need accurate, or is there a deeper or different need being masked?
- Who identified the need — the affected population or an external authority?
- Is the need current and ongoing, or has it changed since the intervention was designed?
- Are there competing or layered needs that the intervention does not address?
- Is the need universal across the population, or does it vary by subgroup?

**AI instruction:** Assess the need as it actually exists for the population, not as it was described in program documentation. If the described need and the observed population behavior suggest different needs, flag this discrepancy explicitly.

---

## Dimension 3: Response

**Definition:** Response is the intervention, action, program, or system deployed to address the identified need within the given context. It includes the design, delivery, resources, and implementation approach of the intervention.

**Assessment criteria:**
- Is the response designed for the actual context it is operating in?
- Is the response addressing the actual need or a proxy need?
- Does the response have the resources and structural support to function as designed?
- Is the response delivered in a way that the target population can access and engage with?
- Does the response respect the agency and dignity of the population it serves?

**AI instruction:** Assess fit between the response and the context and need. A response that is well-designed for one context may be entirely inappropriate for another. A response that addresses a proxy need will produce minimal impact on the actual need.

---

## Dimension 4: Impact

**Definition:** Impact is the observable, measurable, or reported outcome of the response within the context. It includes intended outcomes (what was supposed to happen), actual outcomes (what did happen), unintended consequences (what happened that was not planned), and systemic effects (how the intervention changed the context itself).

**Assessment criteria:**
- What outcomes were intended by the intervention?
- What outcomes have actually been observed or reported?
- Are there unintended consequences? Are they positive or negative?
- Has the intervention changed the context in ways that affect future interventions?
- Has the impact been equitably distributed across all population subgroups?

**AI instruction:** Assess impact against the original need, not only against the stated program goals. A program may achieve its stated goals and still fail to address the actual need. Identify this discrepancy when it exists.

---

## Contextual Relevance

**Definition:** Contextual relevance is the degree to which an intervention is appropriately designed for, and responsive to, the specific context and need it is operating within. An intervention is contextually relevant when it correctly identifies the need, is designed for the actual context, and produces outcomes that address the identified need.

**Contextual relevance fails when:**
- The need assessment is inaccurate or based on external assumptions rather than population input
- The response is designed for a generic or idealized context rather than the actual one
- The response does not have access to the resources or structures required to function
- The impact does not address the identified need even if it addresses program metrics

---

# Step-by-Step Instructions

## Step 1: Define the Evaluation Subject and Goal

**Goal:** Establish what intervention is being evaluated and what the evaluation is intended to produce.

**Action:**
- Identify the intervention, program, policy, or system being evaluated.
- Identify the population it serves.
- Identify the evaluation goal: assess relevance, diagnose failure, guide design, or compare options.

**Expected outcome:** A clear subject definition and evaluation goal.

**Validation:** If the subject or goal is ambiguous, ask for clarification before proceeding.

**Fallback behavior:** If only partial information is available, state what is known and mark assumptions explicitly.

**Continue condition:** Subject and goal are clearly established.

**Stop condition:** The subject cannot be defined from the provided information.

---

## Step 2: Assess the Context Dimension

**Goal:** Map the environment in which the intervention operates.

**Action:**
- Identify the physical, cultural, relational, historical, and systemic features of the context.
- Identify contextual enablers (features that help the intervention function).
- Identify contextual constraints (features that obstruct the intervention).
- Identify power dynamics relevant to the intervention's reception.
- Rate context-intervention alignment: Well-Aligned, Partially Aligned, Misaligned, or Undetermined.

**Expected outcome:** A context assessment with a stated alignment rating and supporting evidence.

**Validation:** Every identified contextual feature must be drawn from the provided description, not assumed.

**Fallback behavior:** If contextual information is insufficient, mark as Undetermined and specify what data is needed.

**Continue condition:** Context alignment has been rated or marked Undetermined.

**Stop condition:** None at this step.

---

## Step 3: Assess the Need Dimension

**Goal:** Determine whether the identified need is accurate, current, and population-specific.

**Action:**
- State the need as described in the program or request.
- Assess whether the described need matches the observed population behavior or reported outcomes.
- Identify any discrepancy between the stated need and the actual need.
- Identify whether the need is universal or varies by subgroup.
- Identify who defined the need and whether the affected population was involved in that definition.
- Rate need accuracy: Accurate, Partially Accurate, Inaccurate, or Undetermined.

**Expected outcome:** A need assessment with a stated accuracy rating and supporting evidence.

**Validation:** Any identified discrepancy between stated and actual need must be flagged explicitly.

**Fallback behavior:** Mark Undetermined and specify what population data would resolve the assessment.

**Continue condition:** Need accuracy has been rated or marked Undetermined.

**Stop condition:** None at this step.

---

## Step 4: Assess the Response Dimension

**Goal:** Determine whether the response is appropriately designed for the context and accurately addresses the need.

**Action:**
- Assess fit between the response design and the identified context.
- Assess fit between the response design and the identified need.
- Identify whether the response has sufficient resources, structural support, and accessibility.
- Identify whether the response respects the agency and dignity of the population.
- Rate response appropriateness: Appropriate, Partially Appropriate, Inappropriate, or Undetermined.

**Expected outcome:** A response assessment with a stated appropriateness rating and supporting evidence.

**Validation:** Appropriateness must be assessed against both the context and the need. A response may fit the need but not the context, or vice versa.

**Fallback behavior:** Mark Undetermined if response design details are insufficient.

**Continue condition:** Response appropriateness has been rated or marked Undetermined.

**Stop condition:** None at this step.

---

## Step 5: Assess the Impact Dimension

**Goal:** Determine whether the response is producing outcomes that address the identified need.

**Action:**
- Identify the intended outcomes of the response.
- Identify the actual outcomes as reported or observed.
- Compare actual outcomes against the identified need (not only against program goals).
- Identify any unintended consequences (positive or negative).
- Identify whether impact is equitably distributed across all population subgroups.
- Rate impact alignment: Aligned, Partially Aligned, Misaligned, or Undetermined.

**Expected outcome:** An impact assessment with a stated alignment rating and evidence.

**Validation:** Impact must be assessed against the actual need, not only the stated program goals.

**Fallback behavior:** If outcome data is unavailable, mark as Undetermined and specify what data is needed.

**Continue condition:** Impact alignment has been rated or marked Undetermined.

**Stop condition:** None at this step.

---

## Step 6: Synthesize Contextual Relevance Finding

**Goal:** Produce a synthesized finding on the overall contextual relevance and effectiveness of the intervention.

**Action:**
- Review ratings from all four dimensions.
- Identify the primary source of misalignment if any dimension is rated Misaligned or Inaccurate.
- State whether the intervention is contextually relevant, partially relevant, or not contextually relevant.
- Identify the most critical dimension requiring attention.

**Expected outcome:** A synthesized contextual relevance finding with a priority dimension identified.

**Validation:** The synthesis must be logically consistent with the four dimension ratings.

**Fallback behavior:** If multiple dimensions are Undetermined, state that a complete synthesis cannot be produced and specify what data is needed.

**Continue condition:** A synthesized finding has been stated.

**Stop condition:** None at this step.

---

## Step 7: Generate Recommendations

**Goal:** Produce actionable recommendations to improve contextual relevance and effectiveness.

**Action:**
- For each misaligned or inaccurate dimension, generate one specific recommendation.
- Each recommendation must name the dimension it addresses, the specific change required, and the expected outcome.
- If the goal is design review, provide design guidance for each dimension before implementation.
- If the goal is post-implementation review, provide remediation guidance for each underperforming dimension.

**Expected outcome:** Two to five specific recommendations grounded in the evaluation findings.

**Validation:** Each recommendation must address a specific dimension rating.

**Fallback behavior:** If recommendations require data not yet available, state what information is needed.

**Continue condition:** At least two grounded recommendations have been generated.

**Stop condition:** The evaluation goal has been addressed.

---

## Step 8: Compose the Final Output

**Goal:** Deliver the complete evaluation in the required format.

**Action:**
- Follow the Output Format section exactly.
- Do not omit any required section.
- Do not fabricate ratings or evidence.

---

# Decision Logic

## Primary Decision: What type of evaluation is being requested?

- If assessing an existing program: evaluate all four dimensions against observed outcomes.
- If reviewing a proposed design: evaluate Context and Need for accuracy; evaluate Response for design fit; note that Impact is prospective.
- If diagnosing failure: identify which dimension is most misaligned and trace the failure pattern through the four dimensions.
- If comparing interventions: apply CEF independently to each and compare dimension ratings.

## Secondary Decision: How to handle need discrepancy?

- If the stated need and observed population behavior diverge: flag the divergence explicitly and assess Response and Impact against the actual need, not the stated need.
- If the need has changed since the intervention was designed: note the temporal gap and assess whether the Response remains relevant to the current need.

## Uncertainty Handling

- Never assign a rating without supporting evidence.
- Always qualify ratings with the limitations of available data.
- When uncertainty exists, name it explicitly and specify what data would resolve it.

## Conflict Resolution

- When program documentation and observed outcomes conflict: present both and flag the discrepancy. Do not resolve it by selecting one source without stated rationale.
- When stakeholder perspectives conflict: present all perspectives and identify the dimension each perspective illuminates.

## Missing Information Handling

- If Context information is missing: state that the evaluation cannot assess context-response alignment without it.
- If Impact data is missing: complete the Context, Need, and Response assessments and mark Impact as Undetermined.
- If the Need is not described: request it before proceeding.

---

# Constraints

1. Do not fabricate data, statistics, or research findings about the intervention.
2. Do not attribute program failure to population characteristics or individual behavior.
3. Do not present evaluation findings as certified or official program evaluations.
4. Do not omit negative findings to protect a program or organization.
5. Do not apply this framework to evaluate individual persons — use the ETAR Framework skill instead.
6. Always distinguish between stated program goals and actual population needs.
7. Always include equity considerations in the Impact assessment.
8. Never use evaluation findings to target, stigmatize, or blame the population served.

---

# Edge Cases

## Edge Case 1: Context has changed significantly since the program was designed

Assess the original context-response alignment separately from the current context. Identify the gap between the two. Recommend whether the response requires redesign or adaptation.

## Edge Case 2: Multiple needs are present

If the population has multiple needs and the intervention addresses only one, assess the intervention against the need it targets and note the unaddressed needs as a finding. Do not expect a single intervention to address all identified needs.

## Edge Case 3: Unintended positive consequences

If the intervention produces unintended positive outcomes beyond its stated goals, document these in the Impact assessment as supplementary findings. Do not allow unintended positive outcomes to mask misalignment in the primary need-response relationship.

## Edge Case 4: Intervention is too new to have impact data

If the intervention has recently launched and has no impact data, complete the Context, Need, and Response dimensions and explicitly note that Impact cannot be assessed. Provide prospective impact indicators the evaluator should monitor.

---

# Failure Handling

## Information is missing

State: "A complete CEF evaluation requires [specific missing element]. The following dimensions can be assessed: [list]. The following dimensions require additional information: [list and what data is needed]."

## Context conflicts

State: "Conflicting indicators exist for the [dimension] dimension: [describe conflict]. Both interpretations will be presented with their implications for contextual relevance."

## Multiple interpretations exist

Present all interpretations with their CEF dimension implications. Do not select one without stated rationale.

## Framework cannot be applied

State: "The Context Evaluation Framework cannot be applied because [specific reason]. A minimum of Context and Need descriptions are required to proceed."

---

# Output Format

**Context Evaluation Framework Assessment**

**Intervention:** [Name or description of the program, policy, or system]
**Population:** [Description of the population served]
**Evaluation Goal:** [Purpose of the assessment]

**CEF Dimension Ratings**

| Dimension | Rating | Key Findings |
|---|---|---|
| Context | [Well-Aligned / Partially Aligned / Misaligned / Undetermined] | [Summary] |
| Need | [Accurate / Partially Accurate / Inaccurate / Undetermined] | [Summary] |
| Response | [Appropriate / Partially Appropriate / Inappropriate / Undetermined] | [Summary] |
| Impact | [Aligned / Partially Aligned / Misaligned / Undetermined] | [Summary] |

**Contextual Relevance Synthesis**
[Overall assessment of whether the intervention is contextually relevant, which dimension is the primary source of misalignment, and what this means for the intervention's effectiveness]

**Equity Finding**
[Whether impact is equitably distributed across population subgroups, and what disparities exist]

**Recommendations**
1. [Recommendation: dimension addressed, specific change, expected outcome]
2. [Recommendation]
3. [Recommendation — if applicable]

---

# Success Criteria

The skill has executed correctly when:

1. All four CEF dimensions have been assessed with stated ratings and supporting evidence.
2. A contextual relevance synthesis has been produced.
3. Need accuracy has been assessed against actual population needs, not only program documentation.
4. Equity considerations are addressed in the Impact assessment.
5. Recommendations are directly linked to dimension ratings.
6. No fabricated data appears in the output.
7. The output follows the specified format completely.

---

# Quality Checklist

Before delivering output, verify:

- [ ] Explicit: Every rating is supported by evidence from the provided input.
- [ ] Deterministic: The same input would produce the same dimension ratings.
- [ ] Context aware: The contextual setting is actively considered in every dimension assessment.
- [ ] Human centered: The evaluation prioritizes the actual needs of the population served.
- [ ] Ethical: No population characteristic is used to explain program failure.
- [ ] Reproducible: Another agent applying this skill would reach the same ratings.
- [ ] No ambiguity: Every rating is named with specific supporting evidence.
- [ ] Production ready: The output is complete, structured, and actionable.
