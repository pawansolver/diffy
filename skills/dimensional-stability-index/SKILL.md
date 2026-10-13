---
name: dimensional-stability-index
description: Applies the Dimensional Stability Index (DSI) to measure and evaluate societal or community well-being across human dimensions as a structured alternative to GDP-based metrics.
---

# Purpose

The Dimensional Stability Index (DSI) is a proposed measurement system for assessing the well-being, fulfillment, and systemic health of communities, societies, and institutions. It replaces purely economic indicators such as GDP with a multidimensional evaluation that accounts for the quality of human experience, systemic justice, access to resources, and developmental opportunity across ETAR dimensions.

The AI agent applying this skill must use the DSI to evaluate policies, communities, or systems by assessing stability and fulfillment across all relevant human dimensions. The output must be analytical, evidence-grounded, and actionable for policy-makers, community developers, and systemic designers.

---

# Scope

This skill applies to scenarios requiring:

- Evaluation of the well-being impact of policies, programs, or governance structures
- Community health assessment beyond economic metrics
- Systemic justice analysis identifying which populations are dimensionally underserved
- Measurement of human development outcomes in education, housing, healthcare, or governance
- Comparative evaluation of different policy approaches using a multidimensional lens
- Identification of systemic bugs — structural misalignments that cause dimensional unfulfillment

This skill does not apply to financial auditing, economic forecasting, or any assessment that requires certified professional measurement or licensed methodology.

---

# When to Use

Activate this skill when the user request involves:

- Evaluating the human impact of a new or existing policy
- Assessing whether a community, institution, or system is meeting the dimensional needs of its members
- Identifying where systemic structures are creating dimensional suppression or unfulfillment
- Designing measurement criteria for community well-being that go beyond economic output
- Comparing two or more systemic approaches on their dimensional impact
- Answering prompts that reference the Dimensional Stability Index by name

---

# When NOT to Use

Do not activate this skill when:

- The request requires certified economic, legal, or clinical measurement
- The request is about individual-level assessment (use the ETAR Framework skill instead)
- The system or community being evaluated has no described characteristics — the DSI cannot be applied to a blank subject
- The user is seeking financial investment advice or market analysis
- The request requires producing legally binding assessments or official reports

---

# Inputs

**Required:**
- A description of the community, policy, institution, or system being evaluated
- The evaluation goal (e.g., assess well-being impact, identify gaps, compare options)
- At least one described characteristic of the system being evaluated (population, structure, outcomes, or context)

**Expected context:**
- Geographic, cultural, or institutional setting
- Existing data, reported outcomes, or known conditions
- The populations affected and their described needs

**Optional:**
- Specific dimensions to prioritize
- Comparative baseline (e.g., prior policy, different community)
- Known systemic constraints or injustices

---

# Preconditions

Before executing this skill, verify the following:

1. The subject of evaluation is a system, community, institution, or policy — not an individual.
2. Sufficient contextual information is available to assess at least two DSI dimensions.
3. The analytical goal is constructive: improving well-being, identifying gaps, or guiding design.
4. No DSI score will be presented as a definitive or certified measurement without appropriate qualification.
5. Systemic findings will not be used to blame or stigmatize any population group.

If any precondition fails, state which precondition is unmet and what information is required.

---

# Core Concepts

## Dimensional Stability

**Definition:** Dimensional stability refers to the consistent, reliable availability of conditions that allow individuals within a system to fulfill their needs across all ETAR dimensions (Experiential, Thought, Action, Reality).

A system is dimensionally stable when:
- Members can safely experience and express their emotional and sensory lives (Experiential stability)
- Members have access to information, education, and cognitive development opportunities (Thought stability)
- Members can take meaningful, self-directed action without systemic obstruction (Action stability)
- The structures, laws, and material conditions of the system produce fair and human-centered outcomes (Reality stability)

A system is dimensionally unstable when one or more of these conditions is absent, suppressed, or inequitably distributed.

## Dimensional Fulfillment vs. Unfulfillment

**Definition:** Dimensional fulfillment occurs when a system actively supports the activation of all four ETAR dimensions for its members. Dimensional unfulfillment occurs when the system suppresses, ignores, or inequitably distributes access to dimensional activation.

**AI instruction:** When applying the DSI, assess each dimension for the degree of fulfillment it provides to the population. Do not assess fulfillment only for the majority population. Identify which subgroups are experiencing dimensional unfulfillment and why.

## Systemic Bugs

**Definition:** A systemic bug is a structural misalignment within a system that consistently produces dimensional unfulfillment for a portion or all of the population. Systemic bugs are not individual failures. They are design errors or historical injustices embedded in the system.

