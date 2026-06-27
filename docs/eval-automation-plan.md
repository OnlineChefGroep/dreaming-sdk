# Eval automation & chains — plan

Status quo: weekly eval op Mon 09:00 via GHA, resultaten naar `eval/results/<run_id>/`.
Geen notificaties, geen trend tracking, geen chains.

## Fase 1 — Eval resultaat aggregatie + notificaties

| Nr | Wat | Waarom | Hoe |
|----|-----|--------|-----|
| 1.1 | **Eval-resultaten naar Postgres** | Trends, dashboard, historical queries | `dream-memory remember` na elke eval run — metrics JSON in memory |
| 1.2 | **Slack notificatie** | Team ziet direct of eval faalt | `SlackClient().report_eval_result()` — al geschreven in `cli.py`, alleen triggeren |
| 1.3 | **Regression detection** | Automatisch alarm als faithfulness < 0.75 | GHA step die vorige score vergelijkt met huidige uit `agent_memory` |
| 1.4 | **Eval dashboard tab** | Visualisatie van faithfulness trend | Nieuwe route op memory dashboard: `/api/eval-history` + chart |

## Fase 2 — Eval chains (meerdere stappen)

| Nr | Wat | Waarom | Hoe |
|----|-----|-------|-----|
| 2.1 | **Chain orchestrator** | Meerdere eval passes achter elkaar | Nieuw `dream chain` commando dat `eval` meerdere keren roept met verschillende corpora |
| 2.2 | **Golden → regression → stress** | 3-traps chain | Eerst golden corpus (baseline), dan regression suite, dan stress corpus |
| 2.3 | **Chain rapport** | Samenvatting van alle stappen in 1 markdown | `eval/results/<run_id>/chain-summary.md` met per-step metrics |
| 2.4 | **Conditional gates** | Stop chain als een stap faalt (hard_fail) | `chain.yaml` config: `{step: golden, required: true}` |

## Fase 3 — Systemd automations op fleet

| Nr | Wat | Waarom | Hoe |
|----|-----|-------|-----|
| 3.1 | **`dream-memory sync` timer** | Hourly Linear sync (staat in docs, niet geprovisioneerd) | systemd timer op bc-scan-arm + playbook |
| 3.2 | **`dream-eval` timer** | Weekly eval zonder GitHub (air-gapped) | systemd timer op bc-monitor die `node bin/dream.js run` draait |
| 3.3 | **Healthcheck endpoint** | Monitor of timers draaien | `dream-memory doctor --json` via cron → Slack als offline |
| 3.4 | **Prefect deployment** | Vervang cron/systemd door Prefect voor fleet-orchestratie | `prefect_flow.py` uitbreiden met eval + memory sync flows |

## Fase 4 — Eval kwaliteitsdashboards

| Nr | Wat | Waarom | Hoe |
|----|-----|-------|-----|
| 4.1 | **Eval metrics endpoint** | JSON API voor eval trends | `GET /api/eval/metrics` op memory dashboard |
| 4.2 | **Faithfulness sparkline** | Visuele trend over tijd | HTMX chart op dashboard |
| 4.3 | **Regression alerts** | Slack + Linear issue bij daling | GHA workflow dispatch naar Linear webhook |
| 4.4 | **Acceptance rate tracking** | Hoeveel van de voorstellen worden geaccepteerd | Uit `decisions.jsonl` → memory → dashboard |

## Prioriteit & volgorde

```
Fase 1 (notificaties)
  ├─ 1.2 Slack — laaghangend fruit, code bestaat al
  ├─ 1.4 Dashboard tab — zichtbaarheid
  ├─ 1.1 Postgres sink — foundation voor alles
  └─ 1.3 Regression detection — alerting

Fase 2 (chains)
  ├─ 2.1 Chain orchestrator — core
  ├─ 2.2 3-traps chain — Waarde
  ├─ 2.4 Conditional gates — safety
  └─ 2.3 Chain rapport — output

Fase 3 (fleet)
  ├─ 3.1 Linear sync timer — direct bruikbaar
  ├─ 3.3 Healthcheck — stabiliteit
  ├─ 3.2 Eval timer — air-gapped
  └─ 3.4 Prefect — scale

Fase 4 (dashboards)
  ├─ 4.1 Metrics endpoint — data
  ├─ 4.2 Faithfulness chart — inzicht
  ├─ 4.3 Alerts — reactie
  └─ 4.4 Acceptance rate — kwaliteit
```

## Direct starten (Fase 1, dag 1)

1. **Slack webhook in `.env`** — `SLACK_WEBHOOK_URL` toevoegen aan GHA secrets
2. **GHA post-eval step** — na `weekly-eval.yml` stap: `dream-memory slack-report --metrics-json eval/results/*/metrics.json`
3. **Eval naar memory** — `dream-memory remember` met de 25 canonical keys
