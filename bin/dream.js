#!/usr/bin/env node

const { run } = require("../lib/dream-cli");

process.exitCode = run(process.argv.slice(2), { binFile: __filename });
