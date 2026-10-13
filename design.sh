#!/usr/bin/env bash
# design.sh — startar utföraren i designfasens band för en kund (BESLUT.md, tillägget 2026-10-13: formgivningen lokalt i
# Astro; skillen designfas): en interaktiv Claude Code-session i repots rot som arbetar i riktningarnas Astro-projekt, med
# kundvakten för kunden, flödets tjänster (Refero, Mobbin, Motion, 21st) med --strict-mcp-config och designgodkännandet
# nekat för sessionen. Startar inget annat. En ny kund får designfasen i läget astro (designfas.py ny).
#   ./design.sh <slug>          (kundunderlaget först: kontroller/prototyp.py <slug> --forbered; sedan researchen, planen
#                                och projekten: kontroller/prototyp.py <slug>, som lämnar riktningarna till bandet)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
[ $# -eq 1 ] || { echo "användning: ./design.sh <slug>" >&2; exit 2; }
cd "$ROOT"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/designfas.py" status "$1" >/dev/null 2>&1 \
  || "$ROOT/.venv/bin/python" -B "$ROOT/kontroller/designfas.py" ny "$1" >/dev/null
exec "$ROOT/.venv/bin/python" -B "$ROOT/kontroller/designfas.py" start "$1"
