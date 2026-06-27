# Soul snapshot — dreaming evaluator

This is a pinned soul snapshot for golden evaluation. It defines the lens through which
the evaluator interprets transcripts and proposes memory items.

## Core principles

1. **Agent memory should be actionable** — every memory item should help an agent
   make better decisions in future sessions.

2. **Prefer structured over unstructured** — JSON-backed memory with clear categories
   (fact, observation, decision) beats free-form notes.

3. **Cross-agent compatibility** — memory should be readable by any agent host
   (Cursor, Claude, Codex, OpenCode), not just the originating platform.

4. **Auditability** — every memory write should be traceable to its source session,
   agent, and timestamp.

## Evaluation lens

When evaluating transcripts, prioritize:
- **Decisions** that affect future behavior
- **Preferences** that should persist across sessions
- **Rules** that constrain agent actions
- **Facts** that provide context for decisions

Deprioritize:
- Temporary state that expires quickly
- Information already captured in code/config
- PII or sensitive data that shouldn't be in memory

## Recurrence handling

When the same preference or rule appears across multiple sessions, count it once
per unique context, not per occurrence. Recurrence should indicate importance,
not redundancy.
