"use strict";

// Antigravity-style interactive terminal engine for the dream CLI.
//
// Design goals:
// - Zero runtime dependencies (pure Node).
// - Pure, testable rendering and state-reduction functions.
// - Smooth keyboard motion, a command palette with fuzzy filtering, a header
//   status bar, a two-pane layout (menu + detail), a spinner, and a footer.
//
// The interactive runner uses the alternate screen buffer so the user's
// scrollback is preserved, mirroring polished agent CLIs.

const ESC = "\x1b";
const ANSI_RE = /\x1b\[[0-9;]*m/g;

const ALT_SCREEN_ENTER = `${ESC}[?1049h`;
const ALT_SCREEN_LEAVE = `${ESC}[?1049l`;
const HIDE_CURSOR = `${ESC}[?25l`;
const SHOW_CURSOR = `${ESC}[?25h`;
const CLEAR = `${ESC}[2J${ESC}[H`;

const SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];

function sgr(...codes) {
  return `${ESC}[${codes.join(";")}m`;
}

function fg(code) {
  return `${ESC}[38;5;${code}m`;
}

function bg(code) {
  return `${ESC}[48;5;${code}m`;
}

const RESET = `${ESC}[0m`;
const BOLD = `${ESC}[1m`;
const DIM = `${ESC}[2m`;

function defaultTheme() {
  return {
    accent: 75, // bright blue
    accentAlt: 213, // magenta/pink
    ok: 78, // green
    warn: 214, // amber
    danger: 203, // red
    text: 252,
    dim: 244,
    barBg: 24,
    barText: 231,
    panelBorder: 60,
    selectionBg: 24,
    selectionText: 231,
  };
}

function stripAnsi(text) {
  return String(text).replace(ANSI_RE, "");
}

function visibleLength(text) {
  return stripAnsi(text).length;
}

function truncate(text, width) {
  if (visibleLength(text) <= width) {
    return text;
  }
  // Slice on the plain string then re-style is hard with embedded codes; for
  // robustness we only truncate plain text (callers pass plain content here).
  const plain = stripAnsi(text);
  if (width <= 1) {
    return plain.slice(0, Math.max(0, width));
  }
  return `${plain.slice(0, width - 1)}…`;
}

function padEnd(text, width) {
  const len = visibleLength(text);
  if (len >= width) {
    return text;
  }
  return text + " ".repeat(width - len);
}

function fuzzyScore(label, query) {
  if (!query) return 0;
  const haystack = label.toLowerCase();
  const needle = query.toLowerCase();
  let score = 0;
  let from = 0;
  for (const ch of needle) {
    const idx = haystack.indexOf(ch, from);
    if (idx === -1) {
      return -1;
    }
    // Reward adjacency (consecutive matches score higher).
    score += idx === from ? 3 : 1;
    from = idx + 1;
  }
  return score;
}

function fuzzyFilter(items, query) {
  if (!query) {
    return items.map((item, index) => ({ item, index }));
  }
  return items
    .map((item, index) => ({ item, index, score: fuzzyScore(item.label, query) }))
    .filter((entry) => entry.score >= 0)
    .sort((a, b) => b.score - a.score);
}

function clamp(value, min, max) {
  if (value < min) return min;
  if (value > max) return max;
  return value;
}

function createState(model, overrides = {}) {
  return {
    title: model.title || "dream terminal motion",
    subtitle: model.subtitle || "Human control surface for the dreaming plugin",
    items: model.items || [],
    report: model.report || { ok: false, paths: { plugin_root: "(unknown)" } },
    theme: model.theme || defaultTheme(),
    selected: overrides.selected || 0,
    mode: overrides.mode || "menu", // "menu" | "palette"
    query: overrides.query || "",
    spinnerFrame: overrides.spinnerFrame || 0,
    status: overrides.status || "",
  };
}

function visibleEntries(state) {
  return fuzzyFilter(state.items, state.mode === "palette" ? state.query : "");
}

function moveSelection(state, delta) {
  const entries = visibleEntries(state);
  if (entries.length === 0) {
    return { ...state, selected: 0 };
  }
  const next = (state.selected + delta + entries.length) % entries.length;
  return { ...state, selected: next };
}

function selectedItem(state) {
  const entries = visibleEntries(state);
  if (entries.length === 0) {
    return null;
  }
  const idx = clamp(state.selected, 0, entries.length - 1);
  return entries[idx].item;
}

