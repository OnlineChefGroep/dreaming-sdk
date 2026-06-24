"use strict";

const assert = require("node:assert/strict");

const {
  clamp,
  composeColumns,
  createState,
  decodeKey,
  defaultTheme,
  fuzzyFilter,
  fuzzyScore,
  moveSelection,
  renderFrame,
  selectedItem,
  step,
  stripAnsi,
  visibleEntries,
  visibleLength,
  wrapText,
} = require("../lib/dream-tui");

const model = {
  title: "dream terminal motion",
  subtitle: "Human control surface for the dreaming plugin",
  report: { ok: true, paths: { plugin_root: "/tmp/dreaming" } },
  items: [
    { label: "Doctor - inspect plugin and runtime", command: "doctor", args: [], hint: "Check discovery." },
    { label: "Test - run deterministic plugin gates", command: "test", args: [], hint: "Run gates." },
    { label: "Eval dry-run - prepare a run plan", command: "eval", args: ["--dry-run"], hint: "Preview." },
    { label: "Run - test + eval + decisions flow", command: "run", args: [], hint: "Full flow." },
    { label: "Quit", command: "quit", args: [], hint: "Leave." },
  ],
};

// --- pure helpers ---
assert.equal(clamp(5, 0, 3), 3);
assert.equal(clamp(-1, 0, 3), 0);
assert.equal(visibleLength("\x1b[1mabc\x1b[0m"), 3);
assert.equal(stripAnsi("\x1b[38;5;75mx\x1b[0m"), "x");
assert.deepEqual(wrapText("one two three", 7), ["one two", "three"]);

// --- key decoding ---
assert.equal(decodeKey("\u001b[A"), "up");
assert.equal(decodeKey("\u001b[B"), "down");
assert.equal(decodeKey("\r"), "enter");
assert.equal(decodeKey("/"), "palette");
assert.equal(decodeKey("\u0003"), "quit");
assert.equal(decodeKey("\u007f"), "backspace");
assert.equal(decodeKey("a"), "char:a");

// --- fuzzy filtering ---
assert.ok(fuzzyScore("Doctor", "dr") > 0);
assert.equal(fuzzyScore("Doctor", "zzz"), -1);
const filtered = fuzzyFilter(model.items, "eval");
assert.ok(filtered.length >= 1);
assert.match(filtered[0].item.label.toLowerCase(), /eval/);

// --- state + motion ---
let state = createState(model);
assert.equal(state.mode, "menu");
state = moveSelection(state, 1);
assert.equal(state.selected, 1);
state = moveSelection(state, -1);
assert.equal(state.selected, 0);
// wrap-around upward
state = moveSelection(createState(model), -1);
assert.equal(state.selected, model.items.length - 1);

// --- reducer: enter selects ---
const selectResult = step(createState(model), "enter");
assert.equal(selectResult.action.type, "select");
assert.equal(selectResult.action.item.command, "doctor");

// --- reducer: quit exits ---
assert.equal(step(createState(model), "quit").action.type, "exit");

// --- palette mode lifecycle ---
let palette = step(createState(model), "palette").state;
assert.equal(palette.mode, "palette");
palette = step(palette, "char:e").state;
palette = step(palette, "char:v").state;
assert.equal(palette.query, "ev");
assert.match(selectedItem(palette).label.toLowerCase(), /eval/);
palette = step(palette, "backspace").state;
assert.equal(palette.query, "e");
palette = step(palette, "escape").state;
assert.equal(palette.mode, "menu");
assert.equal(palette.query, "");

// --- visible entries reflect palette query ---
const queried = { ...createState(model), mode: "palette", query: "quit" };
assert.equal(visibleEntries(queried).length, 1);

// --- rendering ---
const frame = renderFrame(createState(model), { cols: 90, rows: 24 });
const plain = stripAnsi(frame);
assert.match(plain, /dream terminal motion/);
assert.match(plain, /Doctor - inspect plugin and runtime/);
assert.match(plain, /plugin ready/);
assert.match(plain, /enter run/);
// detail panel shows the selected command invocation
assert.match(plain, /dream doctor/);

// color:false yields no escape codes
const plainFrame = renderFrame(createState(model), { cols: 80, rows: 24 }, { color: false });
assert.equal(/\x1b\[/.test(plainFrame), false);

// composeColumns aligns rows
const composed = composeColumns(["a", "bb"], ["x"], 6, 2, defaultTheme());
assert.equal(composed.length, 2);
assert.match(stripAnsi(composed[0]), /a {7}│ x/);

console.log("dream-tui tests passed");
