# Agent Instructions

## Architectural Boundaries

- **dream-judge** and **dream-curator** subagents must NEVER read `soul.md`.
- Only **dream-evaluator** uses the soul to interpret signal.
- Note: `soul.md` resides in the dreaming plugin install directory or the target repo's `.cursor/dreaming/` directory.

## Core Directives

- Maintain the distinction between live dreaming state (`~/.cursor/dreaming/`) and evaluation results (`eval/results/`).
- `eval/results/` are generated artifacts and should not be committed to this SDK repo unless they are canonical baselines.
- Follow the CLI contract specified in `skills-bundle/shared/cli-contract.md`.
