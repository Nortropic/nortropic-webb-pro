#!/usr/bin/env bash
# design.sh — startar utföraren i designfasen i Claude Design för en kund (kunskap/claude-design.md): en interaktiv Claude
# Code-session i repots rot med skillen designfas, kundvakten för kunden, flödets tjänster (Refero, Mobbin, Motion, 21st)
# med --strict-mcp-config och designgodkännandet nekat för sessionen. Startar inget annat.
#   ./design.sh <slug>          (kundunderlaget och researchen först: kontroller/prototyp.py <slug> --forbered, sedan <slug>)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
[ $# -eq 1 ] || { echo "användning: ./design.sh <slug>" >&2; exit 2; }
cd "$ROOT"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/designfas.py" status "$1" >/dev/null 2>&1 \
  || "$ROOT/.venv/bin/python" -B "$ROOT/kontroller/designfas.py" ny "$1" >/dev/null
exec "$ROOT/.venv/bin/python" -B "$ROOT/kontroller/designfas.py" start "$1"
