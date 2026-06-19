# Dream skill bundle — multi-agent install

Portable skill scaffold for the dream-eval / dreaming pipeline across **Cursor**, **Claude**, **Codex**, **OpenCode**, and **Grok (Factory)**.

**Skills in this bundle:**

- `dream-eval-loop` — unattended golden-corpus eval orchestrator.
- `dream-tui` — interactive terminal control surface (human TUI + agent JSON
  protocol) with the `dream-navigator` special agent. UX contract:
  [shared/tui-ux.md](./shared/tui-ux.md).

The installers copy every skill a platform ships; `dream-tui` is available for
Cursor and Codex.

**Prerequisite:** Dreaming plugin at `~/.cursor/plugins/local/dreaming/` (CLI, golden corpus, schemas). This bundle is orchestration markdown only.

**SSOT docs:** [../README.md](../README.md) · [../multi-agent.md](../multi-agent.md) · [../sdk-integration.md](../sdk-integration.md)

---

## Bundle layout

```text
skills-bundle/
├── README.md                          ← this file
├── install-dream-skills.ps1
├── install-dream-skills.sh
├── cursor/skills/dream-eval-loop/     ← reference copy (live: ~/.cursor/skills/)
├── claude/skills/dream-eval-loop/
├── codex/skills/dream-eval-loop/
├── opencode/skills/dream-eval-loop/
├── grok/skills/dream-eval-loop/
└── shared/
    ├── orchestration-body.md          ← 6-step loop (DRY)
    ├── chain-reference.md
    ├── cli-contract.md
    └── metrics-schema.md
```

Platform `SKILL.md` files **include by reference** — do not fork the loop body.

---

## Install (recommended)

```powershell
# Windows — from repo root or this bundle directory
.\docs\ops\dreaming\skills-bundle\install-dream-skills.ps1 -Platform codex -Target C:\path\to\repo
.\docs\ops\dreaming\skills-bundle\install-dream-skills.ps1 -Platform all -Global
```

```bash
# Unix
./docs/ops/dreaming/skills-bundle/install-dream-skills.sh --platform codex --target ~/my-repo
```

Flags: `cursor | claude | codex | opencode | grok | all`

---

## Install per platform (manual)

### Cursor

Already installed at `~/.cursor/skills/dream-eval-loop/`. To sync from bundle:

```powershell
Copy-Item -Recurse docs\ops\dreaming\skills-bundle\cursor\skills\dream-eval-loop `
  $env:USERPROFILE\.cursor\skills\dream-eval-loop
```

Automations: copy `automations.json` from live skill folder (Cursor-only).

**Trigger:** `/dream-eval` or "Apply the dream-eval-loop skill"

---

### Claude (Claude Code)

```powershell
New-Item -ItemType Directory -Force -Path .claude\skills
Copy-Item -Recurse docs\ops\dreaming\skills-bundle\claude\skills\dream-eval-loop .claude\skills\
```

Add to `CLAUDE.md`:

```markdown
## Dream eval
Apply `dream-eval-loop` skill for golden corpus eval. Plugin CLI: `node ~/.cursor/plugins/local/dreaming/cli/dream.mjs`.
```

**Trigger:** "Apply the dream-eval-loop skill to run one golden corpus evaluation pass."

---

### Codex (OpenAI)

```powershell
Copy-Item -Recurse docs\ops\dreaming\skills-bundle\codex\skills\dream-eval-loop .agents\skills\
```

Add row to `.agents/skills/00-skills/SKILL.md`:

```markdown
| `dream-eval-loop` | active | dream eval, golden corpus, faithfulness gate | Unattended dream eval orchestrator (multi-agent). |
```

**Trigger:** "Apply the dream-eval-loop skill."

---

### OpenCode

```powershell
New-Item -ItemType Directory -Force -Path .opencode\skills
Copy-Item -Recurse docs\ops\dreaming\skills-bundle\opencode\skills\dream-eval-loop .opencode\skills\
```

Symlink alternative (Unix):

```bash
ln -sf ../../docs/ops/dreaming/skills-bundle/opencode/skills/dream-eval-loop .opencode/skills/dream-eval-loop
```

---

### Grok / Factory

```powershell
New-Item -ItemType Directory -Force -Path .factory\skills
Copy-Item -Recurse docs\ops\dreaming\skills-bundle\grok\skills\dream-eval-loop .factory\skills\
```

**Trigger:** Delegate to dream-eval-loop droid or "Apply dream-eval-loop skill."

---

## Shared content (DRY)

| File | Purpose |
|------|---------|
| `shared/orchestration-body.md` | 6-step eval loop |
| `shared/chain-reference.md` | Handoff tables |
| `shared/cli-contract.md` | `dream.mjs` JSON shapes |
| `shared/metrics-schema.md` | 25-key metrics.json |

Published copy: [OnlineChefGroep/cursor-dreaming-sdk](https://github.com/OnlineChefGroep/cursor-dreaming-sdk) → `skills-bundle/`.

---

## Verify install

```powershell
cd $env:USERPROFILE\.cursor\plugins\local\dreaming
node cli/dream.mjs test --json
node cli/dream.mjs eval --dry-run --json
```

Then run one eval pass via your platform's skill trigger.

---

## What not to install

- Live `~/.cursor/dreaming/` state
- Cursor-only `automations.json` on non-Cursor platforms (use cron/Actions instead)
