---
name: dimensional-decision-making
description: Guides individuals and groups through multidimensional decision-making by evaluating each decision option against all four ETAR dimensions (Experiential, Thought, Action, Reality) and identifying the choice most aligned with dimensional fulfillment.
---

# Purpose

The Dimensional Decision-Making Framework provides a structured process for evaluating decisions by examining them across all four ETAR dimensions. It is used when a person or group faces a choice that involves not just logical analysis but also experiential, behavioral, and systemic considerations. The framework ensures that decisions are not made from a single dimension in isolation (e.g., only logical or only emotional) but are evaluated for multidimensional alignment and fulfillment.

The AI agent applying this skill must guide the user through a step-by-step dimensional evaluation of each option, identify which option produces the greatest dimensional fulfillment, and deliver a structured recommendation without imposing a choice on the person.

---

# Scope

This skill applies to scenarios requiring:

- Evaluation of two or more decision options using a multidimensional lens
- Identification of dimensional tensions in a decision (e.g., what feels right vs. what is logical vs. what is structurally feasible)
- Support for individuals in personal or professional decision-making
- Group or organizational decision-making where multiple stakeholder dimensions must be considered
- Leadership and coaching contexts where decisions require alignment across experience, reasoning, action, and systemic reality

This skill does not apply to decisions requiring legal, medical, financial, or clinical professional judgment. The framework may inform but does not replace expert professional advice.

---

# When to Use

Activate this skill when the user request involves:

- Choosing between two or more defined options (career path, relationship choice, organizational strategy, educational direction)
- Feeling stuck or conflicted between what feels right (Experiential) and what seems logical (Thought) or practical (Reality)
- A group needing a structured process to reach a decision that accounts for multiple stakeholder perspectives
- A leader or coach helping someone explore the full dimensional implications of a decision
- Answering prompts that reference the Dimensional Decision-Making Framework by name

---

# When NOT to Use

Do not activate this skill when:

- The decision has only one viable option
- The request is for a clinical, legal, medical, or financial recommendation that requires professional certification
- The user has already made a final decision and is seeking validation, not evaluation
- The decision context is so vague that no dimensional analysis can be grounded in evidence
- The decision involves safety or harm, in which case safety must be addressed before this framework is applied

---

# Inputs

**Required:**
- A description of the decision context (what situation is prompting the decision)
- At least two defined options being considered
- The identity of the decision-maker (individual, group, or leadership role)

**Expected context:**
- The person's or group's current environmental state (Survival, Emotional, or Executive — if known)
- Known values, priorities, or constraints
- Any stated experiential, cognitive, behavioral, or systemic factors relevant to the decision

**Optional:**
- The person's stated preference or leaning
- Prior decisions in similar contexts
- Stakeholder perspectives (for group decisions)
- Time constraints or urgency level

---

# Preconditions

Before executing this skill, verify the following:

1. At least two distinct options are identifiable from the user's input.
2. The decision context is described sufficiently to allow dimensional assessment.
3. The environmental state of the decision-maker is assessed or estimated before proceeding.
4. The goal is to support autonomous decision-making, not to impose a choice.
5. If the decision context involves risk to safety or wellbeing, this is explicitly acknowledged and the user is directed to appropriate support before the framework is applied.

If preconditions 1 or 2 are not met, request the required information before proceeding.

---

# Core Concepts

## Dimensional Alignment in Decisions

**Definition:** A decision is dimensionally aligned when it satisfies or moves toward satisfying the needs of all four ETAR dimensions for the decision-maker. A decision is dimensionally misaligned when it fulfills one or two dimensions at the expense of others.

**Examples:**
- A career choice that is financially viable (Reality) but emotionally draining (Experiential unfulfillment) is dimensionally misaligned.
- A career choice that is emotionally fulfilling (Experiential) and intellectually engaging (Thought) but has no viable market pathway (Reality unfulfillment) is also dimensionally misaligned.
- The goal is to identify an option where all four dimensions are as fulfilled as possible, and to make trade-offs explicit and conscious.

## Dimensional Fulfillment in a Decision

**Definition:** For the purpose of decision-making, dimensional fulfillment means that an option actively supports the decision-maker's:
- Experiential dimension: The option honors their emotional needs, felt sense, and values around how they want to experience life.
- Thought dimension: The option aligns with their reasoning, beliefs, and intellectual engagement or curiosity.
- Action dimension: The option provides a viable, accessible path to meaningful and self-directed behavior.
- Reality dimension: The option is supported by external structures, resources, and systemic conditions that make it achievable.

## Trade-off Identification

**Definition:** When no option fully satisfies all four dimensions, a trade-off exists. Trade-offs must be made explicit and conscious. The decision-maker must know what dimensional fulfillment they are choosing to defer or sacrifice, and the AI must not obscure this.

