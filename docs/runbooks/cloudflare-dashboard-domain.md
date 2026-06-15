# Runbook: expose the metrics dashboard on a Cloudflare domain

The agent-memory metrics dashboard runs on `bc-monitor` (`localhost:8787`,
also reachable over Tailscale). It is published to the internet through a
**Cloudflare Tunnel** (no inbound ports, no public IP needed).

## Live

- URL: <https://memory.blackclaw.xyz>
- Origin: `cloudflared` connector on `bc-monitor` → `http://localhost:8787`
- Tunnel: `agent-memory` (cloudflare-managed config)
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

## Moving to `memory.chefgroep.nl`

`chefgroep.nl` / `chefgroep.online` live in Cloudflare account
`3658edc5d94b8eb1fb06790e4b712877`. The fleet currently only holds a *scoped*
API token there (no Zone/Tunnel rights) plus tunnel-connector credentials, so a
new hostname cannot be created from the fleet yet. To switch:

1. Provide an API token on that account with `Cloudflare Tunnel:Edit`,
   `DNS:Edit`, `Zone:Read`, **or** add a Public Hostname to an existing tunnel
   in Zero Trust → Networks → Tunnels and hand over that tunnel token.
2. Re-run the steps above with `TUNNEL_HOSTNAME=memory.chefgroep.nl`.

## Notes / hardening

- The dashboard shows aggregate memory counts only (no secrets), but to lock it
  behind login add a **Cloudflare Access** self-hosted app policy on the
  hostname (Zero Trust → Access → Applications).
- `blackclaw.xyz` has a catch-all dynamic redirect to `chefgroep.nl`; the rule
  expression excludes `http.host eq "memory.blackclaw.xyz"` so the dashboard is
  reachable while every other host keeps redirecting.
