/**
 * SDK driver wrapper for dream-eval cloud runs.
 * This script is a thin wrapper that expects the dreaming plugin to be available
 * at ~/.cursor/plugins/local/dreaming/.
 */

import { spawn } from 'node:child_process';
import { join } from 'node:path';
import { homedir } from 'node:os';

const PLUGIN_ROOT = process.env.DREAM_PLUGIN_ROOT || join(homedir(), '.cursor', 'plugins', 'local', 'dreaming');
const CLOUD_RUNNER = join(PLUGIN_ROOT, 'sdk', 'run-dream-cloud.ts');

async function main() {
  console.log(`Starting dream-eval cloud run via plugin at ${PLUGIN_ROOT}...`);

  const args = process.argv.slice(2);

  // In a real environment, we'd use --experimental-strip-types to run the plugin's TS directly
  const child = spawn('node', ['--experimental-strip-types', CLOUD_RUNNER, ...args], {
    stdio: 'inherit',
    env: {
      ...process.env,
      DREAM_PLUGIN_ROOT: PLUGIN_ROOT
    }
  });

  child.on('exit', (code) => {
    process.exit(code ?? 1);
  });
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