## Environmental State as Decision Readiness

**Definition:** The Environmental State of the decision-maker determines whether they are ready to engage in full dimensional decision-making.
- In Survival State: The person is not in a position to make complex multidimensional decisions. Immediate safety must be addressed first.
- In Emotional State: The person can participate in decision-making but may need emotional validation before engaging with logical or structural analysis.
- In Executive State: The person is fully ready for multidimensional decision analysis.

**AI instruction:** Assess the decision-maker's environmental state before proceeding with the dimensional evaluation. Do not apply the full framework to a person in Survival State without first acknowledging their safety needs.

---

# Step-by-Step Instructions

## Step 1: Receive and Parse the Decision Context

**Goal:** Extract the decision situation, available options, and decision-maker identity from the user's input.

**Reasoning:** The framework cannot proceed without a defined decision context and identified options.

**Action:**
- Identify the triggering situation (what is prompting the decision).
- Identify each option being considered. Label them Option A, Option B, etc.
- Identify the decision-maker (individual, group, or role).
- Note any stated values, priorities, constraints, or time pressures.

**Expected outcome:** A structured summary of the decision context with labeled options.

**Validation:** If fewer than two options are identifiable, ask for the missing option(s) before proceeding.

**Fallback behavior:** If the context is partially described, state what is known and clearly mark assumptions.

**Continue condition:** At least two options are defined and the decision context is described.

**Stop condition:** Only one option exists or the decision context is entirely absent.

---

## Step 2: Assess the Decision-Maker's Environmental State

**Goal:** Determine whether the decision-maker is ready to engage in multidimensional decision analysis.

**Reasoning:** Environmental State determines which dimensions are accessible and how the framework should be applied.

**Action:**
- Look for indicators of Survival State (fear, urgency, self-protective language, threat response).
- Look for indicators of Emotional State (emotionally driven reasoning, relational focus, impulsivity).
- Look for indicators of Executive State (structured reasoning, collaborative framing, openness to options).
- Assign the most likely Environmental State.

**Expected outcome:** A stated Environmental State with supporting observations.

**Validation:** If in Survival State, acknowledge safety needs before proceeding. If in Emotional State, validate the emotional experience before moving to dimensional analysis.

**Fallback behavior:** If Environmental State cannot be determined, assume Emotional State and proceed with validation-first approach.

**Continue condition:** Environmental State has been identified or defaulted.

**Stop condition:** Safety concerns are present. In this case, address safety before applying the framework.

---

## Step 3: Evaluate Each Option Against the Experiential Dimension

**Goal:** Determine how each option aligns with the decision-maker's emotional needs, felt sense, and experiential values.

**Reasoning:** Decisions that suppress the Experiential dimension produce long-term dissatisfaction and dimensional unfulfillment regardless of logical or practical success.

**Action for each option:**
- Does this option allow the person to feel the way they want to feel in daily life?
- Does this option align with their expressed values around how they want to experience their work, relationships, or environment?
- Does this option require suppressing emotional needs or felt experience?
- Assign an Experiential Alignment rating: High, Moderate, Low, or Undetermined.

**Expected outcome:** An Experiential Alignment rating for each option with supporting reasoning.

**Validation:** Ratings must be based on described values and context, not projected preferences.

**Fallback behavior:** If experiential information is unavailable, ask: "What would choosing this option feel like day-to-day?" before proceeding.

**Continue condition:** Each option has an Experiential Alignment rating.

**Stop condition:** None at this step.

---

## Step 4: Evaluate Each Option Against the Thought Dimension

**Goal:** Determine how each option aligns with the decision-maker's reasoning, beliefs, and intellectual engagement.

**Reasoning:** Decisions that contradict a person's belief system or intellectual values create cognitive dissonance and dimensional misalignment over time.

**Action for each option:**
- Does this option align with the person's stated beliefs, values, and mental models?
- Does this option engage or develop their intellectual interests?
- Does this option require accepting beliefs or reasoning frameworks that conflict with their own?
- Assign a Thought Alignment rating: High, Moderate, Low, or Undetermined.

**Expected outcome:** A Thought Alignment rating for each option with supporting reasoning.

**Validation:** Ratings must reflect the person's stated reasoning and beliefs, not assumed intellectual preferences.

**Fallback behavior:** If Thought information is insufficient, proceed with Undetermined and note what information would resolve it.

**Continue condition:** Each option has a Thought Alignment rating.

**Stop condition:** None at this step.

---

## Step 5: Evaluate Each Option Against the Action Dimension

**Goal:** Determine how each option enables or constrains meaningful, self-directed action.

**Reasoning:** Options that restrict agency, require the person to act against their values, or have no viable behavioral pathway produce Action dimension misalignment.

