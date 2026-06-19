#!/usr/bin/env node

// @onlinechefgroep/dream-cli — Phase 1 placeholder.
//
// This thin CLI intentionally has no external dependencies and no imports so it
// stays CommonJS/ESM-agnostic and always passes `node --check`. In Phase 1 the
// real work is delegated to the dreaming plugin's CLI, which is an external local
// install (this repo is an integration kit, not a fork of the plugin).

console.log("@onlinechefgroep/dream-cli (Phase 1 placeholder)");
console.log("");
console.log("This CLI delegates to the dreaming plugin's CLI at:");
console.log("  ~/.cursor/plugins/local/dreaming/cli/dream.mjs");
console.log("");
console.log("Install the dreaming plugin there, then run, for example:");
console.log("  node ~/.cursor/plugins/local/dreaming/cli/dream.mjs test --json");
console.log("");
console.log("A unified wrapper (schema validation + orchestration) ships in a later Phase 1 release.");

process.exit(0);