**Examples:**
- An education system that requires standardized testing for diverse learning styles is a systemic bug in the Thought dimension.
- A healthcare system accessible only to high-income earners is a systemic bug in the Reality dimension.
- A governance structure that excludes community voices from decision-making is a systemic bug in the Action dimension.

**AI instruction:** When identifying systemic bugs, attribute them to structural causes, not to individual behavior or group characteristics.

## Systemic Justice

**Definition:** Systemic justice is the presence of structures and processes that equitably distribute dimensional fulfillment across all population groups regardless of gender, income, age, ethnicity, or background.

**AI instruction:** The DSI must always include a systemic justice assessment. Identify which populations receive disproportionately low dimensional support and what structural factors account for this disparity.

## DSI Dimensions

The DSI evaluates systems across four primary dimensions derived from the ETAR model, plus additional metrics:

**Experiential Stability:** Does the system provide emotional safety, access to cultural expression, and protection from harm?

**Thought Stability:** Does the system provide access to education, critical thinking development, accurate information, and cognitive freedom?

**Action Stability:** Does the system provide agency, participation rights, mobility, employment, and the ability to make meaningful choices?

**Reality Stability:** Do the laws, physical infrastructure, economic structures, and governance systems produce equitable and human-centered outcomes?

**Supplementary Metrics:**
- **Developmental Access:** The degree to which the system supports child and adult development across ETAR dimensions.
- **Relational Health:** The degree to which the system supports healthy interpersonal and community relationships.
- **Systemic Justice Index:** The degree to which dimensional fulfillment is equitably distributed across all population subgroups.

---

# Step-by-Step Instructions

## Step 1: Define the Subject and Evaluation Goal

**Goal:** Establish what system or policy is being evaluated and what the evaluation is intended to produce.

**Reasoning:** The DSI cannot be applied without a clearly defined subject and purpose.

**Action:**
- Identify the system, community, institution, or policy being evaluated.
- Identify the population it serves and the populations most affected by its outcomes.
- Identify the evaluation goal: well-being assessment, gap identification, policy comparison, or design guidance.

**Expected outcome:** A clear subject definition and evaluation goal statement.

**Validation:** If the subject or goal is ambiguous, ask for clarification before proceeding.

**Fallback behavior:** If only partial information is available, state what is known and what assumptions are being made.

**Continue condition:** Subject and goal are clearly established.

**Stop condition:** Subject cannot be defined from the provided information.

---

## Step 2: Assess Experiential Stability

**Goal:** Evaluate whether the system provides emotional safety, cultural expression, and protection from harm.

**Action:**
- Look for evidence of emotional safety infrastructure (mental health services, community support, protection from violence).
- Look for evidence of cultural and expressive freedom (arts, language rights, cultural preservation).
- Look for evidence of harm (trauma exposure, discrimination, emotional suppression at systemic level).
- Assign a stability level: High, Moderate, Low, or Undetermined.
- Identify which populations are most affected by instability.

**Expected outcome:** An Experiential Stability rating with supporting evidence.

**Validation:** The rating must be based on described system characteristics, not assumptions.

**Fallback behavior:** If insufficient information, mark as Undetermined and note what data would resolve it.

**Continue condition:** Rating is assigned or marked Undetermined.

**Stop condition:** None at this step.

---

## Step 3: Assess Thought Stability

**Goal:** Evaluate whether the system supports cognitive development, access to information, and critical reasoning.

**Action:**
- Look for evidence of educational access and quality.
- Look for evidence of information freedom or suppression.
- Look for evidence of critical thinking development in educational or institutional structures.
- Identify structural features that either support or obstruct cognitive development.
- Assign a stability level: High, Moderate, Low, or Undetermined.
- Identify which populations have disproportionately limited Thought stability.

**Expected outcome:** A Thought Stability rating with supporting evidence.

**Validation:** Rating must be grounded in described system characteristics.

**Fallback behavior:** Mark Undetermined and specify needed data if evidence is insufficient.

**Continue condition:** Rating is assigned or marked Undetermined.

**Stop condition:** None at this step.

---

## Step 4: Assess Action Stability

**Goal:** Evaluate whether the system enables meaningful agency, participation, and self-directed choice for its members.

**Action:**
- Look for evidence of participation rights (voting, community input, freedom of movement).
- Look for evidence of economic mobility and employment access.
- Look for evidence of systemic barriers that prevent meaningful action (bureaucratic obstruction, discrimination, poverty).
- Assign a stability level: High, Moderate, Low, or Undetermined.
- Identify which populations are most constrained in the Action dimension.

**Expected outcome:** An Action Stability rating with supporting evidence.

**Validation:** Rating must reference described structural features.

**Fallback behavior:** Mark Undetermined and specify needed data.

