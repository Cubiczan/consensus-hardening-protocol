#!/usr/bin/env python3
"""
CHP Enterprise Demo — Run All Verticals (Python Launcher)
==========================================================
Launches each CHP sandbox demo as a subprocess and generates a
combined HTML audit report. Cross-platform: macOS, Linux, Windows.

Usage:
    python3 examples/run-all.py                    # Run all and generate combined report
    python3 examples/run-all.py --skip-html         # Run all without HTML report
    python3 examples/run-all.py --vertical finance   # Run single vertical
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXAMPLES_DIR = Path(__file__).resolve().parent

VERTICALS = {
    "finance": {
        "script": "chp_sandbox_demo.py",
        "icon": "💰",
        "title": "Finance",
        "json_key": "finance",
    },
    "healthcare": {
        "script": "chp_sandbox_demo_healthcare.py",
        "icon": "🏥",
        "title": "Healthcare",
        "json_key": "healthcare",
    },
    "legal": {
        "script": "chp_sandbox_demo_legal.py",
        "icon": "⚖️",
        "title": "Legal",
        "json_key": "legal",
    },
    "engineering": {
        "script": "chp_sandbox_demo_engineering.py",
        "icon": "🔧",
        "title": "Engineering",
        "json_key": "engineering",
    },
}


def run_vertical(name: str, info: dict) -> list[dict[str, Any]]:
    """Run a vertical's demo script via subprocess and read its JSON output."""
    script_path = EXAMPLES_DIR / info["script"]
    if not script_path.exists():
        print(f"  ❌ Missing: {script_path}")
        return []

    json_path = EXAMPLES_DIR / f"chp_sandbox_demo_{name}.json"
    # Remove stale JSON output
    json_path.unlink(missing_ok=True)

    # Finance uses the generic json key (already had finance output path)
    if name == "finance":
        json_path = EXAMPLES_DIR / "chp_sandbox_demo_finance.json"
        json_path.unlink(missing_ok=True)

    print(f"\n  {'─' * 68}")
    print(f"  {info['icon']} Running {info['title']} vertical: {info['script']}")
    print(f"  {'─' * 68}")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=EXAMPLES_DIR,
        capture_output=True,
        text=True,
        timeout=60,
    )

    # Print stdout
    for line in result.stdout.strip().split("\n"):
        print(f"    {line}")

    if result.returncode != 0:
        print(f"  ❌ {info['title']} failed with code {result.returncode}")
        print(f"    stderr: {result.stderr.strip()[:200]}")
        return []

    if result.stderr.strip():
        print(f"    stderr: {result.stderr.strip()[:200]}")

    # Read JSON output
    if json_path.exists():
        data = json.loads(json_path.read_text())
        # Some scripts return a list (multiple scenarios), some a single packet
        if isinstance(data, list):
            return data
        return [data]
    else:
        print(f"  ⚠️  No JSON output found at {json_path.name}")
        return []


