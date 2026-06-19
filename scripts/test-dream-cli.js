"use strict";

const assert = require("node:assert/strict");
const { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } = require("node:fs");
const { tmpdir } = require("node:os");
const { join } = require("node:path");

const {
  expandHome,
  inspect,
  parseArgs,
  resolvePluginRoot,
  run,
  supportsStripTypes,
} = require("../lib/dream-cli");

function capture() {
  let text = "";
  return {
    stream: {
      write(chunk) {
        text += chunk;
      },
    },
    get text() {
      return text;
    },
  };
}

function withTempPlugin(fn) {
  const root = mkdtempSync(join(tmpdir(), "dream-plugin-"));
  mkdirSync(join(root, "cli"), { recursive: true });
  mkdirSync(join(root, "sdk"), { recursive: true });
  writeFileSync(
    join(root, "cli", "dream.mjs"),
    [
      "import { writeFileSync } from 'node:fs';",
      "writeFileSync(process.env.DREAM_CLI_TEST_OUT, JSON.stringify({",
      "  argv: process.argv.slice(2),",
      "  pluginRoot: process.env.DREAM_PLUGIN_ROOT",
      "}));",
      "process.exit(7);",
    ].join("\n"),
  );
  writeFileSync(join(root, "sdk", "run-dream-cloud.ts"), "console.log('cloud');\n");
  try {
    return fn(root);
  } finally {
    rmSync(root, { force: true, recursive: true });
  }
}

assert.equal(expandHome("~/demo").endsWith("/demo"), true);
assert.equal(parseArgs(["doctor", "--json"]).command, "doctor");
assert.equal(parseArgs(["--version"]).command, "version");
assert.equal(typeof supportsStripTypes(), "boolean");

const missing = mkdtempSync(join(tmpdir(), "dream-missing-"));
rmSync(missing, { force: true, recursive: true });
assert.equal(resolvePluginRoot({ DREAM_PLUGIN_ROOT: missing }), missing);
const missingReport = inspect({ env: { DREAM_PLUGIN_ROOT: missing }, packageRoot: process.cwd() });
assert.equal(missingReport.ok, false);
assert.equal(missingReport.status.plugin_cli.exists, false);

const helpOut = capture();
assert.equal(run(["--help"], { stdout: helpOut.stream, packageRoot: process.cwd() }), 0);
assert.match(helpOut.text, /Plugin pass-through commands/);

const unknownErr = capture();
assert.equal(
  run(["does-not-exist"], {
    stderr: unknownErr.stream,
    stdout: capture().stream,
    packageRoot: process.cwd(),
  }),
  2,
);
assert.match(unknownErr.text, /Unknown dream command/);

withTempPlugin((pluginRoot) => {
  const outFile = join(pluginRoot, "called.json");
  const stdout = capture();
  const code = run(["test", "--json"], {
    env: { DREAM_PLUGIN_ROOT: pluginRoot, DREAM_CLI_TEST_OUT: outFile },
    packageRoot: process.cwd(),
    stdout: stdout.stream,
  });
  assert.equal(code, 7);
  const called = JSON.parse(readFileSync(outFile, "utf8"));
  assert.deepEqual(called.argv, ["test", "--json"]);
  assert.equal(called.pluginRoot, pluginRoot);

  const doctorOut = capture();
  assert.equal(
    run(["doctor", "--json"], {
      env: { DREAM_PLUGIN_ROOT: pluginRoot },
      packageRoot: process.cwd(),
      stdout: doctorOut.stream,
    }),
    0,
  );
  const doctor = JSON.parse(doctorOut.text);
  assert.equal(doctor.ok, true);
  assert.equal(doctor.status.plugin_cli.exists, true);
});

console.log("dream-cli tests passed");
