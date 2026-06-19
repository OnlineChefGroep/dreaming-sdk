"use strict";

const { existsSync, readSync, statSync } = require("node:fs");
const { homedir } = require("node:os");
const { dirname, join, resolve } = require("node:path");
const { spawnSync } = require("node:child_process");

const DEFAULT_PLUGIN_ROOT = join(homedir(), ".cursor", "plugins", "local", "dreaming");
const PASS_THROUGH_COMMANDS = new Set([
  "test",
  "eval",
  "decisions",
  "status",
  "scope",
  "index",
]);

const TUI_ITEMS = [
  { label: "Doctor - inspect plugin and runtime", command: "doctor", args: [] },
  { label: "Test - run deterministic plugin gates", command: "test", args: [] },
  { label: "Eval dry-run - prepare a run plan", command: "eval", args: ["--dry-run"] },
  { label: "Run - test + eval + decisions flow", command: "run", args: [] },
  { label: "Status - live pending counts", command: "status", args: [] },
  { label: "Scope - list in-scope pending sessions", command: "scope", args: [] },
  { label: "Index - inspect live index summary", command: "index", args: [] },
  { label: "Which - print plugin CLI path", command: "which", args: [] },
  { label: "Quit", command: "quit", args: [] },
];

function expandHome(input) {
  if (!input || input === "~") {
    return input === "~" ? homedir() : input;
  }
  if (input.startsWith("~/")) {
    return join(homedir(), input.slice(2));
  }
  return input;
}

function resolvePluginRoot(env = process.env) {
  return resolve(expandHome(env.DREAM_PLUGIN_ROOT || DEFAULT_PLUGIN_ROOT));
}

function packageRootFromBin(binFile = __filename) {
  return resolve(dirname(binFile), "..");
}

function resolvePaths(options = {}) {
  const pluginRoot = resolvePluginRoot(options.env);
  const packageRoot = options.packageRoot || packageRootFromBin(options.binFile);
  return {
    packageRoot,
    pluginRoot,
    pluginCli: join(pluginRoot, "cli", "dream.mjs"),
    pluginCloudRunner: join(pluginRoot, "sdk", "run-dream-cloud.ts"),
    sdkCloudWrapper: join(packageRoot, "sdk", "run-dream-cloud.ts"),
  };
}

function pathStatus(path) {
  if (!existsSync(path)) {
    return { exists: false, type: "missing" };
  }
  const stat = statSync(path);
  return {
    exists: true,
    type: stat.isDirectory() ? "directory" : stat.isFile() ? "file" : "other",
  };
}

function nodeMajor(version = process.versions.node) {
  return Number.parseInt(String(version).split(".")[0], 10);
}

function supportsStripTypes(version = process.versions.node) {
  const major = nodeMajor(version);
  return Number.isFinite(major) && major >= 22;
}

function parseArgs(argv) {
  const args = [...argv];
  const json = args.includes("--json");
  const dryRun = args.includes("--dry-run");
  const help = args.includes("--help") || args.includes("-h");
  const version = args.includes("--version") || args.includes("-v");
  const command = args.find((arg) => !arg.startsWith("-")) || (version ? "version" : help ? "help" : "");
  const rest = command ? args.slice(args.indexOf(command) + 1) : [];
  return { command, rest, json, dryRun, help, version };
}

function usage() {
  return [
    "@onlinechefgroep/dream-cli",
    "",
    "Usage:",
    "  dream <command> [options]",
    "",
    "Local commands:",
    "  help                 Show this help",
    "  version              Print package version",
    "  doctor [--json]      Inspect plugin discovery and local runtime support",
    "  which [--json]       Print resolved plugin paths",
    "  capabilities [--json] Print human/agent command capabilities",
    "  agent [--json]       Print agent protocol envelope and next actions",
    "  tui [--json]         Open the terminal motion menu for humans",
    "  run [--json]         Run test -> eval -> decisions through the plugin",
    "  cloud [...args]      Run sdk/run-dream-cloud.ts through the SDK wrapper",
    "",
    "Plugin pass-through commands:",
    "  test | eval | decisions | status | scope | index",
    "",
    "Environment:",
    `  DREAM_PLUGIN_ROOT   Defaults to ${DEFAULT_PLUGIN_ROOT}`,
  ].join("\n");
}