// Reduce a decoded key into a new state and an optional action.
function step(state, key) {
  if (key === "quit") {
    return { state, action: { type: "exit" } };
  }

  if (state.mode === "menu") {
    if (key === "up") return { state: moveSelection(state, -1), action: null };
    if (key === "down") return { state: moveSelection(state, 1), action: null };
    if (key === "palette") {
      return { state: { ...state, mode: "palette", query: "", selected: 0 }, action: null };
    }
    if (key === "enter") {
      const item = selectedItem(state);
      return { state, action: item ? { type: "select", item } : null };
    }
    return { state, action: null };
  }

  // palette mode
  if (key === "escape") {
    return { state: { ...state, mode: "menu", query: "", selected: 0 }, action: null };
  }
  if (key === "up") return { state: moveSelection(state, -1), action: null };
  if (key === "down") return { state: moveSelection(state, 1), action: null };
  if (key === "backspace") {
    return { state: { ...state, query: state.query.slice(0, -1), selected: 0 }, action: null };
  }
  if (key === "enter") {
    const item = selectedItem(state);
    return { state, action: item ? { type: "select", item } : null };
  }
  if (typeof key === "string" && key.startsWith("char:")) {
    return { state: { ...state, query: state.query + key.slice(5), selected: 0 }, action: null };
  }
  return { state, action: null };
}

function statusBadge(report, theme) {
  if (report.ok) {
    return `${fg(theme.ok)}● plugin ready${RESET}`;
  }
  return `${fg(theme.warn)}● plugin missing${RESET}`;
}

function renderHeader(state, width) {
  const { theme } = state;
  const left = ` ${BOLD}◆ DREAM${RESET}${bg(theme.barBg)}${fg(theme.barText)}  ${state.title} `;
  const node = `node ${process.versions.node}`;
  const right = ` ${statusBadge(state.report, theme)}${bg(theme.barBg)}${fg(theme.barText)}  ${node} `;
  const used = visibleLength(left) + visibleLength(right);
  const gap = Math.max(1, width - used);
  return `${bg(theme.barBg)}${fg(theme.barText)}${left}${" ".repeat(gap)}${right}${RESET}`;
}

function menuLines(state, width) {
  const { theme } = state;
  const entries = visibleEntries(state);
  const lines = [];
  if (state.mode === "palette") {
    lines.push(`${fg(theme.accentAlt)}› ${RESET}${state.query}${fg(theme.dim)}▏${RESET}`);
    lines.push("");
  }
  if (entries.length === 0) {
    lines.push(`${fg(theme.dim)}no matches${RESET}`);
    return lines;
  }
  entries.forEach((entry, index) => {
    const active = index === clamp(state.selected, 0, entries.length - 1);
    const label = truncate(entry.item.label, width - 4);
    if (active) {
      const filled = padEnd(`  ${label}`, width);
      lines.push(`${bg(theme.selectionBg)}${fg(theme.selectionText)}${BOLD}▌ ${label}${RESET}${bg(theme.selectionBg)}${" ".repeat(Math.max(0, width - visibleLength("▌ " + label)))}${RESET}`);
    } else {
      lines.push(`${fg(theme.text)}  ${label}${RESET}`);
    }
  });
  return lines;
}

function detailLines(state, width) {
  const { theme } = state;
  const item = selectedItem(state);
  const lines = [];
  if (!item) {
    lines.push(`${fg(theme.dim)}Select a command to see details.${RESET}`);
    return lines;
  }
  const invocation = ["dream", item.command, ...(item.args || [])].join(" ");
  lines.push(`${BOLD}${fg(theme.accent)}${truncate(item.label, width)}${RESET}`);
  lines.push("");
  lines.push(`${fg(theme.dim)}command${RESET}`);
  lines.push(`${fg(theme.text)}${truncate(invocation, width)}${RESET}`);
  lines.push("");
  if (item.hint) {
    lines.push(`${fg(theme.dim)}what it does${RESET}`);
    for (const wrapped of wrapText(item.hint, width)) {
      lines.push(`${fg(theme.text)}${wrapped}${RESET}`);
    }
    lines.push("");
  }
  lines.push(`${fg(theme.dim)}plugin root${RESET}`);
  lines.push(`${fg(theme.text)}${truncate(state.report.paths.plugin_root, width)}${RESET}`);
  return lines;
}

function wrapText(text, width) {
  const words = String(text).split(/\s+/);
  const lines = [];
  let current = "";
  for (const word of words) {
    if (!current) {
      current = word;
    } else if (visibleLength(`${current} ${word}`) <= width) {
      current += ` ${word}`;
    } else {
      lines.push(current);
      current = word;
    }
  }
  if (current) lines.push(current);
  return lines;
}

