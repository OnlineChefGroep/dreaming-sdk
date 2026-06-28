# Runbook — OCI Free Tier Postgres (SSOT) bootstrap

The agent memory SSOT runs as Postgres on an **Always-Free Ampere A1** instance
(`bc-scan-arm`, 100.68.121.19) reachable over Tailscale. This is the "OCI free
tier DB" — no paid managed service required.

> Status: **live**. `dream-memory doctor` reports `{"postgres": "ok"}` and the
> `agent_memory` schema is applied. This runbook documents how to reproduce /
> rebuild it.

## 1. Why A1 Postgres (not Autonomous DB)

| Option | Free? | Fit |
|--------|-------|-----|
| **Postgres on A1.Flex** | Yes (Always Free, 4 OCPU / 24 GB ARM) | ✅ Postgres SSOT, JSONB, pgvector-ready |
| OCI Database with PostgreSQL | No (paid) | ✗ |
| Autonomous Database | 2 always-free | Oracle SQL, not Postgres-compatible |

We keep Postgres as the single source of truth, so A1 Postgres wins.

## 2. Provision (if rebuilding)

```bash
# Reuse existing A1 instance from fleet-instances.json, or launch one:
oci compute instance launch \
  --availability-domain <AD> \
  --compartment-id "$OCI_COMPARTMENT_ID" \
  --shape VM.Standard.A1.Flex \
  --shape-config '{"ocpus":2,"memoryInGBs":12}' \
  --display-name agent-memory-pg \
  --image-id <UBUNTU_ARM_IMAGE_OCID> \
  --subnet-id <SUBNET_OCID> --assign-public-ip false
```

Join it to Tailscale so the control node and other fleet hosts can reach it
privately (no public Postgres port).

## 3. Run Postgres (Docker)

```bash
ssh bc-scan-arm
cd ~/dreaming-memory/deploy/oci
# docker-compose.yml binds 5432; restrict to the Tailscale interface in prod
docker compose up -d
```

For a hardened setup, bind Postgres to the Tailscale IP only and create a
least-privilege role:

```sql
CREATE ROLE agentmem LOGIN PASSWORD '<generated>';
CREATE DATABASE agent_memory OWNER agentmem;
```

## 4. Apply schema

```bash
export AGENT_MEMORY_DATABASE_URL='postgresql://agentmem:<pw>@100.68.121.19:5432/agent_memory'
uv run dream-memory init       # creates agent_memory table + indexes + trigger
uv run dream-memory doctor     # expect {"postgres": "ok"}
```

## 5. Security notes

- Postgres listens on the **Tailscale mesh only** — never expose 5432 publicly.
- Rotate the `agentmem` password via `ALTER ROLE agentmem PASSWORD '...'` and
  update `~/.config/agent-memory/.env` on every host.
- Backups: `pg_dump` to Cloudflare R2 (see `CloudflareR2`), or OCI block-volume
  snapshots.

## 6. Future (from CHEF-308)

- Add `pgvector` for in-DB embeddings as an alternative to LanceDB.
- Extend schema with `sources`, `documents`, `pipeline_runs`, `eval_runs`,
  `tenants` for the unified metadata layer (keep `agent_memory` as the agent
  insight table).
