#!/bin/bash
# update_combined_csv.sh
# Wrapper für die Aktualisierung der kombinierten CSV-Dateien
# Kann auch als Cron-Job ausgeführt werden

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/update_combined_csv.py"

# Überprüfe, ob Python3 verfügbar ist
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 ist nicht installiert" >&2
    exit 1
fi

# Überprüfe, ob pandas verfügbar ist
if ! python3 -c "import pandas" 2>/dev/null; then
    echo "❌ pandas ist nicht installiert"
    echo "   Installiere mit: pip3 install pandas"
    exit 1
fi

# Überprüfe, ob das Script existiert
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "❌ Python-Script nicht gefunden: $PYTHON_SCRIPT" >&2
    exit 1
fi

# Führe das Python-Script aus
python3 "$PYTHON_SCRIPT"
exit $?