**Continue condition:** Rating is assigned or marked Undetermined.

**Stop condition:** None at this step.

---

## Step 5: Assess Reality Stability

**Goal:** Evaluate whether the laws, infrastructure, economic systems, and governance structures produce equitable and human-centered outcomes.

**Action:**
- Look for evidence of legal protections and rule of law.
- Look for evidence of physical infrastructure quality and access.
- Look for evidence of economic equity or inequity.
- Look for evidence of governance structures that are or are not accountable to the population.
- Assign a stability level: High, Moderate, Low, or Undetermined.
- Identify systemic bugs embedded in Reality structures.

**Expected outcome:** A Reality Stability rating with supporting evidence.

**Validation:** Rating must be grounded in described system characteristics.

**Fallback behavior:** Mark Undetermined and specify needed data.

**Continue condition:** Rating is assigned or marked Undetermined.

**Stop condition:** None at this step.

---

## Step 6: Conduct Systemic Justice Assessment

**Goal:** Determine whether dimensional stability is equitably distributed across all population groups.

**Action:**
- Identify the primary population subgroups present in or affected by the system.
- For each dimension, note whether the stability rating applies equally to all subgroups or disproportionately to some.
- Identify which subgroups experience dimensional unfulfillment.
- Identify the structural causes of any disparity.
- Do not attribute disparity to group characteristics. Attribute it to systemic structure.

**Expected outcome:** A systemic justice assessment stating which dimensions show equity or disparity and for which populations.

**Validation:** All identified disparities must be linked to structural, not behavioral, causes.

**Fallback behavior:** If subgroup data is unavailable, note this explicitly and flag systemic justice as requiring further investigation.

**Continue condition:** At least one equity or disparity finding has been stated.

**Stop condition:** None at this step.

---

## Step 7: Identify Systemic Bugs and Fulfillment Gaps

**Goal:** Name the specific structural misalignments causing dimensional unfulfillment.

**Action:**
- For each dimension rated Low or with noted disparities, identify the structural features causing the rating.
- State each systemic bug as a specific structural feature, not as a population characteristic.
- State the dimensional impact of each systemic bug.

**Expected outcome:** A list of identified systemic bugs with their dimensional impacts.

**Validation:** Each systemic bug must be supported by evidence from the provided context.

**Fallback behavior:** If systemic bugs cannot be identified from available information, note the absence and state what additional data is needed.

**Continue condition:** At least one systemic bug or fulfillment gap has been identified.

**Stop condition:** None at this step.

---

## Step 8: Generate Recommendations Aligned with Evaluation Goal

**Goal:** Produce actionable recommendations that address identified systemic bugs and improve dimensional stability.

**Action:**
- For each identified systemic bug, generate one specific recommendation.
- Each recommendation must name the dimension it addresses, the structural change required, and the expected dimensional impact.
- If the goal is policy comparison, compare each option on its dimensional stability outcomes.

**Expected outcome:** Two to six specific recommendations grounded in DSI findings.

**Validation:** Each recommendation must address a named systemic bug or fulfillment gap.

**Fallback behavior:** If recommendations require data not available, state what information is needed.

**Continue condition:** At least two grounded recommendations have been generated.

**Stop condition:** The evaluation goal has been addressed.

---

## Step 9: Compose the Final Output

**Goal:** Deliver the complete DSI evaluation in the required format.

**Action:**
- Follow the Output Format section exactly.
- Do not omit any required section.
- Do not fabricate ratings or evidence.

---

# Decision Logic

## Primary Decision: What is the appropriate scope of analysis?

- If a single policy is being evaluated: assess all four dimensions against that policy's stated and observed outcomes.
- If a community is being evaluated: assess all four dimensions against described living conditions and structural features.
- If two policies are being compared: apply the DSI independently to each, then compare ratings side by side.

## Secondary Decision: How to handle missing dimension data?

- If data is available for two or more dimensions: proceed with available dimensions and mark missing dimensions as Undetermined.
- If data is available for only one dimension: state that a full DSI evaluation cannot be completed and provide a partial assessment for the available dimension.
- If no data is available: decline to apply the DSI and request the required information.

## Tertiary Decision: How to handle conflicting evidence?

- If evidence shows both high and low stability indicators for the same dimension: identify the populations for whom each applies and note the inequality as a systemic justice finding.
- If evidence from different sources conflicts: present both sets of evidence and note the conflict. Do not resolve it by choosing one source without stated rationale.

## Uncertainty Handling

- Never assign a definitive rating without supporting evidence.
- Always qualify ratings with the limitation of the available data.
- When uncertainty exists, name the uncertainty and specify what data would resolve it.

## Missing Information Handling

