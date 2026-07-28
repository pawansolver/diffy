import { resolve } from "node:path";
import { loadConfig, loadQuestions } from "../src/config.js";

const configPath = resolve(process.argv[2] || "skills_eval_config.json");
const { config, dir } = loadConfig(configPath);

for (const profile of config.profiles) {
  loadQuestions(profile, dir);
}

const providerNames = new Set(Object.keys(config.providers || {}));
for (const [name, provider] of Object.entries(config.providers || {})) {
  if (provider.api_key) {
    throw new Error(
      `Provider '${name}' contains an inline API key; use api_key_env and a secret environment variable`,
    );
  }
}
for (const model of config.models) {
  if (!providerNames.has(model.provider) && !(model.provider === "openrouter" && config.openrouter)) {
    throw new Error(`Model '${model.id}' references unknown provider '${model.provider}'`);
  }
}
if (
  !providerNames.has(config.judge.provider) &&
  !(config.judge.provider === "openrouter" && config.openrouter)
) {
  throw new Error(`Judge references unknown provider '${config.judge.provider}'`);
}

console.log(
  `Configuration valid: ${config.profiles.length} profile(s), ` +
    `${config.models.length} model(s), ${providerNames.size} provider(s).`,
);