function buildCapabilities(options = {}) {
  const report = inspect(options);
  return {
    protocol: "dream-cli/v1",
    modes: {
      human: {
        command: "dream tui",
        interactive: true,
        keys: ["up", "down", "j", "k", "enter", "q"],
      },
      agent: {
        command: "dream agent --json",
        machine_readable: true,
        stable_json: true,
      },
    },
    local_commands: [
      { name: "doctor", json: true, description: "Inspect plugin discovery and runtime support." },
      { name: "which", json: true, description: "Print resolved plugin paths." },
      { name: "capabilities", json: true, description: "Describe human and agent command surfaces." },
      { name: "agent", json: true, description: "Return a machine-readable agent envelope." },
      { name: "tui", json: true, description: "Open or describe the human terminal menu." },
      { name: "run", json: true, description: "Run test -> eval -> decisions via plugin CLI." },
      { name: "cloud", json: false, description: "Run the SDK cloud wrapper." },
    ],
    plugin_commands: [...PASS_THROUGH_COMMANDS].map((name) => ({
      name,
      json: true,
      invocation: `dream ${name} --json`,
    })),
    report,
  };
}

function buildAgentEnvelope(options = {}) {
  const capabilities = buildCapabilities(options);
  const ok = capabilities.report.ok;
  return {
    protocol: "dream-cli-agent/v1",
    ok,
    summary: ok
      ? "Dreaming plugin discovered. Agent commands can be delegated."
      : "Dreaming plugin is not installed or DREAM_PLUGIN_ROOT is misconfigured.",
    recommended_next_actions: ok
      ? [
          "dream test --json",
          "dream eval --dry-run --json",
          "dream run --json",
        ]
      : [
          "Install the dreaming plugin at ~/.cursor/plugins/local/dreaming",
          "Or set DREAM_PLUGIN_ROOT to the plugin install path",
          "Run dream doctor --json again",
        ],
    capabilities,
  };
}

function readPackageVersion(packageRoot) {
  try {
    return require(join(packageRoot, "package.json")).version || "0.0.0";
  } catch {
    return "0.0.0";
  }
}

function inspect(options = {}) {
  const paths = resolvePaths(options);
  return {
    ok: existsSync(paths.pluginRoot) && existsSync(paths.pluginCli),
    node: {
      version: process.versions.node,
      supports_experimental_strip_types: supportsStripTypes(),
    },
    paths: {
      package_root: paths.packageRoot,
      plugin_root: paths.pluginRoot,
      plugin_cli: paths.pluginCli,
      plugin_cloud_runner: paths.pluginCloudRunner,
      sdk_cloud_wrapper: paths.sdkCloudWrapper,
    },
    status: {
      plugin_root: pathStatus(paths.pluginRoot),
      plugin_cli: pathStatus(paths.pluginCli),
      plugin_cloud_runner: pathStatus(paths.pluginCloudRunner),
      sdk_cloud_wrapper: pathStatus(paths.sdkCloudWrapper),
    },
  };
}

function printJson(value, stdout = process.stdout) {
  stdout.write(`${JSON.stringify(value, null, 2)}\n`);
}

function printDoctor(report, stdout = process.stdout) {
  stdout.write(`dream plugin root : ${report.paths.plugin_root}\n`);
  stdout.write(`plugin CLI        : ${report.status.plugin_cli.exists ? "ok" : "missing"}\n`);
  stdout.write(
    `cloud runner      : ${report.status.plugin_cloud_runner.exists ? "ok" : "missing"}\n`,
  );
  stdout.write(
    `SDK wrapper       : ${report.status.sdk_cloud_wrapper.exists ? "ok" : "missing"}\n`,
  );
  stdout.write(
    `Node strip types  : ${report.node.supports_experimental_strip_types ? "ok" : "upgrade to Node 22+"}\n`,
  );
}