- If population information is missing: state that a systemic justice assessment cannot be completed and note what data is needed.
- If the evaluation goal is missing: default to "assess well-being impact" and state the assumption explicitly.

---

# Constraints

1. Do not fabricate data, statistics, or research findings.
2. Do not attribute systemic unfulfillment to group characteristics, cultural traits, or individual behavior.
3. Do not present DSI ratings as certified, official, or legally binding measurements.
4. Do not omit marginalized populations from the systemic justice assessment.
5. Do not apply this skill to assess individual persons — use the ETAR Framework skill instead.
6. Do not use DSI findings to justify discrimination or inequitable resource allocation.
7. Always qualify findings with the limitations of available information.
8. Always attribute systemic bugs to structural causes, not individual failures.

---

# Edge Cases

## Edge Case 1: Evaluating a system with no described population

If the system is described structurally but no population characteristics are provided, complete the structural assessment for each dimension and flag the systemic justice section as incomplete. State what population data is needed.

## Edge Case 2: Evaluating a system in transition

If the system is undergoing significant change (e.g., a new policy just implemented), assess the current state and separately note the projected dimensional impact of the change. Clearly distinguish between current and projected assessments.

## Edge Case 3: Conflicting population subgroup needs

If the described system serves populations with potentially conflicting dimensional needs (e.g., a policy that increases Action stability for one group while reducing it for another), identify both impacts explicitly. Do not resolve the conflict by prioritizing one population.

## Edge Case 4: Evaluating a historical system

When evaluating a historical policy or system, apply the DSI to the conditions as they were described at that time. Do not retroactively apply current standards without acknowledging the temporal context.

---

# Failure Handling

## Information is missing

State: "A complete DSI evaluation requires [specific missing element]. The following dimensions can be assessed with available information: [list]. The following dimensions cannot be assessed: [list]. Please provide [specific data] to complete the evaluation."

## Context conflicts

State: "The provided information contains conflicting indicators for the [dimension] dimension: [describe conflict]. Both interpretations will be presented. The systemic justice implications differ depending on which is accurate."

## Multiple interpretations exist

Present both interpretations with their respective dimensional implications. Do not select one without stated rationale.

## Framework cannot be applied

State: "The Dimensional Stability Index cannot be applied to this request because [specific reason]. A minimum of two assessable dimensions and a defined subject are required."

---

# Output Format

**Dimensional Stability Index Evaluation**

**Subject:** [System, community, policy, or institution being evaluated]
**Population Served:** [Description of affected populations]
**Evaluation Goal:** [Purpose of the assessment]

**DSI Dimensional Ratings**

| Dimension | Stability Level | Key Findings |
|---|---|---|
| Experiential | [High / Moderate / Low / Undetermined] | [Summary of evidence] |
| Thought | [High / Moderate / Low / Undetermined] | [Summary of evidence] |
| Action | [High / Moderate / Low / Undetermined] | [Summary of evidence] |
| Reality | [High / Moderate / Low / Undetermined] | [Summary of evidence] |

**Systemic Justice Assessment**
[Which populations experience dimensional fulfillment, which experience unfulfillment, and what structural factors account for the disparity]

**Identified Systemic Bugs**
1. [Systemic bug: dimension affected, structural cause, dimensional impact]
2. [Systemic bug]
3. [Systemic bug — if applicable]

**Recommendations**
1. [Recommendation: dimension addressed, structural change required, expected impact]
2. [Recommendation]
3. [Recommendation — if applicable]

**Overall DSI Assessment**
[Summary statement on whether the system is dimensionally stable, partially stable, or unstable, with the primary drivers of each finding]

---

# Success Criteria

The skill has executed correctly when:

1. All four DSI dimensions have been assessed with stability ratings and supporting evidence.
2. The systemic justice assessment identifies affected populations and structural causes.
3. Systemic bugs are named as structural features, not population characteristics.
4. Recommendations are directly linked to identified systemic bugs or fulfillment gaps.
5. No fabricated data appears in the output.
6. The output follows the specified format completely.
7. The evaluation is useful for the stated goal.

---

# Quality Checklist

Before delivering output, verify:

- [ ] Explicit: Every rating is supported by described evidence from the input.
- [ ] Deterministic: The same input would produce the same dimensional ratings.
- [ ] Context aware: Population diversity and systemic context are reflected throughout.
- [ ] Human centered: The evaluation prioritizes human well-being and dimensional fulfillment.
- [ ] Ethical: No population is characterized by group traits or blamed for systemic failures.
- [ ] Reproducible: Another agent applying this skill to the same input would reach the same ratings.
- [ ] No ambiguity: Every stability level is named with specific supporting evidence.
- [ ] Production ready: The output is complete, structured, and qualified appropriately.
