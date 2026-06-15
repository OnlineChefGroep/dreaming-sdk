# Runbook: expose the metrics dashboard on a Cloudflare domain

The agent-memory metrics dashboard runs on `bc-monitor` (`localhost:8787`,
also reachable over Tailscale). It is published to the internet through a
**Cloudflare Tunnel** (no inbound ports, no public IP needed).

## Live

- Direct: <https://memory.chefgroep.online>
- Via online control-plane API: <https://api.chefgroep.online/dashboard>
- Origin: `cloudflared` connector on `bc-monitor` → `http://localhost:8787`
- Tunnel: `agent-memory` (cloudflare-managed config) in account `3658edc5…`
- Connector service: `systemctl status cloudflared` on `bc-monitor`

### Hooked into the .online API

`api.chefgroep.online` is the `utrecht-dataos-api` Worker (custom domain). It now
reverse-proxies `/dashboard`, `/api/metrics` and `/healthz` to the dashboard
origin and advertises `dashboard` in its root JSON. Source lives at
`python/deploy/cloudflare/utrecht-dataos-api.worker.js`. Redeploy with:

```bash
T=$CLOUDFLARE_API_TOKEN A=$CLOUDFLARE_ACCOUNT_ID
echo '{"body_part":"script","compatibility_date":"2025-01-01","keep_bindings":["secret_text","plain_text"]}' > /tmp/meta.json
curl -X PUT "https://api.cloudflare.com/client/v4/accounts/$A/workers/scripts/utrecht-dataos-api" \
  -H "Authorization: Bearer $T" \
  -F "metadata=@/tmp/meta.json;type=application/json" \
  -F "script=@python/deploy/cloudflare/utrecht-dataos-api.worker.js;type=application/javascript"
```

`keep_bindings` preserves the `UPSTASH_REDIS_REST_URL` / `UPSTASH_REDIS_REST_TOKEN`
bindings so they survive the redeploy.

## How it was wired

1. `cloudflared` installed on `bc-monitor` (`cloudflared-linux-<arch>.deb`).
2. `python/deploy/fleet/cloudflare_tunnel.py` created the tunnel, set ingress
   (`memory.<zone>` → `http://localhost:8787`), and added the proxied DNS CNAME.
3. The connector was installed with the tunnel token:
   `sudo cloudflared service install <TUNNEL_TOKEN>`.

### Re-run / move to another hostname

```bash
# token auth (Account>Cloudflare Tunnel:Edit + Zone>DNS:Edit + Zone:Read):
export CLOUDFLARE_API_TOKEN=...   CLOUDFLARE_ACCOUNT_ID=...
# or legacy global-key auth (full account):
export CLOUDFLARE_EMAIL=...        CLOUDFLARE_GLOBAL_API_KEY=...  CLOUDFLARE_ACCOUNT_ID=...

export TUNNEL_HOSTNAME=memory.example.com
export TUNNEL_NAME=agent-memory
export LOCAL_SERVICE=http://localhost:8787
python deploy/fleet/cloudflare_tunnel.py        # prints url; TUNNEL_TOKEN to stderr
# then on the host that runs the dashboard:
sudo cloudflared service install <TUNNEL_TOKEN>
```

## Notes / hardening

- The account token (`CLOUDFLARE_API_TOKEN`, account `3658edc5…`) with
  `Cloudflare Tunnel:Edit` + `DNS:Edit` + `Zone:Read`, plus the R2 keys
  (`R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` / `R2_ENDPOINT`), live in
  `~/.openclaude/.env` and are synced to the fleet by `sync-env.sh`.
- The dashboard shows aggregate memory counts only (no secrets), but to lock it
  behind login add a **Cloudflare Access** self-hosted app policy on the
  hostname (Zero Trust → Access → Applications).
- The original temporary deployment on `memory.blackclaw.xyz` (a different
  account, reached via the global key) has been torn down: tunnel + DNS removed
  and that zone's catch-all redirect to `chefgroep.nl` restored to `true`.