function printCapabilities(capabilities, stdout = process.stdout) {
  stdout.write("dream CLI capabilities\n");
  stdout.write(`plugin status : ${capabilities.report.ok ? "ok" : "missing"}\n`);
  stdout.write("human mode    : dream tui\n");
  stdout.write("agent mode    : dream agent --json\n");
  stdout.write("run flow      : dream run --json\n");
  stdout.write(`plugin root   : ${capabilities.report.paths.plugin_root}\n`);
}

function spawnNode(args, options = {}) {
  return spawnSync(process.execPath, args, {
    stdio: options.stdio || "inherit",
    env: options.env || process.env,
  });
}

function spawnNodeCapture(args, options = {}) {
  return spawnSync(process.execPath, args, {
    encoding: "utf8",
    env: options.env || process.env,
  });
}

function exitFromSpawn(result) {
  if (result.error) {
    console.error(`Failed to start process: ${result.error.message}`);
    return 1;
  }
  if (result.signal) {
    console.error(`Process terminated by signal ${result.signal}`);
    return 1;
  }
  return result.status ?? 1;
}

function delegateToPlugin(command, rest, options = {}) {
  const paths = resolvePaths(options);
  if (!existsSync(paths.pluginCli)) {
    console.error(`Fatal: dreaming plugin CLI not found at ${paths.pluginCli}`);
    console.error("Install the plugin or set DREAM_PLUGIN_ROOT to the plugin install path.");
    return 1;
  }

  const pluginArgs = [...rest];
  if (options.json && !pluginArgs.includes("--json")) {
    pluginArgs.push("--json");
  }

  const result = spawnNode([paths.pluginCli, command, ...pluginArgs], {
    env: {
      ...process.env,
      ...(options.env || {}),
      DREAM_PLUGIN_ROOT: paths.pluginRoot,
    },
    stdio: options.stdio,
  });
  return exitFromSpawn(result);
}

