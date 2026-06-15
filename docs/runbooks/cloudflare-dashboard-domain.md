# Runbook: expose the metrics dashboard on a Cloudflare domain

The agent-memory metrics dashboard runs on `bc-monitor` (`localhost:8787`,
also reachable over Tailscale). It is published to the internet through a
**Cloudflare Tunnel** (no inbound ports, no public IP needed).

## Live

- URL: <https://memory.chefgroep.nl>
- Origin: `cloudflared` connector on `bc-monitor` → `http://localhost:8787`
- Tunnel: `agent-memory` (cloudflare-managed config) in account `3658edc5…`
- Connector service: `systemctl status cloudflared` on `bc-monitor`

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
