#!/usr/bin/env node

import { spawn } from 'child_process';
import { join, resolve } from 'path';
import { homedir } from 'os';
import { existsSync, readFileSync, readdirSync } from 'fs';
import Ajv from 'ajv';
import addFormats from 'ajv-formats';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PLUGIN_ROOT = process.env.DREAM_PLUGIN_ROOT || join(homedir(), '.cursor', 'plugins', 'local', 'dreaming');
const CLI_PATH = join(PLUGIN_ROOT, 'cli', 'dream.mjs');

const ajv = new Ajv({ allErrors: true });
addFormats(ajv);

function validateResult(dir) {
  const metricsPath = join(dir, 'metrics.json');
  const metricsSchema = resolve(__dirname, '../schema/metrics.schema.json');

  if (existsSync(metricsPath) && existsSync(metricsSchema)) {
    const data = JSON.parse(readFileSync(metricsPath, 'utf-8'));
    const schema = JSON.parse(readFileSync(metricsSchema, 'utf-8'));
    const validate = ajv.compile(schema);
    const valid = validate(data);
    if (!valid) {
      console.error(`❌ Schema validation failed for ${metricsPath}:`);
      console.error(ajv.errorsText(validate.errors));
    } else {
      console.log(`✅ ${metricsPath} is valid.`);
    }
  }
}

if (!existsSync(CLI_PATH)) {
  console.error(`Error: Dreaming plugin not found at ${PLUGIN_ROOT}`);
  console.error('Please install the plugin or set DREAM_PLUGIN_ROOT.');
  process.exit(1);
}

const args = process.argv.slice(2);
const child = spawn('node', [CLI_PATH, ...args], {
  stdio: 'inherit',
  env: {
    ...process.env,
    DREAMING_DIR: process.env.DREAMING_DIR || join(homedir(), '.cursor', 'dreaming'),
  }
});

child.on('exit', (code) => {
  if (code === 0 && args.includes('eval')) {
    // Basic heuristic to find the latest eval results and validate
    const resultsDir = resolve('eval/results');
    if (existsSync(resultsDir)) {
      const runs = readdirSync(resultsDir).sort().reverse();
      if (runs.length > 0) {
        validateResult(join(resultsDir, runs[0]));
      }
    }
  }
  process.exit(code ?? 0);
});