function parseJsonMaybe(text) {
  if (!text || !text.trim()) {
    return null;
  }
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function runPluginStep(paths, command, args, options = {}) {
  const result = spawnNodeCapture([paths.pluginCli, command, ...args], {
    env: {
      ...process.env,
      ...(options.env || {}),
      DREAM_PLUGIN_ROOT: paths.pluginRoot,
    },
  });
  return {
    command,
    args,
    exit_code: exitFromSpawn(result),
    stdout: result.stdout || "",
    stderr: result.stderr || "",
    json: parseJsonMaybe(result.stdout),
  };
}

function runDreamFlow(rest, options = {}) {
  const paths = resolvePaths(options);
  const evalArgs = rest.filter((arg) => arg !== "--json");
  const dryRun = evalArgs.includes("--dry-run") || options.dryRun;
  const cleanEvalArgs = evalArgs.filter((arg) => arg !== "--dry-run");
  const plannedEvalArgs = dryRun ? [...cleanEvalArgs, "--dry-run", "--json"] : [...cleanEvalArgs, "--json"];
  const plan = [
    { command: "test", args: ["--json"], required: true },
    { command: "eval", args: plannedEvalArgs, required: true },
    { command: "decisions", args: ["--json"], required: false },
  ];

  if (dryRun) {
    return {
      ok: true,
      dry_run: true,
      plugin_root: paths.pluginRoot,
      plan,
      steps: [],
    };
  }

  if (!existsSync(paths.pluginCli)) {
    return {
      ok: false,
      error: "plugin_cli_missing",
      message: `Dreaming plugin CLI not found at ${paths.pluginCli}`,
      plugin_root: paths.pluginRoot,
      plan,
      steps: [],
    };
  }

  const steps = [];
  for (const item of plan) {
    const step = runPluginStep(paths, item.command, item.args, options);
    steps.push(step);
    if (step.exit_code !== 0 && item.required) {
      return {
        ok: false,
        error: "required_step_failed",
        failed_step: item.command,
        plugin_root: paths.pluginRoot,
        steps,
      };
    }
    if (item.command === "test" && step.json && step.json.hard_fail) {
      return {
        ok: false,
        error: "hard_fail",
        failed_step: item.command,
        plugin_root: paths.pluginRoot,
        steps,
      };
    }
  }

  return {
    ok: steps.every((step) => step.exit_code === 0),
    dry_run: false,
    plugin_root: paths.pluginRoot,
    steps,
  };
}

function printRunFlow(flow, stdout = process.stdout) {
  stdout.write(`dream run: ${flow.ok ? "ok" : "failed"}\n`);
  if (flow.dry_run) {
    stdout.write("dry-run plan:\n");
    for (const step of flow.plan) {
      stdout.write(`  - ${step.command} ${step.args.join(" ")}\n`);
    }
    return;
  }
  if (flow.error) {
    stdout.write(`error: ${flow.error}\n`);
  }
  for (const step of flow.steps) {
    stdout.write(`  ${step.command}: exit ${step.exit_code}\n`);
  }
}

function createTuiModel(options = {}) {
  return {
    title: "dream terminal motion",
    subtitle: "Human control surface for the dreaming plugin",
    selected: options.selected || 0,
    items: TUI_ITEMS,
    report: inspect(options),
  };
}

function renderTui(model, options = {}) {
  const clear = options.clear === false ? "" : "\x1b[2J\x1b[H";
  const lines = [
    `${clear}${model.title}`,
    model.subtitle,
    "",
    `plugin: ${model.report.ok ? "ok" : "missing"} (${model.report.paths.plugin_root})`,
    "",
  ];
  model.items.forEach((item, index) => {
    const cursor = index === model.selected ? ">" : " ";
    lines.push(`${cursor} ${item.label}`);
  });
  lines.push("");
  lines.push("keys: up/down or j/k to move, enter to run, q to quit");
  return `${lines.join("\n")}\n`;
}

function nextTuiIndex(current, key, length) {
  if (key === "up" || key === "k") {
    return (current - 1 + length) % length;
  }
  if (key === "down" || key === "j") {
    return (current + 1) % length;
  }
  return current;
}

function decodeKey(input) {
  if (input === "\u0003") return "quit";
  if (input === "q") return "quit";
  if (input === "\r" || input === "\n") return "enter";
  if (input === "j") return "j";
  if (input === "k") return "k";
  if (input === "\u001b[A") return "up";
  if (input === "\u001b[B") return "down";
  return "unknown";
}

function readKey(stdin = process.stdin) {
  const buffer = Buffer.alloc(8);
  const bytes = readSync(stdin.fd, buffer, 0, buffer.length);
  return decodeKey(buffer.toString("utf8", 0, bytes));
}

function runTui(parsed, options = {}) {
  const stdout = options.stdout || process.stdout;
  const stdin = options.stdin || process.stdin;
  const model = createTuiModel(options);

  if (parsed.json) {
    printJson(model, stdout);
    return 0;
  }

  if (!stdin.isTTY || !stdout.isTTY) {
    stdout.write(renderTui(model, { clear: false }));
    return model.report.ok ? 0 : 1;
  }

  let selected = 0;
  const wasRaw = stdin.isRaw;
  stdin.setRawMode(true);
  stdin.resume();
  try {
    while (true) {
      stdout.write(renderTui({ ...model, selected }));
      const key = readKey(stdin);
      if (key === "quit") return 0;
      if (key === "enter") {
        const item = model.items[selected];
        if (item.command === "quit") return 0;
        stdout.write("\x1b[2J\x1b[H");
        return run([item.command, ...item.args], options);
      }
      selected = nextTuiIndex(selected, key, model.items.length);
    }
  } finally {
    stdin.setRawMode(Boolean(wasRaw));
  }
}

function runCloud(rest, options = {}) {
  const paths = resolvePaths(options);
  if (!existsSync(paths.sdkCloudWrapper)) {
    console.error(`Fatal: SDK cloud wrapper not found at ${paths.sdkCloudWrapper}`);
    return 1;
  }
  const result = spawnNode(["--experimental-strip-types", paths.sdkCloudWrapper, ...rest], {
    env: {
      ...process.env,
      ...(options.env || {}),
      DREAM_PLUGIN_ROOT: paths.pluginRoot,
    },
  });
  return exitFromSpawn(result);
}

function run(argv = process.argv.slice(2), options = {}) {
  const parsed = parseArgs(argv);
  const stdout = options.stdout || process.stdout;
  const stderr = options.stderr || process.stderr;
  const packageRoot = options.packageRoot || packageRootFromBin(options.binFile);

  if (!parsed.command) {
    if ((options.stdin || process.stdin).isTTY && stdout.isTTY) {
      return runTui(parsed, { ...options, packageRoot });
    }
    stdout.write(`${usage()}\n`);
    return 0;
  }

  if (parsed.command === "help" || parsed.help) {
    stdout.write(`${usage()}\n`);
    return 0;
  }

  if (parsed.command === "version" || parsed.version) {
    stdout.write(`${readPackageVersion(packageRoot)}\n`);
    return 0;
  }

  if (parsed.command === "doctor") {
    const report = inspect({ ...options, packageRoot });
    if (parsed.json) {
      printJson(report, stdout);
    } else {
      printDoctor(report, stdout);
    }
    return report.ok ? 0 : 1;
  }

  if (parsed.command === "capabilities") {
    const capabilities = buildCapabilities({ ...options, packageRoot });
    if (parsed.json) {
      printJson(capabilities, stdout);
    } else {
      printCapabilities(capabilities, stdout);
    }
    return 0;
  }

  if (parsed.command === "agent") {
    printJson(buildAgentEnvelope({ ...options, packageRoot }), stdout);
    return 0;
  }

  if (parsed.command === "tui") {
    return runTui(parsed, { ...options, packageRoot });
  }

  if (parsed.command === "run") {
    const flow = runDreamFlow(parsed.rest, {
      ...options,
      packageRoot,
      dryRun: parsed.dryRun,
    });
    if (parsed.json) {
      printJson(flow, stdout);
    } else {
      printRunFlow(flow, stdout);
    }
    return flow.ok ? 0 : 1;
  }

  if (parsed.command === "which") {
    const report = inspect({ ...options, packageRoot });
    if (parsed.json) {
      printJson(report.paths, stdout);
    } else {
      stdout.write(`${report.paths.plugin_cli}\n`);
    }
    return report.status.plugin_cli.exists ? 0 : 1;
  }

  if (parsed.command === "cloud") {
    return runCloud(parsed.rest, { ...options, packageRoot });
  }

  if (PASS_THROUGH_COMMANDS.has(parsed.command)) {
    return delegateToPlugin(parsed.command, parsed.rest, {
      ...options,
      packageRoot,
      json: parsed.json,
    });
  }

  stderr.write(`Unknown dream command: ${parsed.command}\n\n`);
  stderr.write(`${usage()}\n`);
  return 2;
}

module.exports = {
  DEFAULT_PLUGIN_ROOT,
  PASS_THROUGH_COMMANDS,
  TUI_ITEMS,
  buildAgentEnvelope,
  buildCapabilities,
  createTuiModel,
  decodeKey,
  delegateToPlugin,
  expandHome,
  inspect,
  nextTuiIndex,
  parseArgs,
  renderTui,
  resolvePaths,
  resolvePluginRoot,
  run,
  runCloud,
  runDreamFlow,
  runTui,
  supportsStripTypes,
  usage,
};
