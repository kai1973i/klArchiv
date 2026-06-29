#!/usr/bin/env python3
"""
Automatische Aktualisierung von produkt_klima_tag_combined_klartext.csv
Kombiniert Daten aus historischen (_his) und aktuellen (_akt) Rohdaten
und erstellt eine unified CSV mit deutschen Spaltennamen.

Verwendung:
    python3 update_combined_csv.py
    
Ausgabe:
    - produkt_klima_tag_combined.csv (Rohformat)
    - produkt_klima_tag_combined_klartext.csv (mit deutschen Spaltennamen)
"""

import pandas as pd
import glob
from pathlib import Path
from typing import Tuple
import sys

# ============================================================================
# Konfiguration
# ============================================================================

BASE_DIR = Path(__file__).parent
HIS_DIR = BASE_DIR / "klarchiv_00691_daily_his"
AKT_DIR = BASE_DIR / "klarchiv_00691_daily_akt"

OUTPUT_COMBINED_RAW = BASE_DIR / "produkt_klima_tag_combined.csv"
OUTPUT_COMBINED_KLARTEXT = BASE_DIR / "produkt_klima_tag_combined_klartext.csv"

# Mapping: Original-Spaltennamen → Deutsche Klartextnamen
SPALTEN_MAPPING = {
    "STATIONS_ID": "Stations_ID",
    "MESS_DATUM": "Messdatum",
    "QN_3": "Qualitaet_Windgust",
    "FX": "Max_Windgeschwindigkeit_kmh",
    "FM": "Mittel_Windgeschwindigkeit_kmh",
    "QN_4": "Qualitaet_Temperatur",
    "RSK": "Niederschlagsmenge_mm",
    "RSKF": "Niederschlagsform_Code",
    "SDK": "Sonnenscheindauer_h",
    "SHK_TAG": "Tagesgang_Feuchte",
    "NM": "Bewoelkungsgrad_Oktas",
    "VPM": "Dampfdruck_hPa",
    "PM": "Luftdruck_hPa",
    "TMK": "Temperatur_Celsius",
    "UPM": "Relative_Feuchte_Prozent",
    "TXK": "Max_Temperatur_Celsius",
    "TNK": "Min_Temperatur_Celsius",
    "TGK": "Min_Bodentemperatur_Celsius",
    "eor": "Datensatz_Ende",
}

# ============================================================================
# Funktionen
# ============================================================================

def find_data_files(directory: Path) -> list:
    """Findet alle produkt_klima_tag*.txt Dateien in einem Verzeichnis."""
    pattern = directory / "produkt_klima_tag_*.txt"
    files = glob.glob(str(pattern))
    return sorted(files)


def read_raw_file(filepath: Path) -> pd.DataFrame:
    """Liest eine Rohdatei mit Semikolon-Trennzeichen."""
    try:
        df = pd.read_csv(
            filepath,
            sep=";",
            skipinitialspace=True,
            dtype=str  # Alle Spalten als String lesen, um Formatierung zu bewahren
        )
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        print(f"⚠ Fehler beim Lesen von {filepath}: {e}", file=sys.stderr)
        return pd.DataFrame()


def combine_data_files(his_dir: Path, akt_dir: Path) -> pd.DataFrame:
    """
    Kombiniert historische und aktuelle Daten.
    - Historische Daten: Kompletter Datensatz (1890 bis gestern)
    - Aktuelle Daten: Neue/aktualisierte Einträge
    
    Duplifikate werden entfernt (neueste Version behält).
    """
    dfs = []
    
    # Historische Daten
    his_files = find_data_files(his_dir)
    if his_files:
        print(f"📖 Lese historische Daten: {len(his_files)} Datei(en)")
        for fpath in his_files:
            df = read_raw_file(Path(fpath))
            if not df.empty:
                dfs.append(df)
                print(f"   ✓ {Path(fpath).name}: {len(df)} Einträge")
    else:
        print("⚠ Keine historischen Dateien gefunden", file=sys.stderr)
    
    # Aktuelle Daten (überschreiben ältere Einträge)
    akt_files = find_data_files(akt_dir)
    if akt_files:
        print(f"📄 Lese aktuelle Daten: {len(akt_files)} Datei(en)")
        for fpath in akt_files:
            df = read_raw_file(Path(fpath))
            if not df.empty:
                dfs.append(df)
                print(f"   ✓ {Path(fpath).name}: {len(df)} Einträge")
    else:
        print("⚠ Keine aktuellen Dateien gefunden", file=sys.stderr)
    
    if not dfs:
        print("❌ Keine Daten gefunden!", file=sys.stderr)
        return pd.DataFrame()
    
    # Kombinieren
    combined = pd.concat(dfs, ignore_index=True)
    
    # Duplikate entfernen (neueste Version behält)
    # Sortiere nach MESS_DATUM und entferne alle außer dem letzten Datensatz pro Tag
    combined = combined.sort_values("MESS_DATUM", ascending=False)
    combined = combined.drop_duplicates(subset=["STATIONS_ID", "MESS_DATUM"], keep="first")
    combined = combined.sort_values("MESS_DATUM", ascending=True)
    
    print(f"\n✓ Kombiniert: {len(combined)} eindeutige Einträge nach Duplikatentfernung")
    
    return combined


