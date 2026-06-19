#!/usr/bin/env node

const { run } = require("../lib/dream-cli");

process.exit(run(process.argv.slice(2), { binFile: __filename }));
