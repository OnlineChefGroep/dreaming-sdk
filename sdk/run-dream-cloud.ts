/**
 * SDK driver wrapper for dream-eval cloud runs.
 *
 * Thin wrapper that delegates to the dreaming plugin's own cloud runner at
 * `$DREAM_PLUGIN_ROOT/sdk/run-dream-cloud.ts`. This repo is an integration kit,
 * not a fork — the real runner lives in the plugin install.
 *
 * Recursion guard: if `DREAM_PLUGIN_ROOT` is pointed at this SDK repo, the
 * naive version would spawn itself forever. We guard with an env sentinel and
 * an absolute-path identity check.
 */

import { spawn } from "node:child_process";
import { join, resolve } from "node:path";
import { homedir } from "node:os";
import { existsSync, realpathSync } from "node:fs";
import { fileURLToPath } from "node:url";

const RECURSION_GUARD_ENV = "DREAM_CLOUD_RUNNER_ACTIVE";

const PLUGIN_ROOT =
  process.env.DREAM_PLUGIN_ROOT ||
  join(homedir(), ".cursor", "plugins", "local", "dreaming");

const CLOUD_RUNNER = join(PLUGIN_ROOT, "sdk", "run-dream-cloud.ts");

function canonical(p: string): string {
  try {
    return realpathSync(p);
  } catch {
    return resolve(p);
  }
}

function main(): void {
  if (process.env[RECURSION_GUARD_ENV] === "1") {
    console.error(
      `Fatal: ${RECURSION_GUARD_ENV}=1 is already set — refusing to re-spawn (recursion guard).`,
    );
    process.exit(1);
  }

  const thisFile = canonical(fileURLToPath(import.meta.url));
  const targetRunner = canonical(CLOUD_RUNNER);
  if (thisFile === targetRunner) {
    console.error(
      "Fatal: refusing to spawn self — DREAM_PLUGIN_ROOT points at the SDK repo, not the plugin.",
    );
    console.error(`  Set DREAM_PLUGIN_ROOT to your dreaming plugin install.`);
    process.exit(1);
  }

  if (!existsSync(PLUGIN_ROOT)) {
    console.error(`Fatal: dreaming plugin not found at ${PLUGIN_ROOT}`);
    process.exit(1);
  }

  if (!existsSync(CLOUD_RUNNER)) {
    console.error(`Fatal: cloud runner not found at ${CLOUD_RUNNER}`);
    process.exit(1);
  }

  console.log(`Starting dream-eval cloud run via plugin at ${PLUGIN_ROOT}...`);

  const args = process.argv.slice(2);
  const child = spawn(
    process.execPath,
    ["--experimental-strip-types", CLOUD_RUNNER, ...args],
    {
      stdio: "inherit",
      env: {
        ...process.env,
        DREAM_PLUGIN_ROOT: PLUGIN_ROOT,
        [RECURSION_GUARD_ENV]: "1",
      },
    },
  );

  child.on("error", (err) => {
    console.error(`Failed to start cloud runner: ${err.message}`);
    process.exit(1);
  });

  child.on("exit", (code, signal) => {
    if (signal) {
      console.error(`Cloud runner terminated by signal ${signal}`);
      process.exit(1);
    }
    process.exit(code ?? 1);
  });
}

main();
