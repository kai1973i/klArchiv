# 📊 Scripts für automatische Klimadaten-Aktualisierung

## 🚀 Schnellstart

```bash
# Einmalige Einrichtung
bash setup_auto_update.sh

# Dann eine Aktualisierung durchführen
./update_combined_csv.sh
```

---

## 📁 Alle verfügbaren Scripts

### 1. **update_combined_csv.py** ⭐ (Hauptscript)
**Zweck:** Kombiniert Rohdaten und erstellt aktualisierte CSV-Dateien

**Direkter Aufruf:**
```bash
python3 update_combined_csv.py
```

**Was es macht:**
- Liest alle `produkt_klima_tag_*.txt` Dateien aus historischen & aktuellen Daten
- Kombiniert beide Quellen
- Entfernt Duplikate (neueste Version gewinnt)
- Generiert zwei Ausgabe-Dateien:
  - `produkt_klima_tag_combined.csv` (Rohformat)
  - `produkt_klima_tag_combined_klartext.csv` (Mit deutschen Spaltennamen)

**Output:** 49.546+ Einträge (Stand: 2026-06-29)

---

### 2. **update_combined_csv.sh**
**Zweck:** Bash-Wrapper mit Fehlerprüfung

**Aufruf:**
```bash
./update_combined_csv.sh
```

**Vorteile:**
- Überprüft Python3 Installation
- Überprüft pandas-Modul
- Bessere Fehlerbehandlung
- Ideal für Cron-Jobs

---

### 3. **setup_auto_update.sh**
**Zweck:** Automatische Einrichtung des ganzen Systems

**Aufruf:**
```bash
bash setup_auto_update.sh
```

**Was es macht:**
- ✓ Überprüft Python3 & pandas
- ✓ Macht alle Scripts ausführbar
- ✓ Installiert Git-Hook für Auto-Updates

**Nur einmalig nötig!**

---

### 4. **post-commit** (Git Hook)
**Zweck:** Automatische CSV-Aktualisierung nach Git-Commits

**Wo:** `.git/hooks/post-commit`

**Automatische Ausführung:**
- Wird nach jedem `git commit` ausgeführt
- Prüft ob neue Klimadaten eingecheckt wurden
- Aktualisiert die CSVs automatisch
- Installiert von `setup_auto_update.sh`

---

## 🔄 Verwendungsszenarien

### Szenario 1: Einmalige Aktualisierung
```bash
cd /home/kai1973i/dev/klArchiv
python3 update_combined_csv.py
```

### Szenario 2: Automatische tägliche Aktualisierung (Cron)
```bash
# Öffne Cron-Editor
crontab -e

# Füge diese Zeile ein (täglich um 2:00 Uhr)
0 2 * * * cd /home/kai1973i/dev/klArchiv && ./update_combined_csv.sh >> /tmp/klima_update.log 2>&1

# Oder wöchentlich (Sonntag um 23:00 Uhr)
0 23 * * 0 cd /home/kai1973i/dev/klArchiv && ./update_combined_csv.sh
```

### Szenario 3: Nach neuen DWD-Daten-Downloads
```bash
# Nachdem neue produkt_klima_tag_*.txt Dateien heruntergeladen wurden:
cd /home/kai1973i/dev/klArchiv
./update_combined_csv.sh

# Oder manuell mit Python
python3 update_combined_csv.py
```

### Szenario 4: Automatisch bei Git-Commits
```bash
# Bereits installiert nach: bash setup_auto_update.sh
# 
# Wenn Sie neue Daten hochladen und committen:
git add klarchiv_00691_daily_akt/produkt_klima_tag_*.txt
git commit -m "Update climate data"
# → Git Hook lädt automatisch die kombinierten CSVs nach!
```

---

## 📋 Checkliste für Setup

- [ ] `bash setup_auto_update.sh` ausgeführt?
- [ ] Python3 installiert? (`python3 --version`)
- [ ] pandas installiert? (`python3 -c "import pandas; print(pandas.__version__)"`)
- [ ] Scripts sind ausführbar? (`ls -la *.py *.sh | grep x`)
- [ ] Git-Hook installiert? (`ls .git/hooks/post-commit`)

---

## 🔍 Monitoring & Logs

### Logs für Cron-Jobs speichern:
```bash
# Append Ausgabe in Log-Datei
0 2 * * * cd /home/kai1973i/dev/klArchiv && ./update_combined_csv.sh >> /tmp/klima_update.log 2>&1

# Log anschauen
tail -f /tmp/klima_update.log
```

### Letzte Ausführung überprüfen:
```bash
# Modifizierungsdatum der CSVs
ls -lh produkt_klima_tag_combined*.csv

# Anzahl der Einträge
wc -l produkt_klima_tag_combined*.csv
```

---

## 📊 Ausgabedateien

Nach erfolgreicher Ausführung:

```
produkt_klima_tag_combined.csv
  ├─ 49.547 Zeilen
  ├─ 19 Spalten (englische Namen)
  ├─ Rohformat
  └─ ~6,8 MB

produkt_klima_tag_combined_klartext.csv
  ├─ 49.547 Zeilen
  ├─ 19 Spalten (deutsche Namen)
  ├─ Leicht lesbar
  └─ ~6,9 MB
```

---

## 🐛 Fehlerbehebung

### Problem: `pandas module not found`
```bash
pip3 install pandas
```

### Problem: `Permission denied` beim Ausführen
```bash
chmod +x *.py *.sh
```

### Problem: Alte CSV-Dateien
```bash
# CSVs werden überschrieben, aber überprüfe vorher:
git diff produkt_klima_tag_combined_klartext.csv | head -20
```

### Problem: Git-Hook funktioniert nicht
```bash
# Hook neu installieren
bash setup_auto_update.sh
```

---

## 📚 Weitere Ressourcen

- **Haupt-README:** `UPDATE_CSV_README.md`
- **Daten-Analyse:** `analyse_klima.py` (nutzt die generierten CSVs)
- **Dokumentation:** `README.md`

---

**Letzte Aktualisierung:** 29. Juni 2026
