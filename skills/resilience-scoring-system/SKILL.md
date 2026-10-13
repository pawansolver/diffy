---
name: resilience-scoring-system
description: Assesses individual or group resilience across all four ETAR dimensions by scoring fulfillment, adaptability, and systemic support, and generates targeted recommendations to strengthen dimensional resilience.
---

# Purpose

The Resilience Scoring System provides a structured, dimensional assessment of how capable an individual or group is of maintaining functional stability and recovering from dimensional disruption. Resilience, in this framework, is not a fixed trait — it is the dynamic capacity to sustain dimensional fulfillment under pressure, adapt when dimensions are disrupted, and access sufficient systemic support to recover.

The AI agent applying this skill must score resilience across all four ETAR dimensions by evaluating three resilience factors — fulfillment, adaptability, and systemic support — for each dimension. The output must produce a dimensional resilience profile that identifies strengths, vulnerabilities, and specific recommendations to build resilience capacity.

---

# Scope

This skill applies to scenarios requiring:

- Assessment of an individual's capacity to sustain functioning under stress or disruption
- Assessment of a team's or group's collective resilience across ETAR dimensions
- Identification of which dimensions represent resilience strengths and which represent vulnerabilities
- Design of coaching, organizational health, or therapeutic support plans targeting dimensional resilience gaps
- Post-disruption evaluation to determine which dimensions were most affected and require priority rebuilding

This skill does not apply to:
- Clinical trauma assessment or PTSD evaluation
- Psychiatric assessment of resilience-related conditions
- Legal or forensic resilience evaluation

---

# When to Use

Activate this skill when the user request involves:

- Scoring or assessing resilience for an individual, team, or organization
- Understanding why a person or group is struggling to recover from a significant disruption
- Identifying which dimensional resources a person or group has and which they lack
- Designing a coaching, development, or organizational health intervention that builds resilience
- Answering prompts that reference the Resilience Scoring System by name

---

# When NOT to Use

Do not activate this skill when:

- The request involves clinical trauma processing or psychiatric intervention
- The individual's described situation suggests immediate safety concern — address safety before applying the scoring system
- The assessment would be used to rank or compare individuals for punitive or discriminatory purposes
- Insufficient contextual information is available to score at least two dimensions

---

# Inputs

**Required:**
- A description of the individual or group being assessed
- A description of the disruption or stressor they have experienced or are experiencing
- At least one described behavioral, emotional, cognitive, or systemic response to the disruption

**Expected context:**
- Current environmental state (Survival, Emotional, or Executive)
- Available relational, institutional, and material supports
- Prior resilience history (how the individual or group has handled previous disruptions)

**Optional:**
- Specific dimensions the user wants to prioritize in the assessment
- Self-reported resilience beliefs or self-perception
- Cultural context that affects resilience expression

---

# Preconditions

Before executing this skill, verify the following:

1. The subject is an individual, group, team, or organization — not a system structure (use DSI or Vyavastha skills for system analysis).
2. A disruption or stressor is described or implied.
3. Sufficient information is available to score at least two dimensions.
4. The goal is constructive: building resilience, identifying support needs, or designing interventions.
5. The scoring will not be used to stigmatize, penalize, or rank the subject.
6. If safety concerns are present, they are acknowledged before the assessment proceeds.

---

# Core Concepts

## Resilience Definition (Framework-Specific)

**Definition:** Resilience is the dynamic capacity of an individual or group to:
1. Maintain dimensional fulfillment under normal conditions
2. Continue functioning (at reduced capacity if necessary) during disruption
3. Recover dimensional fulfillment after disruption
4. Adapt their dimensional expression in response to changed circumstances

Resilience is not the absence of distress. A resilient person or group may experience significant distress and still demonstrate resilience through their capacity to sustain function, seek support, and recover.

**AI instruction:** Do not confuse absence of distress expression with resilience. Do not confuse emotional expression with fragility. Assess actual functional capacity across dimensions, not outward emotional tone.

---

## Three Resilience Factors

### Factor 1: Fulfillment

**Definition:** Fulfillment is the degree to which a dimension is currently active and meeting the individual's or group's needs under baseline (non-disrupted) conditions.

A dimension with high fulfillment is well-established, regularly activated, and positively contributing to the person's functioning.

A dimension with low fulfillment is chronically underactivated, suppressed, or not meeting needs even under baseline conditions.

**AI instruction:** Fulfillment is a baseline measure. It reflects how well the dimension is functioning before or outside the disruption. Low fulfillment in a dimension means the disruption has less resilience capacity to draw on from that dimension.

