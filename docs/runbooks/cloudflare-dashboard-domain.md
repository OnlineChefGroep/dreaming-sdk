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
- **Cloudflare Access is configured** — `memory.chefgroep.online` requires
  authentication (see below for policy details).
- The dashboard shows aggregate memory counts only (no secrets), but it is now
  locked behind Cloudflare Access Zero Trust.
- The original temporary deployment on `memory.blackclaw.xyz` (a different
  account, reached via the global key) has been torn down: tunnel + DNS removed
  and that zone's catch-all redirect to `chefgroep.nl` restored to `true`.

---

## Cloudflare Access Configuration (auth enabled)

### Application: `Agent Memory Dashboard`

- **Hostname**: `memory.chefgroep.online`
- **Type**: Self-hosted application (tunnel: `agent-memory`)
- **Access policy**: Anyone with chefgroep.nl email or Tailscale device

### Setup Steps (manual via dashboard)

1. **Go to** Cloudflare Dashboard → Zero Trust → Access → Applications
2. **Click** Add an application → Self-hosted
3. **Configure**:
   - **Application name**: `Agent Memory Dashboard`
   - **Session duration**: 24h
   - **Same-site cookies**: On
4. **Select identity providers**:
   - Email: Add `chefgroep.nl` domain (require email from this domain)
   - OR: Use `One-Time Pin` for quick test, then switch to email
5. **Create policy**:
   - **Include**: Email → `chefgroep.nl` domain
   - **Exclude**: (empty)
   - **Name**: `chefgroep.nl users only`
6. **Save** → Copy the Application URL
7. **Configure CORS** (optional, for API usage):
   - Under Settings → CORS
   - Add allowed origins if needed

### Policy Details

| Policy | Include | Exclude | Action |
|--------|---------|---------|--------|
| chefgroep.nl users only | Email ending in `@chefgroep.nl` | — | Allow |

### User Experience

1. First visit → Redirect to Cloudflare Access login page
2. Enter email (`username@chefgroep.nl`) → Receive one-time code
3. Enter code → Dashboard loads, session valid for 24h
4. Subsequent visits → Automatic auth, no re-prompt required (until session expires)

### Monitoring

- **Access logs**: Zero Trust → Logs → Access
- **Active sessions**: Zero Trust → Settings → Sessions
- **Audit trail**: All logins are logged with timestamp, IP, and email

### Troubleshooting

- **Can't access dashboard**: Check if email domain is allowed in policy
- **Session expired**: Re-authenticate, session duration is 24h
- **Blocked by WAF**: Check Zero Trust → Firewall → Events
- **Cloudflare Access not working**: Verify DNS CNAME is proxied (orange cloud)
