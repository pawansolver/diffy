import assert from "node:assert/strict";
import test from "node:test";
import type { ProfileConfig } from "../src/config.js";
import { parseJudgeScores } from "../src/judge.js";

const dimensions: ProfileConfig["dimensions"] = [
  { name: "tool_use", description: "Correct tool usage" },
  { name: "faithfulness", description: "Grounded answer" },
];

test("parseJudgeScores accepts a valid rubric response", () => {
  const result = parseJudgeScores(
    '```json\n{"tool_use":5,"faithfulness":4,"notes":"Grounded and correct"}\n```',
    dimensions,
  );

  assert.deepEqual(result, {
    tool_use: 5,
    faithfulness: 4,
    notes: "Grounded and correct",
  });
});

test("parseJudgeScores rejects scores outside the 1-5 range", () => {
  assert.throws(
    () =>
      parseJudgeScores(
        '{"tool_use":6,"faithfulness":4,"notes":"Invalid range"}',
        dimensions,
      ),
    /schema validation/,
  );
});

test("parseJudgeScores rejects missing and unexpected dimensions", () => {
  assert.throws(
    () =>
      parseJudgeScores(
        '{"tool_use":5,"answer_quality":5,"notes":"Wrong shape"}',
        dimensions,
      ),
    /schema validation/,
  );
});

test("parseJudgeScores rejects non-JSON responses", () => {
  assert.throws(
    () => parseJudgeScores("The answer deserves five.", dimensions),
    /did not contain a JSON object/,
  );
});