---

### Factor 2: Adaptability

**Definition:** Adaptability is the degree to which the individual or group can adjust their dimensional expression in response to changed circumstances without losing core function.

High adaptability: The person can shift how they express a dimension (e.g., shifting from collaborative action to independent action when a team is unavailable) without collapsing that dimension.

Low adaptability: The person is locked into a single expression of a dimension. When that expression is disrupted, the dimension collapses entirely.

**AI instruction:** Adaptability is the resilience lever. A dimension with high fulfillment but low adaptability is vulnerable to disruption. A dimension with moderate fulfillment and high adaptability can sustain function through significant disruption.

---

### Factor 3: Systemic Support

**Definition:** Systemic support is the degree to which external structures, relationships, institutions, and resources are available to sustain or restore dimensional function when the individual or group cannot sustain it alone.

High systemic support: Reliable relationships, institutional resources, and material conditions actively support dimensional recovery.

Low systemic support: The individual or group must sustain all dimensional functioning without external support. Isolation, resource deprivation, or institutional failure reduces resilience regardless of individual capacity.

**AI instruction:** Systemic support is not an individual variable. Do not attribute low systemic support to individual failure. Identify the structural reasons for low systemic support and attribute them to systemic conditions.

---

## Resilience Score Construction

For each ETAR dimension, assess all three factors. Each factor is rated on a three-point scale:

- **High (2 points):** Factor is fully present and functioning.
- **Moderate (1 point):** Factor is partially present or inconsistently available.
- **Low (0 points):** Factor is absent or severely compromised.

Maximum score per dimension: 6 (High on all three factors)
Minimum score per dimension: 0 (Low on all three factors)

Overall resilience score: Sum of all four dimensions.
Maximum overall score: 24
Minimum overall score: 0

**Score interpretation:**
- 18-24: High resilience. All or most dimensions are well-supported. The person or group can sustain functioning through significant disruption.
- 12-17: Moderate resilience. Some dimensions are strong; others are vulnerable. Targeted support can substantially improve resilience.
- 6-11: Low resilience. Multiple dimensions have significant gaps. Proactive support and systemic intervention are needed to prevent collapse.
- 0-5: Critical vulnerability. Most dimensions are severely compromised. Immediate, intensive support is required.

**AI instruction:** Present scores as indicators, not as definitive measurements. The score reflects available information, not certified assessment. Always qualify scores accordingly.

---

## Dimensional Resilience Profiles

**Experiential Resilience:** Capacity to maintain emotional processing, self-awareness, and felt safety under pressure.

**Thought Resilience:** Capacity to maintain cognitive clarity, adaptive reasoning, and belief flexibility under pressure.

**Action Resilience:** Capacity to maintain purposeful, self-directed behavior under pressure, and to access alternative action pathways when primary pathways are disrupted.

**Reality Resilience:** Capacity to navigate external systemic conditions, access material and institutional support, and adapt to changed structural circumstances.

---

# Step-by-Step Instructions

## Step 1: Receive and Parse the Subject Description

**Goal:** Extract all relevant information about the subject, the disruption, and their current state.

**Action:**
- Identify the subject (individual, group, team, organization).
- Identify the disruption or stressor being experienced.
- Identify described behavioral, emotional, cognitive, or systemic responses.
- Identify current environmental state (Survival, Emotional, Executive, or Undetermined).
- Note any described supports or absences of support.

**Expected outcome:** A structured summary of the subject, disruption, and current state.

**Validation:** If subject or disruption cannot be identified, request the information before proceeding.

**Fallback behavior:** State what is known and mark assumptions clearly.

**Continue condition:** Subject and disruption are identified.

**Stop condition:** Neither subject nor disruption can be identified.

---

## Step 2: Score the Experiential Dimension

**Goal:** Assign a resilience score for the Experiential dimension.

**Action:**
- Score Fulfillment: Is the person's emotional life well-established and meeting their needs under baseline conditions?
- Score Adaptability: Can the person adjust how they process emotion when usual outlets are unavailable?
- Score Systemic Support: Are relational and emotional support resources reliably available?
- Assign ratings (High/Moderate/Low) for each factor with supporting evidence.
- Calculate the dimension score.

**Expected outcome:** Experiential dimension score (0-6) with factor ratings and evidence.

**Validation:** Every rating must be justified by described evidence, not assumed.

**Fallback behavior:** If information is insufficient for a factor, assign Moderate with a note that the rating is unconfirmed.

**Continue condition:** All three factors are rated.

