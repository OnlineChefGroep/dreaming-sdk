#!/usr/bin/env python3
"""Create/Update a Cloudflare Tunnel that exposes the metrics dashboard on a domain.

Requires a Cloudflare API token with:
  - Account → Cloudflare Tunnel: Edit
  - Zone → DNS: Edit  (on the target zone)
  - Zone → Zone: Read

Env:
  CLOUDFLARE_API_TOKEN   (scoped as above)
  CLOUDFLARE_ACCOUNT_ID
  TUNNEL_HOSTNAME        e.g. memory.chefgroep.nl
  TUNNEL_NAME            default: agent-memory
  LOCAL_SERVICE          default: http://localhost:8787

Outputs the tunnel run token. Install the connector with:
  sudo cloudflared service install <TOKEN>
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

API = "https://api.cloudflare.com/client/v4"


def _auth_headers() -> dict:
    """Bearer token, or legacy global-key (X-Auth-Email/Key) if provided."""
    email = os.environ.get("CLOUDFLARE_EMAIL")
    gkey = os.environ.get("CLOUDFLARE_GLOBAL_API_KEY")
    if email and gkey:
        return {"X-Auth-Email": email, "X-Auth-Key": gkey}
    return {"Authorization": f"Bearer {os.environ['CLOUDFLARE_API_TOKEN']}"}


def _req(method: str, path: str, token: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json", **_auth_headers()}
    req = urllib.request.Request(
        f"{API}{path}",
        data=data,
        method=method,
        headers=headers,
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        out = json.loads(resp.read().decode())
    if not out.get("success"):
        raise SystemExit(f"CF API error {method} {path}: {out.get('errors')}")
    return out


def main() -> None:
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    acct = os.environ["CLOUDFLARE_ACCOUNT_ID"]
    hostname = os.environ["TUNNEL_HOSTNAME"]
    name = os.environ.get("TUNNEL_NAME", "agent-memory")
    service = os.environ.get("LOCAL_SERVICE", "http://localhost:8787")
    zone_name = ".".join(hostname.split(".")[-2:])

    # 1. Resolve zone
    zones = _req("GET", f"/zones?name={zone_name}", token)["result"]
    if not zones:
        raise SystemExit(f"Zone {zone_name} not found / not authorized")
    zone_id = zones[0]["id"]

    # 2. Create (or reuse) the tunnel — cloudflare-managed config
    existing = _req("GET", f"/accounts/{acct}/cfd_tunnel?name={name}&is_deleted=false", token)
    if existing["result"]:
        tunnel = existing["result"][0]
        tunnel_id = tunnel["id"]
        tok = _req("GET", f"/accounts/{acct}/cfd_tunnel/{tunnel_id}/token", token)["result"]
    else:
        created = _req(
            "POST",
            f"/accounts/{acct}/cfd_tunnel",
            token,
            {"name": name, "config_src": "cloudflare"},
        )["result"]
        tunnel_id = created["id"]
        tok = created["token"]

    # 3. Configure ingress
    _req(
        "PUT",
        f"/accounts/{acct}/cfd_tunnel/{tunnel_id}/configurations",
        token,
        {
            "config": {
                "ingress": [
                    {"hostname": hostname, "service": service},
                    {"service": "http_status:404"},
                ]
            }
        },
    )

    # 4. DNS CNAME → tunnel
    cname = f"{tunnel_id}.cfargotunnel.com"
    recs = _req("GET", f"/zones/{zone_id}/dns_records?name={hostname}", token)["result"]
    payload = {"type": "CNAME", "name": hostname, "content": cname, "proxied": True}
    if recs:
        _req("PUT", f"/zones/{zone_id}/dns_records/{recs[0]['id']}", token, payload)
    else:
        _req("POST", f"/zones/{zone_id}/dns_records", token, payload)

    print(json.dumps({"tunnel_id": tunnel_id, "hostname": hostname, "url": f"https://{hostname}"}))
    print("TUNNEL_TOKEN=" + tok, file=sys.stderr)


if __name__ == "__main__":
    main()
