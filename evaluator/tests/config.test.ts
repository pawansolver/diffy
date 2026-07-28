import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import type { ProfileConfig } from "../src/config.js";
import { loadQuestions } from "../src/config.js";

const profile: ProfileConfig = {
  name: "test",
  questions: "questions.json",
  system_prompt: "Use MCP tools.",
  dimensions: [{ name: "tool_use", description: "" }],
};

function writeQuestions(value: unknown): string {
  const directory = mkdtempSync(join(tmpdir(), "dhee-eval-"));
  writeFileSync(join(directory, "questions.json"), JSON.stringify(value), "utf8");
  return directory;
}

test("loadQuestions validates and returns a valid question set", () => {
  const directory = writeQuestions([
    {
      id: "q01",
      category: "discovery",
      question: "List available skills",
      expectation: "Calls list_skills",
    },
  ]);

  assert.equal(loadQuestions(profile, directory)[0].id, "q01");
});

test("loadQuestions rejects duplicate question IDs", () => {
  const directory = writeQuestions([
    { id: "q01", question: "First" },
    { id: "q01", question: "Second" },
  ]);

  assert.throws(() => loadQuestions(profile, directory), /question ids must be unique/);
});

test("loadQuestions rejects malformed question fields", () => {
  const directory = writeQuestions([{ id: "", question: "" }]);

  assert.throws(() => loadQuestions(profile, directory), /Invalid questions file/);
});
