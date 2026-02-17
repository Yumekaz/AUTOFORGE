#!/usr/bin/env python3
"""
AUTOFORGE Live HMI Dashboard

Serves a minimal web HMI that displays live values from the BMS service stub:
- battery_soc
- battery_temperature
- vehicle_speed
- tire pressures
- health status / warnings
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AUTOFORGE Live HMI</title>
  <style>
    :root {
      --bg: #0e1116;
      --panel: #161b22;
      --text: #e6edf3;
      --muted: #8b949e;
      --good: #3fb950;
      --warn: #d29922;
      --bad: #f85149;
    }
    body { margin: 0; background: var(--bg); color: var(--text); font-family: Segoe UI, Arial, sans-serif; }
    .wrap { max-width: 980px; margin: 24px auto; padding: 0 16px; }
    h1 { margin: 0 0 16px; font-size: 28px; letter-spacing: 0.5px; }
    .muted { color: var(--muted); }
    .grid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
    .card { background: var(--panel); border: 1px solid #263041; border-radius: 12px; padding: 14px; }
    .k { font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.8px; }
    .v { font-size: 28px; margin-top: 4px; font-weight: 650; }
    .status-good { color: var(--good); }
    .status-warn { color: var(--warn); }
    .status-bad { color: var(--bad); }
    ul { margin: 8px 0 0; padding-left: 18px; }
    code { background: #1f2937; padding: 2px 6px; border-radius: 4px; }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>AUTOFORGE Live HMI</h1>
    <p class="muted">Source: <code>/bms/latest</code> via service stub. Refresh: 500ms.</p>
    <div class="grid">
      <div class="card"><div class="k">Battery SOC</div><div id="soc" class="v">--</div></div>
      <div class="card"><div class="k">Battery Temp</div><div id="temp" class="v">--</div></div>
      <div class="card"><div class="k">Vehicle Speed</div><div id="speed" class="v">--</div></div>
      <div class="card"><div class="k">Health Status</div><div id="health" class="v">--</div></div>
    </div>
    <div class="grid" style="margin-top:12px;">
      <div class="card"><div class="k">Tire FL</div><div id="tp_fl" class="v">--</div></div>
      <div class="card"><div class="k">Tire FR</div><div id="tp_fr" class="v">--</div></div>
      <div class="card"><div class="k">Tire RL</div><div id="tp_rl" class="v">--</div></div>
      <div class="card"><div class="k">Tire RR</div><div id="tp_rr" class="v">--</div></div>
    </div>
    <div class="card" style="margin-top:12px;">
      <div class="k">Warnings</div>
      <ul id="warnings"><li class="muted">No warnings.</li></ul>
    </div>
    <p class="muted">Last update: <span id="updated">--</span></p>
  </div>
  <script>
    function asNum(v, suffix) {
      if (v === undefined || v === null || Number.isNaN(Number(v))) return "--";
      return `${Number(v).toFixed(1)}${suffix}`;
    }

    function healthClass(status) {
      if (status >= 2) return "status-bad";
      if (status >= 1) return "status-warn";
      return "status-good";
    }

    async function tick() {
      try {
        const r = await fetch("/api/latest", { cache: "no-store" });
        const d = await r.json();
        const s = d.signals || {};
        const resp = d.response || {};
        const warnings = Array.isArray(resp.warnings) ? resp.warnings : [];

        document.getElementById("soc").textContent = asNum(s.battery_soc, "%");
        document.getElementById("temp").textContent = asNum(s.battery_temperature, " C");
        document.getElementById("speed").textContent = asNum(s.vehicle_speed, " km/h");
        document.getElementById("tp_fl").textContent = asNum(s.tire_pressure_fl, " bar");
        document.getElementById("tp_fr").textContent = asNum(s.tire_pressure_fr, " bar");
        document.getElementById("tp_rl").textContent = asNum(s.tire_pressure_rl, " bar");
        document.getElementById("tp_rr").textContent = asNum(s.tire_pressure_rr, " bar");

        const hs = Number(resp.health_status || 0);
        const healthEl = document.getElementById("health");
        healthEl.textContent = `${hs}`;
        healthEl.className = `v ${healthClass(hs)}`;

        const wl = document.getElementById("warnings");
        wl.innerHTML = "";
        if (!warnings.length) {
          wl.innerHTML = '<li class="muted">No warnings.</li>';
        } else {
          for (const w of warnings) {
            const li = document.createElement("li");
            li.textContent = `${w.code ?? "----"}: ${w.message ?? "warning"}`;
            wl.appendChild(li);
          }
        }

        const ts = Number(d.timestamp_unix || 0);
        document.getElementById("updated").textContent = ts ? new Date(ts * 1000).toLocaleTimeString() : "--";
      } catch (e) {
        document.getElementById("updated").textContent = `disconnected (${e})`;
      }
    }
    setInterval(tick, 500);
    tick();
  </script>
</body>
</html>
"""


class DashboardHandler(BaseHTTPRequestHandler):
    service_url = "http://localhost:30509"

    def _write_json(self, payload: dict, status: int = 200) -> None:
        out = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def do_GET(self):  # noqa: N802
        if self.path in ("/", "/index.html"):
            out = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)
            return

        if self.path == "/api/latest":
            req = urllib.request.Request(f"{self.service_url}/bms/latest", method="GET")
            try:
                with urllib.request.urlopen(req, timeout=2) as r:
                    data = json.loads(r.read().decode("utf-8"))
                self._write_json(data, 200)
            except urllib.error.URLError as exc:
                self._write_json({"error": "service_unavailable", "details": str(exc)}, 503)
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):  # noqa: A003
        return


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AUTOFORGE live HMI dashboard")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=30600)
    parser.add_argument("--service-url", default="http://localhost:30509")
    args = parser.parse_args()

    DashboardHandler.service_url = args.service_url.rstrip("/")
    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    print(f"[HMI] Dashboard running at http://{args.host}:{args.port}")
    print(f"[HMI] Upstream service: {DashboardHandler.service_url}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