def generate_combined_html(all_results: dict[str, list[dict]]) -> str:
    """Generate a combined HTML report from all vertical results."""
    icon = {"PASS": "✅", "FAIL": "❌", "ESCALATE": "⚠️"}

    vertical_rows = ""
    total_scenarios = 0
    total_pass = 0
    total_escalate = 0
    total_fail = 0

    # Build combined scenario list
    for vname, packets in all_results.items():
        vinfo = VERTICALS[vname]
        for pkt in packets:
            total_scenarios += 1
            gate = pkt.get("gate_result", {})
            lock = pkt.get("lock_state", "UNKNOWN")
            foundation = pkt.get("foundation", {})
            attack = pkt.get("attack", {})
            sandbox_log = pkt.get("sandbox_replay_log", [])
            verdict_str = gate.get("verdict", "UNKNOWN")

            if verdict_str == "PASS":
                total_pass += 1
            elif verdict_str == "ESCALATE":
                total_escalate += 1
            else:
                total_fail += 1

            discrepancies = gate.get("discrepancies", [])
            if not discrepancies:
                discrepancies = ["Issue identified by CHP adversary"]

            lock_css = lock.lower().replace("_", "-")

            vertical_rows += f"""
            <div class="scenario-card state-{lock_css}">
                <div class="card-header">
                    <span class="verdict-icon">{icon.get(verdict_str, '❓')}</span>
                    <span class="vertical-badge">{vinfo['icon']} {vinfo['title']}</span>
                    <h2>{pkt.get('title', 'Unknown')[:80]}</h2>
                    <span class="badge badge-{lock_css}">{lock}</span>
                </div>
                <div class="card-body">
                    <div class="section">
                        <h3>📋 Foundation Disclosure</h3>
                        <p><strong>Agent:</strong> {foundation.get('agent_id', 'unknown')}</p>
                        <p><strong>Claim:</strong> {str(foundation.get('claim', ''))[:120]}</p>
                        <p><strong>Confidence:</strong> {foundation.get('confidence', 0):.0%}</p>
                    </div>
                    <div class="section">
                        <h3>⚔️ Foundation Attack</h3>
                        <p><strong>Vulnerability:</strong> {str(attack.get('vulnerability', ''))[:120]}</p>
                        <p><strong>Severity:</strong> {attack.get('severity', 0):.0%}</p>
                    </div>
                    <div class="section">
                        <h3>🚧 R0 Gate</h3>
                        <p><strong>Verdict:</strong> <span class="verdict-tag verdict-{verdict_str.lower()}">{verdict_str}</span></p>
                        <p><strong>Adjusted Confidence:</strong> {gate.get('adjusted_confidence', 0):.0%}</p>
                        <ul>{''.join(f'<li>🔴 {str(d)[:100]}</li>' for d in discrepancies[:3])}</ul>
                    </div>
                    <div class="section">
                        <h3>🔒 Sandbox Replay</h3>
                        <p><strong>Hash:</strong> <code>{pkt.get('sandbox_replay_hash', 'N/A')[:50]}...</code></p>
                        <table class="replay-table">
                            <tr><th>Step</th><th>Action</th><th>Hash</th><th>Status</th></tr>
                            {''.join(f'<tr><td>{s["step"]}</td><td>{s["action"]}</td><td><code>{s["hash"]}</code></td><td class="status-{s["status"]}">{s["status"]}</td></tr>' for s in sandbox_log)}
                        </table>
                    </div>
                </div>
            </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CHP Enterprise Demo — All Verticals</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; padding: 20px; }}
  .container {{ max-width: 1100px; margin: 0 auto; }}
  h1 {{ color: #58a6ff; margin-bottom: 8px; font-size: 28px; }}
  .subtitle {{ color: #8b949e; margin-bottom: 24px; font-size: 14px; }}
  .summary-bar {{ display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }}
  .summary-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; flex: 1; min-width: 140px; }}
  .summary-card h3 {{ color: #8b949e; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }}
  .summary-card .value {{ color: #f0f6fc; font-size: 24px; font-weight: 600; margin-top: 4px; }}
  .scenario-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; margin-bottom: 20px; overflow: hidden; }}
  .state-pass {{ border-left: 4px solid #3fb950; }}
  .state-provisional_lock {{ border-left: 4px solid #d29922; }}
  .state-pending {{ border-left: 4px solid #f85149; }}
  .card-header {{ display: flex; align-items: center; gap: 12px; padding: 16px; background: #1c2128; border-bottom: 1px solid #30363d; flex-wrap: wrap; }}
  .card-header h2 {{ color: #f0f6fc; font-size: 16px; flex: 1; min-width: 200px; }}
  .verdict-icon {{ font-size: 24px; }}
  .vertical-badge {{ background: #1c2128; padding: 4px 10px; border-radius: 12px; font-size: 13px; color: #58a6ff; font-weight: 600; }}
  .badge {{ padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; text-transform: uppercase; }}
  .badge-locked {{ background: #1b3a2b; color: #3fb950; }}
  .badge-provisional_lock {{ background: #3d2e00; color: #d29922; }}
  .badge-exploring {{ background: #3d1115; color: #f85149; }}
  .card-body {{ padding: 16px; }}
  .section {{ margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #21262d; }}
  .section:last-child {{ border-bottom: none; margin-bottom: 0; }}
  .section h3 {{ color: #58a6ff; font-size: 14px; margin-bottom: 6px; }}
  .section p {{ margin-bottom: 3px; line-height: 1.5; font-size: 13px; }}
  .section ul {{ margin: 4px 0 0 20px; }}
  .section ul li {{ margin-bottom: 2px; font-size: 13px; }}
  .verdict-tag {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 12px; }}
  .verdict-pass {{ background: #1b3a2b; color: #3fb950; }}
  .verdict-fail {{ background: #3d1115; color: #f85149; }}
  .verdict-escalate {{ background: #3d2e00; color: #d29922; }}
  .replay-table {{ width: 100%; border-collapse: collapse; margin-top: 6px; font-size: 12px; }}
  .replay-table th {{ text-align: left; padding: 6px; background: #1c2128; color: #8b949e; font-size: 11px; text-transform: uppercase; border-bottom: 1px solid #30363d; }}
  .replay-table td {{ padding: 6px; border-bottom: 1px solid #21262d; }}
  .replay-table code {{ background: #1c2128; padding: 1px 4px; border-radius: 3px; font-size: 11px; }}
  .status-verified {{ color: #3fb950; }}
  code {{ background: #1c2128; padding: 2px 6px; border-radius: 3px; font-size: 11px; }}
  .footer {{ text-align: center; color: #484f58; font-size: 12px; margin-top: 40px; padding: 20px; border-top: 1px solid #21262d; }}
</style>
</head>
<body>
<div class="container">
  <h1>🛡️ CHP Enterprise Demo Suite</h1>
  <p class="subtitle">{total_scenarios} Scenarios · {len(all_results)} Verticals · Full Compliance Chain</p>

  <div class="summary-bar">
    <div class="summary-card"><h3>Scenarios</h3><div class="value">{total_scenarios}</div></div>
    <div class="summary-card"><h3>Verticals</h3><div class="value">{len(all_results)}</div></div>
    <div class="summary-card"><h3>R0 ESCALATE</h3><div class="value" style="color:#d29922">{total_escalate}</div></div>
    <div class="summary-card"><h3>R0 FAIL</h3><div class="value" style="color:#f85149">{total_fail}</div></div>
    <div class="summary-card"><h3>R0 PASS</h3><div class="value" style="color:#3fb950">{total_pass}</div></div>
    <div class="summary-card"><h3>Generated</h3><div class="value" style="font-size:14px">{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</div></div>
  </div>

  {vertical_rows}

  <div class="footer">
    <p>Consensus Hardening Protocol — Enterprise Demo Suite v1.0</p>
    <p>Run: <code>python3 examples/run-all.py</code> → produces this combined report</p>
  </div>
</div>
</body>
</html>"""
    return html


