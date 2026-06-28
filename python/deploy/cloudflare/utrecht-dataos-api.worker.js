// utrecht-dataos-control-plane-api  (Cloudflare Worker, custom domain api.chefgroep.online)
// Placeholder control-plane API surface + reverse proxy for the agent-memory dashboard.
// Bindings (kept on deploy via keep_bindings): UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN

const DASHBOARD_ORIGIN = 'https://memory.chefgroep.online';

addEventListener('fetch', (event) => {
  event.respondWith(handle(event.request));
});

async function handle(request) {
  const url = new URL(request.url);
  const path = url.pathname;

  // Dashboard, served under the online API at /dashboard
  if (path === '/dashboard' || path === '/dashboard/' || path.startsWith('/dashboard/')) {
    const sub = path.length > '/dashboard'.length ? path.slice('/dashboard'.length) : '/';
    return proxy(DASHBOARD_ORIGIN + sub + url.search, request);
  }
  // Footer links / refresh targets used by the dashboard HTML
  if (path === '/api/metrics' || path === '/healthz') {
    return proxy(DASHBOARD_ORIGIN + path + url.search, request);
  }

  const hasUpstash =
    typeof UPSTASH_REDIS_REST_URL !== 'undefined' && !!UPSTASH_REDIS_REST_URL;
  const body = {
    service: 'utrecht-dataos-control-plane-api',
    status: 'ok',
    hostname: url.hostname,
    path,
    upstash_bound: hasUpstash,
    dashboard: 'https://api.chefgroep.online/dashboard',
    dashboard_origin: DASHBOARD_ORIGIN,
    note: 'placeholder API surface for Utrecht Data OS control plane',
    ts: new Date().toISOString(),
  };
  return new Response(JSON.stringify(body, null, 2), {
    status: 200,
    headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' },
  });
}

async function proxy(target, request) {
  const upstream = await fetch(target, {
    method: "GET",
    headers: { accept: request.headers.get("accept") || "*/*" },
    redirect: "follow",
  });
  const ct = upstream.headers.get("content-type") || "text/html; charset=utf-8";
  const headers = new Headers({ "content-type": ct, "cache-control": "no-store" });
  return new Response(upstream.body, { status: upstream.status, headers });
}