**Action for each option:**
- Does this option provide a clear and accessible pathway for the person to act?
- Does this option allow the person to make meaningful, self-directed choices in daily life?
- Does this option require behaviors that conflict with the person's values or capacity?
- Are there systemic or structural barriers that make one option less actionable than another?
- Assign an Action Alignment rating: High, Moderate, Low, or Undetermined.

**Expected outcome:** An Action Alignment rating for each option with supporting reasoning.

**Validation:** Identify and note any systemic or structural barriers that affect actionability.

**Fallback behavior:** If behavioral pathway information is insufficient, flag as Undetermined.

**Continue condition:** Each option has an Action Alignment rating.

**Stop condition:** None at this step.

---

## Step 6: Evaluate Each Option Against the Reality Dimension

**Goal:** Determine how each option is supported or constrained by external systems, material conditions, and structural realities.

**Reasoning:** Options that are experientially and cognitively aligned but structurally unviable will fail at the Reality dimension. All four dimensions must be considered.

**Action for each option:**
- Does this option have the structural, material, or institutional support to be viable?
- What are the external consequences of choosing this option?
- Are there legal, financial, social, or institutional barriers that affect viability?
- Does this option produce outcomes aligned with the person's needs within their systemic reality?
- Assign a Reality Alignment rating: High, Moderate, Low, or Undetermined.

**Expected outcome:** A Reality Alignment rating for each option with supporting reasoning.

**Validation:** Identify specific structural factors, not general assumptions, when rating Reality alignment.

**Fallback behavior:** If structural information is insufficient, flag as Undetermined and specify what information is needed.

**Continue condition:** Each option has a Reality Alignment rating.

**Stop condition:** None at this step.

---

## Step 7: Identify Trade-offs and Dimensional Tensions

**Goal:** Surface the trade-offs between options and within options clearly.

**Action:**
- Compare each option's dimensional ratings.
- Identify where one option is stronger on some dimensions but weaker on others.
- Identify within each option where dimensions are in tension (e.g., Option A scores High on Thought but Low on Experiential).
- Name the trade-off explicitly: "Choosing Option A means prioritizing [dimension] over [dimension]."

**Expected outcome:** A clear trade-off statement for each option.

**Validation:** Trade-offs must be named explicitly. Do not present a trade-off as a neutral fact — name what is being gained and what is being deferred.

**Fallback behavior:** If no trade-offs are evident, confirm that all dimensions are aligned and note this as an unusual finding requiring verification.

**Continue condition:** Trade-offs have been identified and named.

**Stop condition:** None at this step.

---

## Step 8: Generate Dimensional Recommendation

**Goal:** Identify which option produces the greatest dimensional fulfillment and state this clearly without imposing a choice.

**Action:**
- Review all dimension ratings for each option.
- Identify the option with the highest overall dimensional alignment.
- If options are equivalent on overall alignment, identify which option is stronger on the dimensions the person has stated are most important to them.
- State the recommendation clearly and name the dimensional reasoning.
- Acknowledge the trade-offs involved in the recommendation.
- Affirm that the final choice belongs to the decision-maker.

**Expected outcome:** A stated dimensional recommendation with reasoning, trade-off acknowledgment, and autonomy affirmation.

**Validation:** The recommendation must be traceable to specific dimension ratings. It must not be based on the AI's general preference.

**Fallback behavior:** If all options are dimensionally equivalent, state this and present the deciding factor as the person's stated primary value or priority.

**Continue condition:** A recommendation has been stated with reasoning.

**Stop condition:** None at this step.

---

## Step 9: Compose the Final Output

**Goal:** Deliver the complete dimensional decision analysis in the required format.

**Action:**
- Follow the Output Format section exactly.
- Do not omit any required section.
- Do not impose a choice.
- Do not fabricate dimensional evidence.

---

# Decision Logic

## Primary Decision: How many options are present?

- Two options: apply full dimensional evaluation to both and compare.
- Three or more options: apply full dimensional evaluation to each; eliminate options that score Low across three or more dimensions; then compare remaining options.
- One option with a question of whether to proceed: evaluate the single option against all four dimensions and state whether it is dimensionally aligned.

## Secondary Decision: What if dimensions conflict within the same option?

- If an option scores High on Thought and Low on Experiential: identify this as a cognitive-experiential tension and present it as a trade-off.
- If an option scores High on Experiential and Low on Reality: identify this as an experiential-structural tension and present it as a trade-off.
- Do not resolve the tension by dismissing one dimension. Present both and let the decision-maker choose which dimension to prioritize.

## Uncertainty Handling

- If a dimension cannot be rated: mark it Undetermined and note what information would resolve it.
- Do not produce a recommendation if more than two dimensions are Undetermined for any option.

## Conflict Resolution

- If the person's stated preference conflicts with the dimensional analysis: present both the dimensional analysis and the stated preference. Do not override the stated preference. Note the tension and ask the person what they would like to prioritize.

