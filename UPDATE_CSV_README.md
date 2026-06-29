# Automatische CSV-Aktualisierung für Klimadaten

Dieses Projekt enthält Scripts zur automatischen Aktualisierung der kombinierten Klimadaten-CSV-Dateien aus den Rohdaten des Deutschen Wetter Dienstes (DWD).

## Dateien

### 1. **update_combined_csv.py** (Hauptscript)
Das Python-Script, das die Aktualisierung durchführt.

**Funktionen:**
- Liest historische Daten aus `klarchiv_00691_daily_his/`
- Liest aktuelle Daten aus `klarchiv_00691_daily_akt/`
- Kombiniert beide Datensätze
- Entfernt Duplikate (neueste Version behält)
- Erzeugt zwei Ausgaben:
  - `produkt_klima_tag_combined.csv` (Rohformat mit englischen Spaltennamen)
  - `produkt_klima_tag_combined_klartext.csv` (Mit deutschen Spaltennamen)

**Spalten-Mapping (Rohformat → Klartext):**
```
STATIONS_ID           → Stations_ID
MESS_DATUM            → Messdatum
QN_3                  → Qualitaet_Windgust
FX                    → Max_Windgeschwindigkeit_kmh
FM                    → Mittel_Windgeschwindigkeit_kmh
QN_4                  → Qualitaet_Temperatur
RSK                   → Niederschlagsmenge_mm
RSKF                  → Niederschlagsform_Code
SDK                   → Sonnenscheindauer_h
SHK_TAG               → Tagesgang_Feuchte
NM                    → Bewoelkungsgrad_Oktas
VPM                   → Dampfdruck_hPa
PM                    → Luftdruck_hPa
TMK                   → Temperatur_Celsius
UPM                   → Relative_Feuchte_Prozent
TXK                   → Max_Temperatur_Celsius
TNK                   → Min_Temperatur_Celsius
TGK                   → Min_Bodentemperatur_Celsius
eor                   → Datensatz_Ende
```

### 2. **update_combined_csv.sh** (Wrapper-Script)
Bash-Wrapper für einfache Ausführung und Validierung von Abhängigkeiten.

## Installation

### Voraussetzungen
- Python 3.7+
- pandas

### Setup
```bash
# pandas installieren
pip3 install pandas

# Scripts ausführbar machen
chmod +x update_combined_csv.sh
chmod +x update_combined_csv.py
```

## Verwendung

### Manuelle Ausführung

**Mit Python:**
```bash
python3 update_combined_csv.py
```

**Mit dem Bash-Wrapper:**
```bash
./update_combined_csv.sh
```

### Automatisierte Ausführung (Cron)

**Täglich um 02:00 Uhr aktualisieren:**
```bash
0 2 * * * cd /home/kai1973i/dev/klArchiv && ./update_combined_csv.sh >> /tmp/klima_update.log 2>&1
```

**Wöchentlich montags um 23:00 Uhr:**
```bash
0 23 * * 1 cd /home/kai1973i/dev/klArchiv && ./update_combined_csv.sh >> /tmp/klima_update.log 2>&1
```

## Output

Das Script gibt Informationen über den Fortschritt aus:

```
======================================================================
🔄 Aktualisiere kombinierte Klimadaten-CSV
======================================================================

📁 Arbeitsverzeichnis: /home/kai1973i/dev/klArchiv
📁 Historische Daten  : /home/kai1973i/dev/klArchiv/klarchiv_00691_daily_his
📁 Aktuelle Daten     : /home/kai1973i/dev/klArchiv/klarchiv_00691_daily_akt

📖 Lese historische Daten: 1 Datei(en)
   ✓ produkt_klima_tag_18900101_20241231_00691.txt: 49002 Einträge
📄 Lese aktuelle Daten: 1 Datei(en)
   ✓ produkt_klima_tag_20241226_20260628_00691.txt: 550 Einträge

✓ Kombiniert: 49546 eindeutige Einträge nach Duplikatentfernung

💾 Speichere Rohformat: produkt_klima_tag_combined.csv
💾 Speichere Klartextformat: produkt_klima_tag_combined_klartext.csv

======================================================================
ZUSAMMENFASSUNG
======================================================================
Zeitraum     : 18900101 bis 20260628
Einträge     : 49,546
Spalten      : 19
Station(en)  : ['691']

✅ Aktualisierung erfolgreich abgeschlossen!
======================================================================
```

## Datenstruktur

### Eingabe-Verzeichnisse

```
klArchiv/
├── klarchiv_00691_daily_his/          # Historische Daten (1890-2024)
│   └── produkt_klima_tag_18900101_20241231_00691.txt
├── klarchiv_00691_daily_akt/          # Aktuelle Daten (2024-heute)
│   └── produkt_klima_tag_20241226_20260628_00691.txt
└── ...
```

### Ausgabe-Dateien

```
klArchiv/
├── produkt_klima_tag_combined.csv           # Rohformat (englisch)
├── produkt_klima_tag_combined_klartext.csv  # Klartext (deutsch)
└── ...
```

## Besonderheiten

### Duplikatbehandlung
- Falls Daten für den gleichen Tag in mehreren Dateien vorhanden sind, behält der Script die **neueste** Version
- Dies ist wichtig, da aktuelle Daten frühere Werte korrigieren können

### Datenformat
- **Trennzeichen:** Semikolon (`;`)
- **Datumsformat:** YYYYMMDD (z.B. 20260628)
- **Dezimaltrennzeichen:** Punkt (`.`)
- **Fehlwert-Markierung:** `-999` (wird von `analyse_klima.py` in NaN konvertiert)

### Qualität
- Die Spalten `QN_3` und `QN_4` enthalten Qualitätskennzeichen
- `-999` ist ein allgemeiner Fehlwert-Marker

## Fehlerbehandlung

Das Script behandelt verschiedene Fehler:
- Fehlende Verzeichnisse werden gemeldet
- Unlesbare Dateien werden übersprungen (mit Warnung)
- Leere Dataframes werden erkannt

## Integration mit analyse_klima.py

Die generierten CSV-Dateien werden von `analyse_klima.py` verwendet:

```python
DATA_FILE = Path(__file__).parent / "produkt_klima_tag_combined_klartext.csv"
```

Aktualisiere die kombinierte CSV vor dem Ausführen von `analyse_klima.py`, um mit den neuesten Daten zu arbeiten.

## Lizenz

Klimadaten: Deutscher Wetterdienst (DWD)
Scripts: Lokal

## Änderungen

- **2026-06-29:** Erstes Release
  - Automatische CSV-Kombinierung aus Rohdaten
  - Deutsche Spaltennamen für Klartext-Version
  - Bash und Python Scripts

---

**Letzte Aktualisierung:** 29. Juni 2026
