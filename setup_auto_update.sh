#!/bin/bash
# setup_auto_update.sh
# Installiert die automatische CSV-Aktualisierung

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "================================="
echo "🔧 Setup automatische CSV-Aktualisierung"
echo "================================="
echo

# Überprüfe Python3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 nicht gefunden. Bitte installieren."
    exit 1
fi

# Überprüfe pandas
echo "Überprüfe Abhängigkeiten..."
if ! python3 -c "import pandas" 2>/dev/null; then
    echo "📦 Installiere pandas..."
    pip3 install pandas
fi
echo "✓ Alle Abhängigkeiten vorhanden"
echo

# Mache Scripts ausführbar
echo "Mache Scripts ausführbar..."
chmod +x "$SCRIPT_DIR/update_combined_csv.py"
chmod +x "$SCRIPT_DIR/update_combined_csv.sh"
echo "✓ Scripts sind ausführbar"
echo

# Setup Git Hook
echo "Installiere Git Post-Commit Hook..."
mkdir -p "$SCRIPT_DIR/.git/hooks"
cp "$SCRIPT_DIR/post-commit" "$SCRIPT_DIR/.git/hooks/post-commit"
chmod +x "$SCRIPT_DIR/.git/hooks/post-commit"
echo "✓ Git Hook installiert (.git/hooks/post-commit)"
echo

echo "================================="
echo "✅ Setup erfolgreich abgeschlossen!"
echo "================================="
echo
echo "Nächste Schritte:"
echo "1. Manuell ausführen: ./update_combined_csv.sh"
echo "2. Via Cron planen: crontab -e"
echo "3. Git Hook verwendet automatische Updates bei Commits"
echo