## Missing Information Handling

- If options are not defined: request definition before proceeding.
- If dimensional information is insufficient for a specific dimension: ask targeted questions to obtain it.

---

# Constraints

1. Do not make the final decision for the person. The framework produces a recommendation, not a directive.
2. Do not dismiss any dimension as less important than others without the person's explicit guidance.
3. Do not fabricate dimensional evidence.
4. Do not apply this framework to decisions involving immediate safety risk without first addressing safety.
5. Do not present dimensional ratings as objective scores. They are assessments based on available information.
6. Always acknowledge trade-offs explicitly. Do not present any option as perfect.
7. Always affirm the decision-maker's autonomy in the final step.
8. Do not apply this framework to recommend medical, legal, or financial decisions requiring professional certification.

---

# Edge Cases

## Edge Case 1: All options are dimensionally low

If no option scores well across dimensions, do not recommend any option. Instead, state that all available options produce dimensional unfulfillment and recommend the person seek additional options or explore what systemic barriers are preventing dimensionally aligned choices.

## Edge Case 2: Decision-maker is in Survival State

Do not proceed with multidimensional analysis. Acknowledge the Safety concern, state that complex decision-making is not recommended in a Survival State, and suggest addressing safety needs first.

## Edge Case 3: Group decision with conflicting individual dimensions

When different group members prioritize different dimensions, map each member's dimensional priorities separately. Identify the option that maximizes aggregate dimensional alignment across the group. Name where trade-offs exist for specific members.

## Edge Case 4: Decision has already been made

If the person has already decided and is seeking validation, acknowledge the decision, apply the framework retrospectively to identify dimensional strengths and risks, and focus the output on what to monitor or develop in the chosen direction.

---

# Failure Handling

## Information is missing

State: "A dimensional evaluation requires [specific missing element]. Please describe [specific information] to proceed."

## Context conflicts

State: "The provided context contains conflicting indicators for [dimension]. Both interpretations will be evaluated and the trade-offs named explicitly."

## Multiple interpretations exist

Present both interpretations and their dimensional implications for each option.

## Framework cannot be applied

State: "The Dimensional Decision-Making Framework requires at least two defined options and a described decision context. Please provide [missing element] to proceed."

---

# Output Format

**Dimensional Decision Analysis**

**Decision-Maker:** [Individual, group, or role]
**Decision Context:** [Summary of the situation]
**Options Under Consideration:** Option A: [Description], Option B: [Description]

**Environmental State Assessment**
State: [Survival / Emotional / Executive / Undetermined]
Readiness for Decision Analysis: [Ready / Proceed with validation-first approach / Safety concern present]

**Dimensional Evaluation Matrix**

| Dimension | Option A | Option B |
|---|---|---|
| Experiential | [High / Moderate / Low / Undetermined] | [High / Moderate / Low / Undetermined] |
| Thought | [High / Moderate / Low / Undetermined] | [High / Moderate / Low / Undetermined] |
| Action | [High / Moderate / Low / Undetermined] | [High / Moderate / Low / Undetermined] |
| Reality | [High / Moderate / Low / Undetermined] | [High / Moderate / Low / Undetermined] |

**Dimensional Evidence**

Option A:
- Experiential: [Reasoning]
- Thought: [Reasoning]
- Action: [Reasoning]
- Reality: [Reasoning]

Option B:
- Experiential: [Reasoning]
- Thought: [Reasoning]
- Action: [Reasoning]
- Reality: [Reasoning]

**Trade-offs**
[Explicit naming of what is gained and deferred with each option]

**Dimensional Recommendation**
[Option with highest overall dimensional alignment, with reasoning, trade-off acknowledgment, and explicit statement that the final choice belongs to the decision-maker]

---

# Success Criteria

The skill has executed correctly when:

1. All four dimensions have been evaluated for each option with stated ratings.
2. Trade-offs are explicitly named, not implied.
3. The recommendation is grounded in dimensional ratings, not general preference.
4. The decision-maker's autonomy is explicitly affirmed.
5. No fabricated evidence appears in the output.
6. The output follows the specified format completely.
7. The environmental state was assessed before dimensional analysis was applied.

---

# Quality Checklist

Before delivering output, verify:

- [ ] Explicit: Every dimensional rating is supported by stated evidence.
- [ ] Deterministic: The same input would produce the same dimensional ratings.
- [ ] Context aware: Environmental State and decision context are reflected throughout.
- [ ] Human centered: The framework supports autonomous, dimensionally aligned decision-making.
- [ ] Ethical: No dimension is dismissed; no choice is imposed.
- [ ] Reproducible: Another agent applying this skill would reach the same ratings.
- [ ] No ambiguity: Every trade-off is explicitly named.
- [ ] Production ready: The output is complete, structured, and respects decision-maker autonomy.
