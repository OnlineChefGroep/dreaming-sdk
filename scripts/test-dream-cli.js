"use strict";

const assert = require("node:assert/strict");
const { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } = require("node:fs");
const { tmpdir } = require("node:os");
const { join } = require("node:path");

const {
  buildAgentEnvelope,
  createTuiModel,
  decodeKey,
  expandHome,
  inspect,
  nextTuiIndex,
  parseArgs,
  renderTui,
  resolvePluginRoot,
  run,
  runDreamFlow,
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
      "const payload = {",
      "  argv: process.argv.slice(2),",
      "  pluginRoot: process.env.DREAM_PLUGIN_ROOT",
      "};",
      "if (process.env.DREAM_CLI_TEST_OUT) writeFileSync(process.env.DREAM_CLI_TEST_OUT, JSON.stringify(payload));",
      "if (process.argv[2] === 'test') { console.log(JSON.stringify({ hard_fail: false, tests: { hash_determinism: { pass: true } } })); process.exit(process.env.DREAM_CLI_TEST_EXIT ? Number(process.env.DREAM_CLI_TEST_EXIT) : 0); }",
      "if (process.argv[2] === 'eval') { console.log(JSON.stringify({ run_id: 'fake-run', prepared: true, argv: process.argv.slice(2) })); process.exit(0); }",
      "if (process.argv[2] === 'decisions') { console.log(JSON.stringify({ decisions_present: true, rows: 0 })); process.exit(0); }",
      "console.log(JSON.stringify(payload));",
      "process.exit(0);",
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
assert.equal(parseArgs(["run", "--dry-run", "--json"]).dryRun, true);
assert.equal(typeof supportsStripTypes(), "boolean");
assert.equal(decodeKey("j"), "j");
assert.equal(decodeKey("\u001b[A"), "up");
assert.equal(nextTuiIndex(0, "up", 3), 2);
assert.equal(nextTuiIndex(2, "down", 3), 0);

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

const agentEnvelope = buildAgentEnvelope({
  env: { DREAM_PLUGIN_ROOT: missing },
  packageRoot: process.cwd(),
});
assert.equal(agentEnvelope.protocol, "dream-cli-agent/v1");
assert.equal(agentEnvelope.ok, false);
assert.match(agentEnvelope.recommended_next_actions.join("\n"), /DREAM_PLUGIN_ROOT/);

const tuiModel = createTuiModel({ env: { DREAM_PLUGIN_ROOT: missing }, packageRoot: process.cwd() });
assert.match(renderTui(tuiModel, { clear: false }), /dream terminal motion/);
assert.match(renderTui(tuiModel, { clear: false }), /Doctor - inspect plugin/);

withTempPlugin((pluginRoot) => {
  const outFile = join(pluginRoot, "called.json");
  const stdout = capture();
  const code = run(["test", "--json"], {
    env: { DREAM_PLUGIN_ROOT: pluginRoot, DREAM_CLI_TEST_OUT: outFile },
    packageRoot: process.cwd(),
    stdio: "pipe",
    stdout: stdout.stream,
  });
  assert.equal(code, 0);
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

  const capabilitiesOut = capture();
  assert.equal(
    run(["capabilities", "--json"], {
      env: { DREAM_PLUGIN_ROOT: pluginRoot },
      packageRoot: process.cwd(),
      stdout: capabilitiesOut.stream,
    }),
    0,
  );
  const capabilities = JSON.parse(capabilitiesOut.text);
  assert.equal(capabilities.protocol, "dream-cli/v1");
  assert.equal(capabilities.report.ok, true);

  const agentOut = capture();
  assert.equal(
    run(["agent", "--json"], {
      env: { DREAM_PLUGIN_ROOT: pluginRoot },
      packageRoot: process.cwd(),
      stdout: agentOut.stream,
    }),
    0,
  );
  assert.equal(JSON.parse(agentOut.text).ok, true);

  const tuiOut = capture();
  assert.equal(
    run(["tui", "--json"], {
      env: { DREAM_PLUGIN_ROOT: pluginRoot },
      packageRoot: process.cwd(),
      stdout: tuiOut.stream,
    }),
    0,
  );
  assert.equal(JSON.parse(tuiOut.text).items.length > 3, true);

  const dryRun = runDreamFlow(["--dry-run", "--corpus", "eval/golden-corpus"], {
    env: { DREAM_PLUGIN_ROOT: pluginRoot },
    packageRoot: process.cwd(),
  });
  assert.equal(dryRun.ok, true);
  assert.equal(dryRun.dry_run, true);
  assert.deepEqual(dryRun.plan[1].args, ["--corpus", "eval/golden-corpus", "--dry-run", "--json"]);

  const flow = runDreamFlow([], {
    env: { DREAM_PLUGIN_ROOT: pluginRoot },
    packageRoot: process.cwd(),
  });
  assert.equal(flow.ok, true);
  assert.equal(flow.steps.length, 3);
  assert.equal(flow.steps[0].json.hard_fail, false);
  assert.equal(flow.steps[1].json.run_id, "fake-run");
});

console.log("dream-cli tests passed");