def main():
    import argparse

    parser = argparse.ArgumentParser(description="CHP Enterprise Demo — Run All Verticals")
    parser.add_argument("--skip-html", action="store_true", help="Skip generating combined HTML report")
    parser.add_argument("--vertical", "-v", choices=list(VERTICALS.keys()) + ["all"], default="all")
    args = parser.parse_args()

    print("=" * 72)
    print("🛡️  CHP Enterprise Demo Suite v1.0")
    print("    5 Scenarios · 4 Verticals · Full Compliance Chain")
    print("=" * 72)

    verticals_to_run = list(VERTICALS.keys()) if args.vertical == "all" else [args.vertical]

    all_results: dict[str, list[dict]] = {}

    for vname in verticals_to_run:
        info = VERTICALS[vname]
        packets = run_vertical(vname, info)
        all_results[vname] = packets

    total = sum(len(v) for v in all_results.values())

    if not args.skip_html and all_results:
        html = generate_combined_html(all_results)
        report_path = EXAMPLES_DIR / "chp_enterprise_demo.html"
        report_path.write_text(html)

        json_path = EXAMPLES_DIR / "chp_enterprise_demo.json"
        json_path.write_text(json.dumps(all_results, indent=2, default=str))

    print(f"\n{'=' * 72}")
    verdict_str = "✅" if total > 0 else "❌"
    print(f"  {verdict_str} Suite complete: {total} scenarios across {len(all_results)} verticals")
    if all_results:
        print(f"  📄 Combined HTML: {EXAMPLES_DIR / 'chp_enterprise_demo.html'}")
        print(f"  📄 Combined JSON:  {EXAMPLES_DIR / 'chp_enterprise_demo.json'}")
    print(f"{'=' * 72}")


if __name__ == "__main__":
    main()
