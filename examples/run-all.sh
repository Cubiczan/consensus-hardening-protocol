#!/usr/bin/env bash
# CHP Enterprise Demo — Run All Verticals
# =========================================
# Launches all CHP sandbox demos across verticals:
#   Finance  (chp_sandbox_demo.py)
#   Supply Chain (included in chp_sandbox_demo.py)
#   Healthcare (chp_sandbox_demo_healthcare.py)
#   Legal (chp_sandbox_demo_legal.py)
#   Engineering (chp_sandbox_demo_engineering.py)
#
# Usage: bash examples/run-all.sh
#        python3 examples/run-all.py  (preferred — cross-platform)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "══════════════════════════════════════════════════════════════════════"
echo "  CHP Enterprise Demo Suite — 5 Verticals"
echo "  Consensus Hardening Protocol: Compliance Chain Demo"
echo "══════════════════════════════════════════════════════════════════════"
echo ""

VERTICALS=(
    "chp_sandbox_demo.py"
    "chp_sandbox_demo_healthcare.py"
    "chp_sandbox_demo_legal.py"
    "chp_sandbox_demo_engineering.py"
)

FAILED=0

for script in "${VERTICALS[@]}"; do
    if [ ! -f "$script" ]; then
        echo "  ❌ Missing: $script"
        FAILED=$((FAILED + 1))
        continue
    fi

    echo ""
    echo "──────────────────────────────────────────────────────────────────────"
    echo "  Running: $script"
    echo "──────────────────────────────────────────────────────────────────────"
    python3 "$script" || { echo "  ❌ $script failed"; FAILED=$((FAILED + 1)); }
    echo ""
done

echo "══════════════════════════════════════════════════════════════════════"
if [ "$FAILED" -eq 0 ]; then
    echo "  ✅ All $(( ${#VERTICALS[@]} )) verticals completed successfully!"
else
    echo "  ⚠️  $FAILED/$(( ${#VERTICALS[@]} )) verticals had errors"
fi
echo "══════════════════════════════════════════════════════════════════════"