**Stop condition:** None at this step.

---

## Step 3: Score the Thought Dimension

**Goal:** Assign a resilience score for the Thought dimension.

**Action:**
- Score Fulfillment: Is the person's cognitive functioning well-established and meeting their reasoning needs under baseline conditions?
- Score Adaptability: Can the person shift reasoning frameworks when their usual approach fails?
- Score Systemic Support: Are educational, informational, or mentorship resources available?
- Assign ratings with supporting evidence and calculate the dimension score.

**Expected outcome:** Thought dimension score (0-6) with factor ratings and evidence.

**Validation and fallback:** Same as Step 2.

**Continue condition:** All three factors are rated.

**Stop condition:** None at this step.

---

## Step 4: Score the Action Dimension

**Goal:** Assign a resilience score for the Action dimension.

**Action:**
- Score Fulfillment: Is the person's action capacity well-established and producing meaningful outcomes under baseline conditions?
- Score Adaptability: Can the person access alternative action pathways when primary pathways are disrupted?
- Score Systemic Support: Are employment, mobility, participation, and institutional resources available?
- Assign ratings with supporting evidence and calculate the dimension score.

**Expected outcome:** Action dimension score (0-6) with factor ratings and evidence.

**Validation and fallback:** Same as Step 2.

**Continue condition:** All three factors are rated.

**Stop condition:** None at this step.

---

## Step 5: Score the Reality Dimension

**Goal:** Assign a resilience score for the Reality dimension.

**Action:**
- Score Fulfillment: Are the person's material and structural conditions meeting their needs under baseline conditions?
- Score Adaptability: Can the person navigate or adapt to changed structural conditions?
- Score Systemic Support: Are material resources, legal protections, and institutional supports available?
- Assign ratings with supporting evidence and calculate the dimension score.

**Expected outcome:** Reality dimension score (0-6) with factor ratings and evidence.

**Validation and fallback:** Same as Step 2.

**Continue condition:** All three factors are rated.

**Stop condition:** None at this step.

---

## Step 6: Calculate Overall Resilience Score and Interpret

**Goal:** Produce the overall resilience score and interpret it within the scoring scale.

**Action:**
- Sum all four dimension scores.
- Interpret the overall score against the scale (18-24 High, 12-17 Moderate, 6-11 Low, 0-5 Critical).
- Identify the highest-scoring dimension (resilience strength).
- Identify the lowest-scoring dimension (primary vulnerability).

**Expected outcome:** Overall score, interpretation, identified strength, and identified primary vulnerability.

**Validation:** The interpretation must match the score range. Do not apply a more favorable interpretation than the score warrants.

**Continue condition:** Overall score and interpretation are stated.

**Stop condition:** None at this step.

---

## Step 7: Generate Dimensional Resilience Recommendations

**Goal:** Provide specific recommendations to build resilience in the identified vulnerability dimensions.

**Action:**
- For each dimension scoring Low or Moderate, generate one recommendation per resilience factor that is Low or Moderate.
- Each recommendation must name: the dimension, the factor being addressed, the specific action, and the expected outcome.
- Prioritize recommendations for the lowest-scoring dimension first.
- If systemic support is consistently Low across dimensions, include a systemic-level recommendation.

**Expected outcome:** Three to six specific resilience-building recommendations.

**Validation:** Each recommendation must address a named factor rating.

**Fallback behavior:** If the intervention requires clinical support, state this and recommend professional resources as the first priority.

**Continue condition:** At least two recommendations have been generated.

**Stop condition:** The analytical goal has been addressed.

---

## Step 8: Compose the Final Output

**Goal:** Deliver the complete resilience assessment in the required format.

**Action:**
- Follow the Output Format section exactly.
- Do not omit any required section.
- Do not fabricate factor ratings or evidence.

---

# Decision Logic

## Primary Decision: Individual or group assessment?

- Individual: score all four dimensions for the described person.
- Group: score collective resilience by assessing the group's aggregate capacity across dimensions. Note significant individual variation within the group.

## Secondary Decision: How to handle insufficient information?

- If two or more dimensions cannot be scored: state that a complete resilience assessment cannot be produced. Provide scores for available dimensions and specify what information is needed.
- If one dimension cannot be scored: assign Moderate across all factors with a note that the rating is unconfirmed and proceed.

## Uncertainty Handling

- Never assign High without positive evidence.
- When uncertainty exists, default to Moderate and note explicitly that the rating is unconfirmed.

## Missing Information Handling

