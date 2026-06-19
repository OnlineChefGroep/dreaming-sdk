"use strict";

const { existsSync, statSync } = require("node:fs");
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
  const help = args.includes("--help") || args.includes("-h");
  const version = args.includes("--version") || args.includes("-v");
  const command = args.find((arg) => !arg.startsWith("-")) || (version ? "version" : help ? "help" : "");
  const rest = command ? args.slice(args.indexOf(command) + 1) : [];
  return { command, rest, json, help, version };
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
    "  cloud [...args]      Run sdk/run-dream-cloud.ts through the SDK wrapper",
    "",
    "Plugin pass-through commands:",
    "  test | eval | decisions | status | scope | index",
    "",
    "Environment:",
    `  DREAM_PLUGIN_ROOT   Defaults to ${DEFAULT_PLUGIN_ROOT}`,
  ].join("\n");
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

function spawnNode(args, options = {}) {
  return spawnSync(process.execPath, args, {
    stdio: options.stdio || "inherit",
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

  const result = spawnNode([paths.pluginCli, command, ...rest], {
    env: {
      ...process.env,
      ...(options.env || {}),
      DREAM_PLUGIN_ROOT: paths.pluginRoot,
    },
  });
  return exitFromSpawn(result);
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

  if (!parsed.command || parsed.command === "help" || parsed.help) {
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
    return delegateToPlugin(parsed.command, parsed.rest, { ...options, packageRoot });
  }

  stderr.write(`Unknown dream command: ${parsed.command}\n\n`);
  stderr.write(`${usage()}\n`);
  return 2;
}

module.exports = {
  DEFAULT_PLUGIN_ROOT,
  PASS_THROUGH_COMMANDS,
  delegateToPlugin,
  expandHome,
  inspect,
  parseArgs,
  resolvePaths,
  resolvePluginRoot,
  run,
  runCloud,
  supportsStripTypes,
  usage,
};
