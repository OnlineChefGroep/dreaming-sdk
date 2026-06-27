"""Always-on metrics dashboard for the agent memory layer.

Serves an auto-refreshing HTML overview plus JSON endpoints, reading from the
Postgres SSOT. Designed to run as a systemd service on a fleet host (bc-monitor)
and be viewed any time over Tailscale.

Run:
    uv run --extra web dream-memory serve --host 0.0.0.0 --port 8787
or:
    uv run uvicorn cursor_dreaming_memory.dashboard:app --host 0.0.0.0 --port 8787
"""

from __future__ import annotations

from typing import Any

from dreaming_memory.config import FleetConfig
from dreaming_memory.store.postgres import AgentMemoryStore

try:
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse, JSONResponse
except ImportError:  # pragma: no cover
    FastAPI = None  # type: ignore[assignment]

_store: AgentMemoryStore | None = None


def _get_store() -> AgentMemoryStore:
    global _store  # noqa: PLW0603
    if _store is None:
        _store = AgentMemoryStore()
    return _store


def get_metrics(days: int = 14) -> dict[str, Any]:
    return _get_store().metrics(days=days)


def _bars(rows: list[dict[str, Any]], total: int) -> str:
    out = []
    for r in rows:
        pct = (r["count"] / total * 100) if total else 0
        out.append(
            f'<div class="row"><span class="k">{r["key"]}</span>'
            f'<span class="bar"><i style="width:{pct:.1f}%"></i></span>'
            f'<span class="n">{r["count"]}</span></div>'
        )
    return "\n".join(out)


def _sparkline(per_day: list[dict[str, Any]]) -> str:
    if not per_day:
        return '<span class="muted">no data</span>'
    mx = max(d["count"] for d in per_day) or 1
    cells = []
    for d in per_day:
        h = int(d["count"] / mx * 40) + 2
        cells.append(
            f'<span class="spark" title="{d["day"]}: {d["count"]}" '
            f'style="height:{h}px"></span>'
        )
    return '<div class="sparkrow">' + "".join(cells) + "</div>"


def render_html(m: dict[str, Any]) -> str:
    total = m["total"]
    recent_rows = "\n".join(
        f"<tr><td>{r['created_at'][:19].replace('T',' ')}</td>"
        f"<td><span class='tag'>{r['source']}</span></td>"
        f"<td>{r['memory_type']}</td><td>{r['session_type']}</td>"
        f"<td class='muted'>{r['agent_id']}</td><td>{r['preview']}</td></tr>"
        for r in m["recent"]
    )
    return f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="30">
<title>Agent Memory — Metrics</title>
<style>
:root{{--bg:#0b0e14;--card:#141925;--fg:#e6edf3;--muted:#8b98a9;--accent:#4f9cff;--accent2:#37d39b}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 ui-sans-serif,system-ui,Segoe UI,Roboto}}
header{{padding:20px 28px;border-bottom:1px solid #222b3a;display:flex;align-items:baseline;gap:16px;flex-wrap:wrap}}
h1{{font-size:18px;margin:0}}
.muted{{color:var(--muted)}}
.wrap{{padding:24px 28px;display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px}}
.card{{background:var(--card);border:1px solid #222b3a;border-radius:12px;padding:18px}}
.card h2{{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:0 0 14px}}
.big{{font-size:34px;font-weight:700}}
.row{{display:flex;align-items:center;gap:10px;margin:6px 0}}
.row .k{{width:130px;color:var(--fg);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.row .bar{{flex:1;background:#0b0e14;border-radius:6px;height:10px;overflow:hidden}}
.row .bar i{{display:block;height:100%;background:linear-gradient(90deg,var(--accent),var(--accent2))}}
.row .n{{width:46px;text-align:right;color:var(--muted)}}
.sparkrow{{display:flex;align-items:flex-end;gap:3px;height:48px}}
.spark{{width:10px;background:linear-gradient(180deg,var(--accent),var(--accent2));border-radius:2px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
td,th{{padding:7px 8px;border-bottom:1px solid #1d2533;text-align:left}}
th{{color:var(--muted);font-weight:500;text-transform:uppercase;font-size:11px;letter-spacing:.05em}}
.tag{{background:#1d2942;color:var(--accent);padding:1px 8px;border-radius:20px;font-size:11px}}
.full{{grid-column:1/-1}}
a{{color:var(--accent)}}
</style></head><body>
<header>
  <h1>🧠 Agent Memory — Unified Insight Layer</h1>
  <span class="muted">OCI Postgres SSOT · auto-refresh 30s · last activity {m['last_activity'] or '—'}</span>
</header>
<div class="wrap">
  <div class="card"><h2>Total records</h2><div class="big">{total}</div>
    <div class="muted">Triage decisions: {m['triage_decisions']}</div></div>
  <div class="card"><h2>Activity (last 14 days)</h2>{_sparkline(m['per_day'])}</div>
  <div class="card"><h2>By source</h2>{_bars(m['by_source'], total)}</div>
  <div class="card"><h2>By memory type</h2>{_bars(m['by_memory_type'], total)}</div>
  <div class="card"><h2>By session type</h2>{_bars(m['by_session_type'], total)}</div>
  <div class="card"><h2>Top agents</h2>{_bars(m['by_agent'], total)}</div>
  <div class="card full"><h2>Recent activity</h2>
    <table><tr><th>Time (UTC)</th><th>Source</th><th>Type</th><th>Session</th><th>Agent</th><th>Preview</th></tr>
    {recent_rows}</table>
    <p class="muted" style="margin-top:14px">JSON: <a href="/api/metrics">/api/metrics</a> · health: <a href="/healthz">/healthz</a></p>
  </div>
</div></body></html>"""


if FastAPI is not None:
    app = FastAPI(title="Agent Memory Metrics", version="0.1.0")

    @app.get("/", response_class=HTMLResponse)
    def index() -> Any:
        return HTMLResponse(render_html(get_metrics()))

    @app.get("/api/metrics")
    def api_metrics(days: int = 14) -> Any:
        return JSONResponse(get_metrics(days))

    @app.get("/healthz")
    def healthz() -> Any:
        cfg = FleetConfig.load()
        try:
            _get_store().metrics(days=1)
            return JSONResponse({"status": "ok", "config": cfg.status()})
        except Exception:  # noqa: BLE001
            return JSONResponse({"status": "error", "detail": "metrics unavailable"}, status_code=500)
else:  # pragma: no cover
    app = None  # type: ignore[assignment]


def serve(host: str = "0.0.0.0", port: int = 8787) -> None:
    import uvicorn

    uvicorn.run("cursor_dreaming_memory.dashboard:app", host=host, port=port, log_level="info")