- If disruption is not described: request it before proceeding.
- If support resources are not described: note Low systemic support as a possibility and flag it for confirmation.

---

# Constraints

1. Do not present resilience scores as certified, clinical, or diagnostic measurements.
2. Do not attribute low resilience scores to character flaws, weakness, or individual failure.
3. Do not attribute low systemic support to individual choices without acknowledging structural factors.
4. Do not compare individuals' resilience scores in a ranking or competitive context.
5. Always qualify scores with the limitations of available information.
6. Always attribute systemic support gaps to structural conditions.
7. Do not fabricate evidence for any factor rating.

---

# Edge Cases

## Edge Case 1: Subject in acute crisis

If the subject is in active crisis (Survival State), note that resilience scoring reflects emergency conditions, not baseline capacity. Score the current state and separately estimate baseline resilience capacity if information allows. Recommend immediate crisis support before coaching or development interventions.

## Edge Case 2: Very high adaptability with very low fulfillment

A subject may have high adaptability (they adjust constantly) but very low fulfillment (they are constantly adjusting from a deficit state). This pattern indicates chronic survival-mode functioning disguised as resilience. Identify it explicitly and address the fulfillment deficit as the priority.

## Edge Case 3: Group with high collective and low individual resilience

Some groups demonstrate high collective resilience (strong social cohesion, shared resources) with individual members who are personally vulnerable. Score both the collective and individual levels where information allows.

---

# Failure Handling

## Information is missing

State: "A complete resilience assessment requires [specific missing element]. The following dimensions can be scored: [list]. Please provide [specific information] to complete the assessment."

## Safety concerns present

State: "The described situation includes indicators of acute distress or safety concern. Immediate support is recommended as the priority before resilience scoring is applied. Specific concerns: [list]."

## Framework cannot be applied

State: "The Resilience Scoring System requires a described subject and at least one disruption or stressor. Please provide [missing element] to proceed."

---

# Output Format

**Resilience Assessment**

**Subject:** [Individual / Group / Team / Organization]
**Disruption or Stressor:** [Description]
**Current Environmental State:** [Survival / Emotional / Executive / Undetermined]

**Dimensional Resilience Scores**

| Dimension | Fulfillment | Adaptability | Systemic Support | Dimension Score |
|---|---|---|---|---|
| Experiential | [High(2) / Moderate(1) / Low(0)] | [H/M/L] | [H/M/L] | [0-6] |
| Thought | [H/M/L] | [H/M/L] | [H/M/L] | [0-6] |
| Action | [H/M/L] | [H/M/L] | [H/M/L] | [0-6] |
| Reality | [H/M/L] | [H/M/L] | [H/M/L] | [0-6] |
| **Overall** | | | | **[0-24]** |

**Score Interpretation:** [High / Moderate / Low / Critical Vulnerability]

**Resilience Strength:** [Dimension with highest score and why it represents a strength]

**Primary Vulnerability:** [Dimension with lowest score and what specific factors account for it]

**Factor Evidence Summary**
[Brief narrative explaining the key evidence that drove the scoring for each dimension]

**Resilience-Building Recommendations**
Priority 1 (lowest-scoring dimension):
1. [Factor addressed, specific action, expected outcome]

Priority 2:
2. [Factor addressed, specific action, expected outcome]

Priority 3 (if applicable):
3. [Factor addressed, specific action, expected outcome]

**Systemic Recommendation** (if systemic support is Low across multiple dimensions):
[Structural or institutional changes needed to improve aggregate systemic support]

---

# Success Criteria

The skill has executed correctly when:

1. All four dimensions have been scored with all three factors rated and evidenced.
2. The overall score and interpretation are correct relative to the scale.
3. Resilience strength and primary vulnerability are named with evidence.
4. Recommendations are targeted to specific factor gaps.
5. Systemic support deficits are attributed to structural conditions, not individual failure.
6. No fabricated evidence appears in the output.
7. The output follows the specified format completely.

---

# Quality Checklist

Before delivering output, verify:

- [ ] Explicit: Every factor rating is supported by described evidence.
- [ ] Deterministic: The same input would produce the same scores.
- [ ] Context aware: Current environmental state and systemic conditions are considered throughout.
- [ ] Human centered: The assessment supports dimensional recovery and well-being, not ranking or judgment.
- [ ] Ethical: No stigmatizing attributions appear in the output.
- [ ] Reproducible: Another agent applying this skill would reach the same scores.
- [ ] No ambiguity: Every Low rating is named with specific supporting evidence.
- [ ] Production ready: The output is complete, scored, and immediately actionable.
