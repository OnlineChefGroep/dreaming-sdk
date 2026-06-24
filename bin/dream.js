#!/usr/bin/env node

const { spawn } = require("child_process");
const { join, resolve } = require("path");
const { homedir } = require("os");
const { existsSync } = require("fs");

const DEFAULT_PLUGIN_ROOT = join(homedir(), ".cursor", "plugins", "local", "dreaming");
const PLUGIN_ROOT = process.env.DREAM_PLUGIN_ROOT || DEFAULT_PLUGIN_ROOT;
const CLI_PATH = join(PLUGIN_ROOT, "cli", "dream.mjs");

if (!existsSync(CLI_PATH)) {
  // Plugin not installed — run local dream CLI (TUI/agent mode)
  const { run } = require("../lib/dream-cli");
  process.exit(run(process.argv.slice(2), { binFile: __filename }));
}

// Plugin available — spawn it and optionally validate results
const args = process.argv.slice(2);

async function validateLatestResults() {
  try {
    const { readFileSync, readdirSync } = require("fs");
    const Ajv = (await import("ajv")).default;
    const addFormats = (await import("ajv-formats")).default;
    const ajv = new Ajv({ allErrors: true });
    addFormats(ajv);

    const resultsDir = resolve("eval/results");
    if (!existsSync(resultsDir)) return;
    const runs = readdirSync(resultsDir).sort().reverse();
    if (runs.length === 0) return;
    const lastRun = runs[0];
    const metricsPath = join(resultsDir, lastRun, "metrics.json");
    const metricsSchema = resolve(__dirname, "../schema/metrics.schema.json");
    if (!existsSync(metricsPath) || !existsSync(metricsSchema)) return;

    const data = JSON.parse(readFileSync(metricsPath, "utf-8"));
    const schema = JSON.parse(readFileSync(metricsSchema, "utf-8"));
    const validate = ajv.compile(schema);
    const valid = validate(data);
    if (!valid) {
      console.error(`Schema validation failed for ${metricsPath}:`);
      console.error(ajv.errorsText(validate.errors));
    } else {
      console.log(`Metrics validated: ${metricsPath}`);
    }
  } catch {
    // best-effort
  }
}

const child = spawn("node", [CLI_PATH, ...args], {
  stdio: "inherit",
  env: {
    ...process.env,
    DREAMING_DIR: process.env.DREAMING_DIR || join(homedir(), ".cursor", "dreaming"),
  }
});

child.on("exit", (code) => {
  if (code === 0 && args.includes("eval")) {
    validateLatestResults().then(() => process.exit(code ?? 0));
  } else {
    process.exit(code ?? 0);
  }
});