def apply_column_mapping(df: pd.DataFrame) -> pd.DataFrame:
    """Wendet das Spalten-Mapping (Englisch → Deutsch) an."""
    # Nur Spalten umbenennen, die im Mapping definiert sind
    available_cols = {k: v for k, v in SPALTEN_MAPPING.items() if k in df.columns}
    
    if not available_cols:
        print("⚠ Kein Spalten-Mapping möglich (keine bekannten Spalten gefunden)", file=sys.stderr)
        return df
    
    df = df.rename(columns=available_cols)
    print(f"✓ {len(available_cols)} Spalten umbenannt (Englisch → Deutsch)")
    
    return df


def save_combined_files(df_raw: pd.DataFrame, output_raw: Path, output_klartext: Path) -> None:
    """Speichert beide Versionen der kombinierten CSV."""
    
    # Version 1: Rohformat (mit englischen Spaltennamen, unverändert)
    print(f"\n💾 Speichere Rohformat: {output_raw.name}")
    df_raw.to_csv(output_raw, sep=";", index=False)
    print(f"   ✓ {len(df_raw)} Einträge, {len(df_raw.columns)} Spalten")
    
    # Version 2: Klartext (mit deutschen Spaltennamen)
    print(f"💾 Speichere Klartextformat: {output_klartext.name}")
    df_klartext = apply_column_mapping(df_raw.copy())
    df_klartext.to_csv(output_klartext, sep=";", index=False)
    print(f"   ✓ {len(df_klartext)} Einträge, {len(df_klartext.columns)} Spalten")


def print_summary(df: pd.DataFrame) -> None:
    """Gibt eine Zusammenfassung der Daten aus."""
    if df.empty:
        print("⚠ Keine Daten zum Zusammenfassen", file=sys.stderr)
        return
    
    print("\n" + "=" * 70)
    print("ZUSAMMENFASSUNG")
    print("=" * 70)
    
    # Datum extrahieren
    df_copy = df.copy()
    df_copy["MESS_DATUM"] = df_copy["MESS_DATUM"].astype(str)
    
    min_date = df_copy["MESS_DATUM"].min()
    max_date = df_copy["MESS_DATUM"].max()
    
    print(f"Zeitraum     : {min_date} bis {max_date}")
    print(f"Einträge     : {len(df):,}")
    print(f"Spalten      : {len(df.columns)}")
    print(f"Station(en)  : {df['STATIONS_ID'].unique().tolist()}")
    print()


def main():
    """Hauptfunktion."""
    print("\n" + "=" * 70)
    print("🔄 Aktualisiere kombinierte Klimadaten-CSV")
    print("=" * 70 + "\n")
    
    # Überprüfe Verzeichnisse
    if not HIS_DIR.exists():
        print(f"❌ Historisches Verzeichnis nicht gefunden: {HIS_DIR}", file=sys.stderr)
        return 1
    
    if not AKT_DIR.exists():
        print(f"❌ Aktuelles Verzeichnis nicht gefunden: {AKT_DIR}", file=sys.stderr)
        return 1
    
    print(f"📁 Arbeitsverzeichnis: {BASE_DIR}")
    print(f"📁 Historische Daten  : {HIS_DIR}")
    print(f"📁 Aktuelle Daten     : {AKT_DIR}\n")
    
    # Lade und kombiniere Daten
    df_combined = combine_data_files(HIS_DIR, AKT_DIR)
    
    if df_combined.empty:
        print("\n❌ Fehler: Keine Daten verfügbar!", file=sys.stderr)
        return 1
    
    # Speichere beide Versionen
    save_combined_files(df_combined, OUTPUT_COMBINED_RAW, OUTPUT_COMBINED_KLARTEXT)
    
    # Zusammenfassung
    print_summary(df_combined)
    
    print("=" * 70)
    print("✅ Aktualisierung erfolgreich abgeschlossen!")
    print("=" * 70 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
