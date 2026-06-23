/**
 * Cursor SDK Cloud Wrapper
 * delegates execution to the dreaming plugin's cloud driver.
 */

import { join } from "path";
import { homedir } from "os";
import { existsSync } from "fs";
import { spawn } from "child_process";

const PLUGIN_ROOT = process.env.DREAM_PLUGIN_ROOT || join(homedir(), ".cursor", "plugins", "local", "dreaming");
const CLOUD_DRIVER = join(PLUGIN_ROOT, "sdk", "run-dream-cloud.ts");

async function run() {
  if (!existsSync(CLOUD_DRIVER)) {
    console.error(`Error: Cloud driver not found at ${CLOUD_DRIVER}`);
    process.exit(1);
  }

  console.log(`Delegating to ${CLOUD_DRIVER}...`);

  const child = spawn("node", ["--experimental-strip-types", CLOUD_DRIVER, ...process.argv.slice(2)], {
    stdio: "inherit",
    env: {
      ...process.env,
      DREAM_PLUGIN_ROOT: PLUGIN_ROOT,
    },
  });

  child.on("exit", (code) => {
    process.exit(code ?? 0);
  });
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