function composeColumns(leftLines, rightLines, leftWidth, gap, theme) {
  const rows = Math.max(leftLines.length, rightLines.length);
  const out = [];
  const sep = `${fg(theme.panelBorder)}│${RESET}`;
  for (let i = 0; i < rows; i += 1) {
    const left = padEnd(leftLines[i] || "", leftWidth);
    const right = rightLines[i] || "";
    out.push(`${left}${" ".repeat(gap)}${sep} ${right}`);
  }
  return out;
}

function renderFooter(state, width) {
  const { theme } = state;
  const keys =
    state.mode === "palette"
      ? "type to filter · ↑/↓ move · enter run · esc back · ^C quit"
      : "↑/↓ or j/k move · enter run · / palette · q quit";
  return `${bg(theme.barBg)}${fg(theme.barText)} ${padEnd(keys, Math.max(0, width - 2))} ${RESET}`;
}

function renderFrame(state, size = {}, options = {}) {
  const cols = size.cols || 80;
  const rows = size.rows || 24;
  const color = options.color !== false;

  const leftWidth = Math.max(24, Math.floor(cols * 0.42));
  const gap = 2;
  const rightWidth = Math.max(20, cols - leftWidth - gap - 2);

  const header = renderHeader(state, cols);
  const footer = renderFooter(state, cols);

  const bodyHeight = Math.max(3, rows - 4);
  const left = menuLines(state, leftWidth);
  const right = detailLines(state, rightWidth);
  while (left.length < bodyHeight) left.push("");
  while (right.length < bodyHeight) right.push("");
  left.length = bodyHeight;
  right.length = bodyHeight;

  const body = composeColumns(left, right, leftWidth, gap, state.theme);

  const subtitle = `${fg(state.theme.dim)} ${truncate(state.subtitle, cols - 2)}${RESET}`;

  const frame = [header, subtitle, ...body, footer].join("\n");
  const prefix = options.clear === false || color === false ? "" : CLEAR;
  const output = `${prefix}${frame}\n`;
  return color ? output : stripAnsi(output);
}

function decodeKey(input) {
  if (input === "\u0003") return "quit"; // Ctrl-C
  if (input === "\u001b[A") return "up";
  if (input === "\u001b[B") return "down";
  if (input === "\r" || input === "\n") return "enter";
  if (input === "\u001b") return "escape";
  if (input === "\u007f" || input === "\b") return "backspace";
  if (input === "q") return "quit";
  if (input === "k") return "up";
  if (input === "j") return "down";
  if (input === "/") return "palette";
  if (input.length === 1 && input >= " " && input <= "~") return `char:${input}`;
  return "unknown";
}

function readKey(stdin) {
  const { readSync } = require("node:fs");
  const buffer = Buffer.alloc(8);
  const bytes = readSync(stdin.fd, buffer, 0, buffer.length);
  return decodeKey(buffer.toString("utf8", 0, bytes));
}

function terminalSize(stdout) {
  return {
    cols: stdout.columns || 80,
    rows: stdout.rows || 24,
  };
}

// Interactive runner. Returns { action: "exit" } or { action: "select", item }.
function runInteractive(model, io = {}) {
  const stdout = io.stdout || process.stdout;
  const stdin = io.stdin || process.stdin;
  let state = createState(model);

  const wasRaw = Boolean(stdin.isRaw);
  stdout.write(ALT_SCREEN_ENTER + HIDE_CURSOR);
  if (typeof stdin.setRawMode === "function") {
    stdin.setRawMode(true);
  }
  stdin.resume();

  try {
    // eslint-disable-next-line no-constant-condition
    while (true) {
      stdout.write(renderFrame(state, terminalSize(stdout)));
      const key = readKey(stdin);
      const result = step(state, key);
      state = result.state;
      if (result.action && result.action.type === "exit") {
        return { action: "exit" };
      }
      if (result.action && result.action.type === "select") {
        return { action: "select", item: result.action.item };
      }
    }
  } finally {
    if (typeof stdin.setRawMode === "function") {
      stdin.setRawMode(wasRaw);
    }
    stdin.pause();
    stdout.write(SHOW_CURSOR + ALT_SCREEN_LEAVE);
  }
}

module.exports = {
  ALT_SCREEN_ENTER,
  ALT_SCREEN_LEAVE,
  SPINNER_FRAMES,
  clamp,
  composeColumns,
  createState,
  decodeKey,
  defaultTheme,
  fuzzyFilter,
  fuzzyScore,
  moveSelection,
  padEnd,
  renderFrame,
  runInteractive,
  selectedItem,
  step,
  stripAnsi,
  terminalSize,
  truncate,
  visibleEntries,
  visibleLength,
  wrapText,
};
