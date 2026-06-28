# Multi-agent distribution — dream-eval pipeline

How **Claude Code**, **Codex/OpenAI**, **OpenCode**, **Grok (Factory)**, and **Cursor** consume the same eval loop without forking plugin logic.

**Runtime SSOT:** `~/.cursor/plugins/local/dreaming/`  
**Portable skills:** [skills-bundle/](../skills-bundle/)  
**Integration kit:** [OnlineChefGroep/cursor-dreaming-sdk](https://github.com/OnlineChefGroep/cursor-dreaming-sdk)

---

## Design principles

1. **CLI is platform-agnostic.** All agents call `node cli/dream.mjs test|eval|status|scope|decisions|index` against the plugin root.
2. **Skills are portable markdown.** Orchestration lives in `dream-eval-loop`; platform folders differ only in frontmatter and install path.
3. **Readonly vs write boundaries are fixed.** Eval = readonly evaluator + readonly judge; live `/dream` = write curator. Never pass `soul.md` to judge or curator.
4. **Eval never mutates live state.** Writes limited to `eval/results/<run_id>/`.
5. **DRY via shared bundle.** `skills-bundle/shared/` holds chain reference, CLI contract, metrics schema, and orchestration body.

---

## Platform matrix

| Platform | Skill install path | `/dream` equivalent | `/dream-eval` equivalent |
|----------|-------------------|---------------------|--------------------------|
| **Cursor** | `~/.cursor/skills/dream-eval-loop/` | `/dream` → `dreaming` skill | `/dream-eval` → `dream-eval-loop` |
| **Claude** | `.claude/skills/dream-eval-loop/` | "Run the dreaming skill" | "Apply dream-eval-loop skill" |
| **Codex** | `.agents/skills/dream-eval-loop/` | Plugin `dreaming` skill | "Apply dream-eval-loop skill" |
| **OpenCode** | `.opencode/skills/dream-eval-loop/` | Skill trigger in chat | "Apply dream-eval-loop skill" |
| **Grok/Factory** | `.factory/skills/dream-eval-loop/` | Droid + `dreaming` skill | Droid or skill: dream-eval-loop |

---

## Install quick reference

| Platform | Command |
|----------|---------|
| **All** | `.\skills-bundle\install-dream-skills.ps1 -Platform all -Target C:\path\to\repo` |
| **Claude** | `-Platform claude` → `.claude/skills/` |
| **Codex** | `-Platform codex` → `.agents/skills/`; add row to `00-skills/SKILL.md` |
| **OpenCode** | `-Platform opencode` → `.opencode/skills/` |
| **Grok** | `-Platform grok` → `.factory/skills/`; optional droid in `.factory/droids/` |
| **Cursor** | `-Platform cursor -Global` → sync `~/.cursor/skills/` |

Unix: `./skills-bundle/install-dream-skills.sh --platform codex --target ~/my-repo`

Full steps: [skills-bundle/README.md](../skills-bundle/README.md).

---

## Per-platform consumption

### Cursor (reference)

| Artifact | Path |
|----------|------|
| Eval orchestrator | `~/.cursor/skills/dream-eval-loop/SKILL.md` |
| Live dream | Plugin `skills/dreaming/SKILL.md` |
| SDK driver | Plugin `sdk/run-dream-cloud.ts` |
| Automations | `~/.cursor/skills/dream-eval-loop/automations.json` |
| Subagents | Task: `dream-evaluator`, `dream-judge`, `dream-curator` |

**Trigger:** `/dream-eval` or "Apply the dream-eval-loop skill"  
**Cron:** Cursor Automation Monday 09:00 (`dream_eval_weekly`)

See [sdk-integration.md](./sdk-integration.md) § Cursor SDK and Automations.

---

### Claude (Claude Code / API)

No Cursor Automation or `@cursor/sdk`. Integration is skill markdown + shell CLI + optional MCP (Phase 3).

| Scope | Path |
|-------|------|
| Project | `<repo>/.claude/skills/dream-eval-loop/SKILL.md` |
| User global | `~/.claude/skills/dream-eval-loop/SKILL.md` |
| Context | `CLAUDE.md` — one-line pointer to eval skill |

**Trigger:** "Apply the dream-eval-loop skill to run one golden corpus evaluation pass."

**Subagent mapping:**

- `dream-evaluator` → readonly analysis over golden corpus
- `dream-judge` → readonly scoring (**never** pass `soul.md`)
- `dream-curator` → **live loop only**; user must approve writes

**Do not port:** Cursor-only frontmatter (`disable-model-invocation`, `user: disabled`).

---

### Codex (OpenAI)

Reads `.agents/skills/` and optional `agents/openai.yaml` per skill.

| Scope | Path |
|-------|------|
| Project | `<repo>/.agents/skills/dream-eval-loop/SKILL.md` |
| Index | `<repo>/.agents/skills/00-skills/SKILL.md` |
| Metadata | `<repo>/.agents/skills/dream-eval-loop/agents/openai.yaml` |

**Trigger:** "Apply the dream-eval-loop skill."

**Unattended:** cron on sofie/chefgroep + agent prompt, or GitHub Actions (Phase 2).

**`openai.yaml`:**

```yaml
interface:
  display_name: "Dream Eval Loop"
  short_description: "Unattended dream evaluation pipeline (golden corpus, faithfulness gate)"
  default_prompt: "Use $dream-eval-loop to run one golden corpus eval pass and write metrics.json + summary.md."
policy:
  allow_implicit_invocation: false
```

---

### OpenCode

Project skills under `.opencode/skills/<skill-name>/SKILL.md`.

**Trigger:** "Apply the dream-eval-loop skill."

Schedule via host cron or CI that runs `dream test` then triggers an OpenCode agent for evaluator/judge steps.

---

### Grok / Factory

| Artifact | Path |
|----------|------|
| Skill | `<repo>/.factory/skills/dream-eval-loop/SKILL.md` |
| Eval droid (optional) | `<repo>/.factory/droids/dream-eval-loop.md` |
| Subagent specs | Plugin or `.factory/droids/dream-evaluator.md`, `dream-judge.md` |

Factory droids should state readonly boundaries, reference `skills-bundle/shared/chain-reference.md`, list CLI commands verbatim, and forbid `soul.md` for judge/curator.

**Do not port:** Cursor hook auto-run behavior; live `reconcileDreamIndex({ write: true })` during eval prep.

---

## CLI entry (all platforms)

**Plugin root:** `~/.cursor/plugins/local/dreaming/` (override: `DREAM_PLUGIN_ROOT`)

```text
node cli/dream.mjs <command> [--json]
```

| Subcommand | Eval loop | Mutates live state? |
|------------|-----------|---------------------|
| `test` | Step 1 | No |
| `eval` | Step 0 | No (creates `eval/results/<run_id>/` only) |
| `decisions` | Step 3 | No |
| `status` | Nightly dry-run gate | Yes — **not golden eval** |
| `scope` | Nightly dry-run | Yes — **not golden eval** |
| `index` | Diagnostics | Yes — **not golden eval** |

---

## What must NOT be ported (any platform)

| Item | Reason |
|------|--------|
| `soul.md` → `dream-judge` | Judge spec forbids; breaks faithfulness methodology |
| `soul.md` → `dream-curator` | Curator consumes approved action blocks only |
| Live index mutation in eval | Eval uses isolated workspace |
| `~/.cursor/dreaming/` writes during eval | Contaminates production state |
| `AGENTS.md` writes during eval | Eval is measurement-only |
| Cursor-only frontmatter | Breaks non-Cursor hosts |
| Full plugin fork | SSOT stays in plugin install |

---

## Distribution phases

| Phase | Deliverable | Status |
|-------|-------------|--------|
| **0** | CLI + schemas; `skills-bundle/shared/` | Done |
| **1** | Skill bundle in `dreaming-sdk` | Done (this publish) |
| **2** | Install scripts (`install-dream-skills.ps1` / `.sh`) | Done |
| **3** | MCP wrapper (`dream_test`, `dream_eval`, `dream_decisions`) | Planned |

---

## References

| Artifact | Path |
|----------|------|
| SDK integration | [sdk-integration.md](./sdk-integration.md) |
| Skill bundle | [skills-bundle/](../skills-bundle/) |
| Utrecht Codex index pattern | `.agents/skills/00-skills/SKILL.md` |
| Target repo | https://github.com/OnlineChefGroep/cursor-dreaming-sdk |
