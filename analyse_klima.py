"""
Klimadaten-Analyse – Station Bremen (ID 691)
Zeitraum: 1890–2026 (Tageswerte)
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import numpy as np
from pathlib import Path

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------
DATA_FILE = Path(__file__).parent / "produkt_klima_tag_combined_klartext.csv"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

FEHLWERT = -999

# ---------------------------------------------------------------------------
# Laden & Bereinigen
# ---------------------------------------------------------------------------
def lade_daten(pfad: Path) -> pd.DataFrame:
    df = pd.read_csv(pfad, sep=";", skipinitialspace=True)
    df.columns = df.columns.str.strip()

    # Messdatum als datetime
    df["Datum"] = pd.to_datetime(df["Messdatum"].astype(str), format="%Y%m%d")
    df = df.set_index("Datum").sort_index()

    # Fehlwerte → NaN
    numerische = df.select_dtypes(include="number").columns
    df[numerische] = df[numerische].replace(FEHLWERT, np.nan)

    return df


# ---------------------------------------------------------------------------
# 1. Datenübersicht & Fehlwert-Quantifizierung
# ---------------------------------------------------------------------------
def uebersicht(df: pd.DataFrame):
    print("=" * 60)
    print("DATENÜBERSICHT")
    print("=" * 60)
    print(f"Zeitraum : {df.index.min().date()} – {df.index.max().date()}")
    print(f"Datensätze: {len(df):,}")
    print()

    messwert_spalten = [
        "Max_Windgeschwindigkeit_kmh", "Mittel_Windgeschwindigkeit_kmh",
        "Niederschlagsmenge_mm", "Sonnenscheindauer_h",
        "Bewoelkungsgrad_Oktas", "Dampfdruck_hPa", "Luftdruck_hPa",
        "Temperatur_Celsius", "Relative_Feuchte_Prozent",
        "Max_Temperatur_Celsius", "Min_Temperatur_Celsius",
        "Min_Bodentemperatur_Celsius",
    ]

    print(f"{'Spalte':<38} {'Fehlwerte':>10} {'%':>7}  {'Min':>8}  {'Max':>8}  {'Mittel':>8}")
    print("-" * 85)
    for col in messwert_spalten:
        if col not in df.columns:
            continue
        n_nan = df[col].isna().sum()
        pct = 100 * n_nan / len(df)
        s = df[col].dropna()
        print(f"{col:<38} {n_nan:>10,} {pct:>6.1f}%  {s.min():>8.2f}  {s.max():>8.2f}  {s.mean():>8.2f}")

    print()

    # Fehlwert-Verlauf als Heatmap (Jahrzehnte)
    fig, ax = plt.subplots(figsize=(14, 5))
    df["Jahrzehnt"] = (df.index.year // 10) * 10
    fehlwert_rate = (
        df.groupby("Jahrzehnt")[messwert_spalten]
        .apply(lambda g: g.isna().mean() * 100)
    )
    im = ax.imshow(fehlwert_rate.T, aspect="auto", cmap="RdYlGn_r", vmin=0, vmax=100)
    ax.set_xticks(range(len(fehlwert_rate)))
    ax.set_xticklabels(fehlwert_rate.index, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(messwert_spalten)))
    ax.set_yticklabels([c.replace("_", " ") for c in messwert_spalten], fontsize=8)
    ax.set_title("Fehlwert-Rate pro Jahrzehnt (%)")
    plt.colorbar(im, ax=ax, label="%")
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "01_fehlwert_heatmap.png", dpi=150)
    plt.close(fig)
    print(f"→ Gespeichert: 01_fehlwert_heatmap.png")


# ---------------------------------------------------------------------------
# 2. Temperaturtrend
# ---------------------------------------------------------------------------
def temperaturtrend(df: pd.DataFrame):
    col = "Temperatur_Celsius"
    jahres = df[col].resample("YE").mean().dropna()
    monatsmittel = df[col].groupby(df.index.month).mean()

    fig, axes = plt.subplots(2, 1, figsize=(14, 9))

    # Jahrestrend
    ax = axes[0]
    ax.plot(jahres.index, jahres.values, color="steelblue", alpha=0.7, linewidth=1, label="Jahresmittel")
    # 10-Jahres-Glättung
    glaett = jahres.rolling(10, center=True).mean()
    ax.plot(glaett.index, glaett.values, color="red", linewidth=2.5, label="10-J.-Glättung")
    # Lineare Regression
    x_num = np.arange(len(jahres))
    m, b = np.polyfit(x_num, jahres.values, 1)
    trend_line = m * x_num + b
    ax.plot(jahres.index, trend_line, "--", color="darkred", linewidth=1.5,
            label=f"Trend: {m * 10:.2f} °C/Jahrzehnt")
    ax.set_title("Jahresmittel der Lufttemperatur – Bremen (1890–2026)")
    ax.set_ylabel("°C")
    ax.legend()
    ax.grid(alpha=0.3)

    # Monatsmittel
    ax2 = axes[1]
    monate = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
              "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
    bars = ax2.bar(monate, monatsmittel.values, color="steelblue", edgecolor="white")
    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.set_title("Klimatologisches Monatsmittel der Temperatur (gesamter Zeitraum)")
    ax2.set_ylabel("°C")
    ax2.grid(axis="y", alpha=0.3)
    for bar, val in zip(bars, monatsmittel.values):
        ax2.text(bar.get_x() + bar.get_width() / 2, val + 0.15, f"{val:.1f}",
                 ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "02_temperaturtrend.png", dpi=150)
    plt.close(fig)
    print(f"→ Gespeichert: 02_temperaturtrend.png")


# ---------------------------------------------------------------------------
# 3. Niederschlagsverteilung
# ---------------------------------------------------------------------------
def niederschlag(df: pd.DataFrame):
    col = "Niederschlagsmenge_mm"
    jahres = df[col].resample("YE").sum().dropna()
    monatssumme = df[col].groupby(df.index.month).mean() * 30  # mittl. Monatssumme

    fig, axes = plt.subplots(2, 1, figsize=(14, 9))

    ax = axes[0]
    ax.bar(jahres.index, jahres.values, width=300, color="royalblue", alpha=0.7)
    ax.plot(jahres.rolling(10, center=True).mean(), color="darkblue", linewidth=2)
    ax.set_title("Jährliche Niederschlagssumme – Bremen")
    ax.set_ylabel("mm")
    ax.grid(axis="y", alpha=0.3)

    ax2 = axes[1]
    monate = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
              "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
    ax2.bar(monate, monatssumme.values, color="royalblue", edgecolor="white")
    ax2.set_title("Mittlere monatliche Niederschlagssumme (gesamter Zeitraum)")
    ax2.set_ylabel("mm")
    ax2.grid(axis="y", alpha=0.3)
    for i, val in enumerate(monatssumme.values):
        ax2.text(i, val + 1, f"{val:.0f}", ha="center", fontsize=8)

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "03_niederschlag.png", dpi=150)
    plt.close(fig)
    print(f"→ Gespeichert: 03_niederschlag.png")


# ---------------------------------------------------------------------------
# 4. Sonnenscheindauer-Trend
# ---------------------------------------------------------------------------
def sonnenschein(df: pd.DataFrame):
    col = "Sonnenscheindauer_h"
    jahres = df[col].resample("YE").sum().dropna()

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.bar(jahres.index, jahres.values, width=300, color="gold", edgecolor="orange", alpha=0.8)
    ax.plot(jahres.rolling(10, center=True).mean(), color="darkorange", linewidth=2.5, label="10-J.-Glättung")
    ax.set_title("Jährliche Sonnenscheinstunden – Bremen")
    ax.set_ylabel("Stunden/Jahr")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "04_sonnenschein.png", dpi=150)
    plt.close(fig)
    print(f"→ Gespeichert: 04_sonnenschein.png")


# ---------------------------------------------------------------------------
# 5. Extremwerte
# ---------------------------------------------------------------------------
def extremwerte(df: pd.DataFrame):
    print()
    print("=" * 60)
    print("EXTREMWERTE")
    print("=" * 60)

    def zeige_extrema(col, label, n=10):
        s = df[col].dropna()
        if s.empty:
            return
        top_max = s.nlargest(n)
        top_min = s.nsmallest(n)
        print(f"\n{label} – Top {n} höchste Werte:")
        for datum, wert in top_max.items():
            print(f"  {datum.date()}  {wert:+.1f}")
        print(f"\n{label} – Top {n} niedrigste Werte:")
        for datum, wert in top_min.items():
            print(f"  {datum.date()}  {wert:+.1f}")

    zeige_extrema("Max_Temperatur_Celsius", "Tagesmaximum Temperatur")
    zeige_extrema("Min_Temperatur_Celsius", "Tagesminimum Temperatur")
    zeige_extrema("Niederschlagsmenge_mm", "Tagesniederschlag")
    zeige_extrema("Max_Windgeschwindigkeit_kmh", "Max. Windgeschwindigkeit")


# ---------------------------------------------------------------------------
# 6. Saisonale Muster (Boxplots je Monat)
# ---------------------------------------------------------------------------
def saisonale_boxplots(df: pd.DataFrame):
    spalten = [
        ("Temperatur_Celsius", "Lufttemperatur (°C)"),
        ("Niederschlagsmenge_mm", "Niederschlag (mm/Tag)"),
        ("Sonnenscheindauer_h", "Sonnenscheindauer (h/Tag)"),
    ]
    monate_kurz = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
                   "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]

    fig, axes = plt.subplots(len(spalten), 1, figsize=(14, 14))

    for ax, (col, label) in zip(axes, spalten):
        s = df[col].dropna()
        daten_pro_monat = [s[s.index.month == m].values for m in range(1, 13)]
        bp = ax.boxplot(daten_pro_monat, labels=monate_kurz, patch_artist=True,
                        flierprops={"marker": ".", "markersize": 2, "alpha": 0.3},
                        medianprops={"color": "red", "linewidth": 2})
        colors = plt.cm.coolwarm(np.linspace(0, 1, 12))
        for patch, color in zip(bp["boxes"], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        ax.set_title(f"Saisonale Verteilung – {label}")
        ax.set_ylabel(label)
        ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "05_saisonale_boxplots.png", dpi=150)
    plt.close(fig)
    print(f"→ Gespeichert: 05_saisonale_boxplots.png")


# ---------------------------------------------------------------------------
# 7. Korrelationsmatrix
# ---------------------------------------------------------------------------
def korrelation(df: pd.DataFrame):
    spalten = [
        "Temperatur_Celsius", "Max_Temperatur_Celsius", "Min_Temperatur_Celsius",
        "Niederschlagsmenge_mm", "Sonnenscheindauer_h", "Bewoelkungsgrad_Oktas",
        "Relative_Feuchte_Prozent", "Luftdruck_hPa", "Dampfdruck_hPa",
        "Max_Windgeschwindigkeit_kmh",
    ]
    vorh = [c for c in spalten if c in df.columns]
    corr = df[vorh].corr()

    labels = [c.replace("_", "\n") for c in vorh]
    fig, ax = plt.subplots(figsize=(12, 10))
    im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
    plt.colorbar(im, ax=ax, label="Pearson r")
    ax.set_xticks(range(len(vorh)))
    ax.set_yticks(range(len(vorh)))
    ax.set_xticklabels(labels, fontsize=7, rotation=45, ha="right")
    ax.set_yticklabels(labels, fontsize=7)
    for i in range(len(vorh)):
        for j in range(len(vorh)):
            val = corr.iloc[i, j]
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=6, color="black" if abs(val) < 0.7 else "white")
    ax.set_title("Korrelationsmatrix der Klimamessgrößen – Bremen")
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "06_korrelation.png", dpi=150)
    plt.close(fig)
    print(f"→ Gespeichert: 06_korrelation.png")


# ---------------------------------------------------------------------------
# 7b. Hitzeextreme pro Jahr
# ---------------------------------------------------------------------------
def hitzeextreme_pro_jahr(df: pd.DataFrame):
    """
    DWD-Definitionen:
      Sommertag   : Tmax >= 25 °C
      Heißer Tag  : Tmax >= 30 °C
      Tropennacht : Tmin >= 20 °C
      Eistag      : Tmax <  0 °C  (als Kältegegenstück)
      Frosttag    : Tmin <  0 °C
    """
    tmax = df["Max_Temperatur_Celsius"].dropna()
    tmin = df["Min_Temperatur_Celsius"].dropna()

    def jahres_count(series, bedingung_fn):
        s = series[bedingung_fn(series)]
        cnt = s.resample("YE").count()
        cnt.index = cnt.index.year
        return cnt

    kategorien = {
        "Sommertag (Tmax ≥ 25 °C)":  (tmax, lambda s: s >= 25, "tomato"),
        "Heißer Tag (Tmax ≥ 30 °C)": (tmax, lambda s: s >= 30, "firebrick"),
        "Tropennacht (Tmin ≥ 20 °C)": (tmin, lambda s: s >= 20, "darkorange"),
        "Frosttag (Tmin < 0 °C)":     (tmin, lambda s: s < 0,  "steelblue"),
        "Eistag (Tmax < 0 °C)":       (tmax, lambda s: s < 0,  "navy"),
    }

    daten = {label: jahres_count(series, fn)
             for label, (series, fn, _) in kategorien.items()}
    jahres_df = pd.DataFrame(daten).fillna(0).astype(int)

    # Konsolausgabe
    print()
    print("=" * 75)
    print("HITZEEXTREME PRO JAHR (Anzahl Tage je Kategorie)")
    print("=" * 75)
    header = f"{'Jahr':>6}" + "".join(f"  {k[:12]:>12}" for k in kategorien)
    print(header)
    print("-" * len(header))
    for jahr, row in jahres_df.iterrows():
        zeile = f"{jahr:>6}" + "".join(f"  {row[k]:>12}" for k in kategorien)
        print(zeile)
    print()
    print("Mittelwerte pro Jahr:")
    for label in kategorien:
        print(f"  {label}: {jahres_df[label].mean():.1f} Tage/Jahr")

    # Grafik
    n = len(kategorien)
    fig, axes = plt.subplots(n, 1, figsize=(14, 4 * n), sharex=True)

    for ax, (label, (_, _, farbe)) in zip(axes, kategorien.items()):
        y = jahres_df[label]
        ax.bar(y.index, y.values, color=farbe, alpha=0.75, width=0.8)
        glaett = y.rolling(10, center=True).mean()
        ax.plot(glaett.index, glaett.values, color="black", linewidth=2,
                label="10-J.-Glättung")
        mittel = y.mean()
        ax.axhline(mittel, color="gold", linewidth=1.5, linestyle="--",
                   label=f"Mittel: {mittel:.1f} Tage/Jahr")
        ax.set_ylabel("Tage/Jahr")
        ax.set_title(label)
        ax.legend(fontsize=8)
        ax.grid(axis="y", alpha=0.3)

    axes[-1].set_xlabel("Jahr")
    plt.suptitle("Hitze- und Kälteextreme pro Jahr – Bremen (1890–2026)",
                 fontsize=13, y=1.005)
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "07b_hitzeextreme_pro_jahr.png", dpi=150)
    plt.close(fig)
    print(f"→ Gespeichert: 07b_hitzeextreme_pro_jahr.png")

    return jahres_df


# ---------------------------------------------------------------------------
# 8. Niederschlag-Extremwerte pro Jahr
# ---------------------------------------------------------------------------
def niederschlag_extremwerte_pro_jahr(df: pd.DataFrame):
    col = "Niederschlagsmenge_mm"
    s = df[col].dropna()

    # Schwellwerte: DWD-Definitionen für Starkregen
    schwellen = {
        "≥10 mm": 10,
        "≥20 mm": 20,
        "≥30 mm": 30,
        "≥50 mm": 50,
    }

    # Anzahl Tage pro Jahr je Schwelle
    ergebnisse = {}
    for label, grenzwert in schwellen.items():
        jahres_count = s[s >= grenzwert].resample("YE").count()
        jahres_count.index = jahres_count.index.year
        ergebnisse[label] = jahres_count

    jahres_df = pd.DataFrame(ergebnisse).fillna(0).astype(int)

    # Konsolausgabe
    print()
    print("=" * 70)
    print("NIEDERSCHLAG-EXTREMWERTE PRO JAHR (Anzahl Tage je Schwellwert)")
    print("=" * 70)
    print(f"{'Jahr':>6}  {'≥10 mm':>8}  {'≥20 mm':>8}  {'≥30 mm':>8}  {'≥50 mm':>8}")
    print("-" * 50)
    for jahr, row in jahres_df.iterrows():
        print(f"{jahr:>6}  {row['≥10 mm']:>8}  {row['≥20 mm']:>8}  {row['≥30 mm']:>8}  {row['≥50 mm']:>8}")

    print()
    print("Mittelwerte pro Jahr:")
    for label in schwellen:
        print(f"  {label}: {jahres_df[label].mean():.1f} Tage/Jahr")

    # Grafik
    fig, axes = plt.subplots(4, 1, figsize=(14, 16), sharex=True)
    farben = ["steelblue", "royalblue", "darkblue", "navy"]

    for ax, (label, grenzwert), farbe in zip(axes, schwellen.items(), farben):
        y = jahres_df[label]
        ax.bar(y.index, y.values, color=farbe, alpha=0.7, width=0.8)
        glaett = y.rolling(10, center=True).mean()
        ax.plot(glaett.index, glaett.values, color="red", linewidth=2, label="10-J.-Glättung")
        mittel = y.mean()
        ax.axhline(mittel, color="orange", linewidth=1.5, linestyle="--",
                   label=f"Mittel: {mittel:.1f} Tage/Jahr")
        ax.set_ylabel("Tage/Jahr")
        ax.set_title(f"Anzahl Tage mit Tagesniederschlag {label}")
        ax.legend(fontsize=8)
        ax.grid(axis="y", alpha=0.3)

    axes[-1].set_xlabel("Jahr")
    plt.suptitle("Niederschlag-Extremwerte pro Jahr – Bremen (1890–2026)",
                 fontsize=13, y=1.01)
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "07_niederschlag_extremwerte_pro_jahr.png", dpi=150)
    plt.close(fig)
    print(f"→ Gespeichert: 07_niederschlag_extremwerte_pro_jahr.png")

    return jahres_df


# ---------------------------------------------------------------------------
# 9. Klimanormalperioden-Vergleich (WMO)
# ---------------------------------------------------------------------------
def klimanormalperioden(df: pd.DataFrame):
    """
    Vergleicht die drei WMO-Klimanormalperioden:
      1961–1990 (klassische Referenz)
      1991–2020 (aktuelle WMO-Normalperiode)
      2001–2026 (neueste 25-Jahr-Spanne, laufend)
    Kenngrößen: Temperatur, Niederschlag, Sonnenschein – je Monat
    """
    perioden = {
        "1961–1990": (1961, 1990),
        "1991–2020": (1991, 2020),
        "2001–2026": (2001, 2026),
    }
    farben = {"1961–1990": "steelblue", "1991–2020": "darkorange", "2001–2026": "firebrick"}
    monate_kurz = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
                   "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]

    kenngroessen = [
        ("Temperatur_Celsius",      "Monatsmittel Temperatur",       "°C",        "mean"),
        ("Niederschlagsmenge_mm",   "Monatliche Niederschlagssumme", "mm",        "sum"),
        ("Sonnenscheindauer_h",     "Monatliche Sonnenscheinstunden","h",         "sum"),
    ]

    # ---------- Konsolausgabe ----------
    print()
    print("=" * 75)
    print("KLIMANORMALPERIODEN-VERGLEICH (WMO)")
    print("=" * 75)

    for col, titel, einheit, aggr in kenngroessen:
        if col not in df.columns:
            continue
        print(f"\n{titel} ({einheit}):")
        header = f"  {'Monat':>5}" + "".join(f"  {p:>12}" for p in perioden)
        print(header)
        print("  " + "-" * (len(header) - 2))
        monats_tabelle = {}
        for p_label, (j_von, j_bis) in perioden.items():
            subset = df[col][(df.index.year >= j_von) & (df.index.year <= j_bis)].dropna()
            if aggr == "mean":
                monats_werte = subset.groupby(subset.index.month).mean()
            else:
                # Tagessumme → Jahressumme → Monatsmittel der Jahressummen
                monats_werte = subset.groupby(subset.index.month).sum() / (j_bis - j_von + 1)
            monats_tabelle[p_label] = monats_werte
        for m in range(1, 13):
            zeile = f"  {monate_kurz[m-1]:>5}"
            for p_label in perioden:
                val = monats_tabelle[p_label].get(m, float("nan"))
                zeile += f"  {val:>12.1f}"
            print(zeile)

    # ---------- Grafik ----------
    n = len(kenngroessen)
    fig, axes = plt.subplots(n, 1, figsize=(13, 5 * n))
    x = np.arange(12)
    breite = 0.25

    for ax, (col, titel, einheit, aggr) in zip(axes, kenngroessen):
        if col not in df.columns:
            continue
        for i, (p_label, (j_von, j_bis)) in enumerate(perioden.items()):
            subset = df[col][(df.index.year >= j_von) & (df.index.year <= j_bis)].dropna()
            if aggr == "mean":
                werte = [subset[subset.index.month == m].mean() for m in range(1, 13)]
            else:
                werte = [subset[subset.index.month == m].sum() / (j_bis - j_von + 1)
                         for m in range(1, 13)]
            offset = (i - 1) * breite
            ax.bar(x + offset, werte, width=breite, label=p_label,
                   color=farben[p_label], alpha=0.85, edgecolor="white")

        ax.set_xticks(x)
        ax.set_xticklabels(monate_kurz)
        ax.set_ylabel(einheit)
        ax.set_title(titel)
        ax.legend(title="Periode")
        ax.grid(axis="y", alpha=0.3)

    plt.suptitle("Klimanormalperioden-Vergleich – Bremen\n(WMO: 1961–1990 | 1991–2020 | 2001–2026)",
                 fontsize=13)
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "08_klimanormalperioden.png", dpi=150)
    plt.close(fig)
    print(f"\n→ Gespeichert: 08_klimanormalperioden.png")


# ---------------------------------------------------------------------------
# 10. Temperaturanomalie & Warming Stripes
# ---------------------------------------------------------------------------
def temperaturanomalie(df: pd.DataFrame):
    """
    Referenzzeitraum: 1961–1990 (WMO-Standardnormal)
    Darstellung:
      - Balkendiagramm der Jahresanomalien mit 10-J.-Glättung
      - Klassische „Warming Stripes" (Ed Hawkins-Stil)
    """
    col = "Temperatur_Celsius"
    jahres = df[col].resample("YE").mean().dropna()
    jahres.index = jahres.index.year

    # Referenzmittel 1961–1990
    referenz_mittel = jahres[(jahres.index >= 1961) & (jahres.index <= 1990)].mean()
    anomalie = jahres - referenz_mittel

    # ---------- Grafik 1: Anomalie-Balken ----------
    fig, ax = plt.subplots(figsize=(16, 5))
    farben = ["#d73027" if v >= 0 else "#4575b4" for v in anomalie.values]
    ax.bar(anomalie.index, anomalie.values, color=farben, width=0.9, alpha=0.85)
    glaett = anomalie.rolling(10, center=True).mean()
    ax.plot(glaett.index, glaett.values, color="black", linewidth=2.5,
            label="10-J.-Glättung")
    ax.axhline(0, color="gray", linewidth=0.8, linestyle="--")
    ax.set_ylabel("Temperaturanomalie (°C)")
    ax.set_title(
        f"Jahrestemperatur-Anomalie Bremen – Referenz: Ø 1961–1990 = {referenz_mittel:.2f} °C"
    )
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "09a_temperaturanomalie.png", dpi=150)
    plt.close(fig)
    print(f"→ Gespeichert: 09a_temperaturanomalie.png")

    # ---------- Grafik 2: Warming Stripes ----------
    vmax = max(abs(anomalie.min()), abs(anomalie.max()))
    norm = plt.Normalize(-vmax, vmax)
    cmap = plt.get_cmap("RdBu_r")

    fig, ax = plt.subplots(figsize=(16, 3))
    ax.set_axis_off()
    for i, (jahr, val) in enumerate(anomalie.items()):
        ax.add_patch(plt.Rectangle(
            (i, 0), 1, 1,
            color=cmap(norm(val)),
            linewidth=0,
        ))
    # Jahres-Ticks alle 10 Jahre
    jahre_liste = list(anomalie.index)
    tick_pos = [i for i, j in enumerate(jahre_liste) if j % 10 == 0]
    tick_lab = [str(jahre_liste[i]) for i in tick_pos]
    ax.set_xlim(0, len(jahre_liste))
    ax.set_ylim(0, 1)
    ax2 = ax.twiny()
    ax2.set_xlim(0, len(jahre_liste))
    ax2.set_xticks([p + 0.5 for p in tick_pos])
    ax2.set_xticklabels(tick_lab, fontsize=9)
    ax2.tick_params(length=4)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax2, orientation="horizontal", pad=0.25,
                        fraction=0.03, aspect=60)
    cbar.set_label("Anomalie (°C) gegenüber 1961–1990")

    fig.suptitle("Warming Stripes – Bremen 1890–2026", fontsize=13, y=1.12)
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "09b_warming_stripes.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"→ Gespeichert: 09b_warming_stripes.png")

    # ---------- Konsolausgabe ----------
    print()
    print("=" * 55)
    print("TEMPERATURANOMALIEN (Referenz Ø 1961–1990)")
    print("=" * 55)
    print(f"Referenzmittel:  {referenz_mittel:.2f} °C")
    print(f"Stärkste Kälte:  {anomalie.min():.2f} °C  ({anomalie.idxmin()})")
    print(f"Stärkste Wärme:  {anomalie.max():.2f} °C  ({anomalie.idxmax()})")
    print(f"Anomalie 2020er: {anomalie[anomalie.index >= 2020].mean():.2f} °C (Ø 2020–heute)")
    print(f"Anomalie 1890er: {anomalie[anomalie.index < 1900].mean():.2f} °C (Ø 1890–1899)")


# ---------------------------------------------------------------------------
# 12. Saisonale Trends (Erwärmt sich der Sommer stärker als der Winter?)
# ---------------------------------------------------------------------------
def saisonale_trends(df: pd.DataFrame):
    """
    Jahresmittel der Temperatur je meteorologischer Jahreszeit:
      Frühling: Mär–Mai | Sommer: Jun–Aug | Herbst: Sep–Nov | Winter: Dez–Feb
    Dazu: lineare Trendlinie und Trendstärke in °C/Jahrzehnt.
    """
    col = "Temperatur_Celsius"

    jahreszeiten = {
        "Frühling (Mär–Mai)": [3, 4, 5],
        "Sommer (Jun–Aug)":   [6, 7, 8],
        "Herbst (Sep–Nov)":   [9, 10, 11],
        "Winter (Dez–Feb)":   [12, 1, 2],
    }
    farben = {
        "Frühling (Mär–Mai)": "forestgreen",
        "Sommer (Jun–Aug)":   "firebrick",
        "Herbst (Sep–Nov)":   "darkorange",
        "Winter (Dez–Feb)":   "steelblue",
    }

    def jahres_mittel(monate):
        s = df[col][df.index.month.isin(monate)].dropna()
        # Für Winter: Dezember gehört zum Folgejahr-Winter → Jahr des Dez auf nächstes Jahr setzen
        if 12 in monate:
            idx = s.index.copy()
            # Dezember → Jahr +1
            jahre = np.where(s.index.month == 12, s.index.year + 1, s.index.year)
            s2 = pd.Series(s.values, index=jahre)
            return s2.groupby(s2.index).mean().dropna()
        return s.groupby(s.index.year).mean().dropna()

    fig, axes = plt.subplots(2, 2, figsize=(16, 10), sharex=True)
    axes_flat = axes.flatten()

    print()
    print("=" * 60)
    print("SAISONALE TEMPERATURTRENDS – Bremen")
    print("=" * 60)
    print(f"  {'Jahreszeit':<25} {'Ø °C':>7}  {'Trend':>15}")
    print("  " + "-" * 50)

    for ax, (jahreszeit, monate) in zip(axes_flat, jahreszeiten.items()):
        jm = jahres_mittel(monate)
        farbe = farben[jahreszeit]

        ax.plot(jm.index, jm.values, color=farbe, alpha=0.5, linewidth=1)
        glaett = jm.rolling(10, center=True).mean()
        ax.plot(glaett.index, glaett.values, color="black", linewidth=2,
                label="10-J.-Glättung")

        x = np.arange(len(jm))
        m, b = np.polyfit(x, jm.values, 1)
        trend_dez = m * 10
        ax.plot(jm.index, m * x + b, "--", color="red", linewidth=1.8,
                label=f"Trend: {trend_dez:+.2f} °C/Jhz.")

        ax.set_title(jahreszeit, fontsize=11)
        ax.set_ylabel("°C")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)

        print(f"  {jahreszeit:<25} {jm.mean():>7.2f}  {trend_dez:>+14.2f} °C/Jhz.")

    plt.suptitle("Saisonale Temperaturtrends – Bremen (1890–2026)", fontsize=13)
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "11_saisonale_trends.png", dpi=150)
    plt.close(fig)
    print(f"\n→ Gespeichert: 11_saisonale_trends.png")


# ---------------------------------------------------------------------------
# 13. Trockenperioden – längste trockene Serie pro Jahr
# ---------------------------------------------------------------------------
def trockenperioden(df: pd.DataFrame):
    """
    Für jedes Jahr:
      - Längste zusammenhängende Folge von Tagen mit RSK = 0 mm
      - Anzahl Trockenperioden >= 7 Tage
      - Anzahl Trockenperioden >= 14 Tage
    Trockentag-Definition: Niederschlag < 0.1 mm (DWD-Standard)
    """
    col = "Niederschlagsmenge_mm"
    s = df[col].dropna()

    ergebnisse = {}
    for jahr in range(s.index.year.min(), s.index.year.max() + 1):
        sub = s[s.index.year == jahr]
        if len(sub) < 300:
            continue
        trocken = (sub < 0.1).astype(int)
        max_len, cur_len = 0, 0
        perioden_7, perioden_14 = 0, 0
        laengen = []
        for v in trocken.values:
            if v:
                cur_len += 1
                max_len = max(max_len, cur_len)
            else:
                if cur_len > 0:
                    laengen.append(cur_len)
                cur_len = 0
        if cur_len > 0:
            laengen.append(cur_len)
        perioden_7  = sum(1 for l in laengen if l >= 7)
        perioden_14 = sum(1 for l in laengen if l >= 14)
        ergebnisse[jahr] = {"max": max_len, "n7": perioden_7, "n14": perioden_14}

    res = pd.DataFrame(ergebnisse).T
    res.index.name = "Jahr"

    # Konsolausgabe – Top-10 längste Trockenperioden
    print()
    print("=" * 55)
    print("TROCKENPERIODEN – längste trockene Serie pro Jahr")
    print("=" * 55)
    print(f"  Ø längste Trockenperiode: {res['max'].mean():.1f} Tage/Jahr")
    print(f"  Ø Perioden ≥ 7 Tage:      {res['n7'].mean():.1f} /Jahr")
    print(f"  Ø Perioden ≥ 14 Tage:     {res['n14'].mean():.1f} /Jahr")
    print()
    print("  Top-10 Jahre (längste Trockenperiode):")
    for jahr, row in res.nlargest(10, "max").iterrows():
        print(f"    {int(jahr)}: {int(row['max'])} Tage")

    # Grafik
    fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)

    ax = axes[0]
    ax.bar(res.index, res["max"], color="sienna", alpha=0.75, width=0.8)
    ax.plot(res["max"].rolling(10, center=True).mean(), color="black",
            linewidth=2, label="10-J.-Glättung")
    ax.axhline(res["max"].mean(), color="gold", linestyle="--", linewidth=1.5,
               label=f"Mittel: {res['max'].mean():.1f} Tage")
    ax.set_ylabel("Tage"); ax.set_title("Längste zusammenhängende Trockenperiode")
    ax.legend(fontsize=8); ax.grid(axis="y", alpha=0.3)

    ax = axes[1]
    ax.bar(res.index, res["n7"], color="peru", alpha=0.75, width=0.8)
    ax.plot(res["n7"].rolling(10, center=True).mean(), color="black", linewidth=2)
    ax.axhline(res["n7"].mean(), color="gold", linestyle="--", linewidth=1.5,
               label=f"Mittel: {res['n7'].mean():.1f}/Jahr")
    ax.set_ylabel("Anzahl"); ax.set_title("Anzahl Trockenperioden ≥ 7 Tage")
    ax.legend(fontsize=8); ax.grid(axis="y", alpha=0.3)

    ax = axes[2]
    ax.bar(res.index, res["n14"], color="chocolate", alpha=0.75, width=0.8)
    ax.plot(res["n14"].rolling(10, center=True).mean(), color="black", linewidth=2)
    ax.axhline(res["n14"].mean(), color="gold", linestyle="--", linewidth=1.5,
               label=f"Mittel: {res['n14'].mean():.1f}/Jahr")
    ax.set_ylabel("Anzahl"); ax.set_title("Anzahl Trockenperioden ≥ 14 Tage")
    ax.legend(fontsize=8); ax.grid(axis="y", alpha=0.3)
    ax.set_xlabel("Jahr")

    plt.suptitle("Trockenperioden pro Jahr – Bremen (1890–2026)", fontsize=13)
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "12_trockenperioden.png", dpi=150)
    plt.close(fig)
    print(f"\n→ Gespeichert: 12_trockenperioden.png")


# ---------------------------------------------------------------------------
# 14. Spätfröste, Frühfröste & Vegetationsperiode
# ---------------------------------------------------------------------------
def vegetationsperiode(df: pd.DataFrame):
    """
    Pro Jahr:
      - Letzter Spätfrost (Tmin < 0 °C) im Frühjahr  (Jan–Jun) → DOY
      - Erster Frühfrost  (Tmin < 0 °C) im Herbst    (Jul–Dez) → DOY
      - Vegetationsperiode = Frühfrost-DOY minus Spätfrost-DOY (Tage)
    """
    tmin = df["Min_Temperatur_Celsius"].dropna()

    spaetfrost, fruehfrost, vegperiode = {}, {}, {}
    for jahr in range(tmin.index.year.min(), tmin.index.year.max() + 1):
        # Spätfrost: letzter Frost Jan–Jun
        sf = tmin[(tmin.index.year == jahr) & (tmin.index.month <= 6) & (tmin < 0)]
        # Frühfrost: erster Frost Jul–Dez
        ff = tmin[(tmin.index.year == jahr) & (tmin.index.month >= 7) & (tmin < 0)]
        if not sf.empty:
            spaetfrost[jahr] = sf.index[-1].day_of_year
        if not ff.empty:
            fruehfrost[jahr] = ff.index[0].day_of_year
        if jahr in spaetfrost and jahr in fruehfrost:
            vegperiode[jahr] = fruehfrost[jahr] - spaetfrost[jahr]

    sf_s = pd.Series(spaetfrost).dropna()
    ff_s = pd.Series(fruehfrost).dropna()
    vp_s = pd.Series(vegperiode).dropna()

    ref = pd.Timestamp("2000-01-01")
    def doy_datum(doy):
        return (ref + pd.Timedelta(days=int(doy) - 1)).strftime("%d. %b")

    def trend_dez(s):
        x = np.arange(len(s))
        m, _ = np.polyfit(x, s.values, 1)
        return m * 10

    # Konsolausgabe
    print()
    print("=" * 60)
    print("SPÄTFRÖSTE, FRÜHFRÖSTE & VEGETATIONSPERIODE")
    print("=" * 60)
    print(f"  Ø Spätfrost (letzter Frost Jan–Jun): DOY {sf_s.mean():.0f} (≈ {doy_datum(sf_s.mean())})  Trend: {trend_dez(sf_s):+.1f} Tage/Jhz.")
    print(f"  Ø Frühfrost (erster Frost Jul–Dez):  DOY {ff_s.mean():.0f} (≈ {doy_datum(ff_s.mean())})  Trend: {trend_dez(ff_s):+.1f} Tage/Jhz.")
    print(f"  Ø Vegetationsperiode:                {vp_s.mean():.0f} Tage           Trend: {trend_dez(vp_s):+.1f} Tage/Jhz.")
    print()
    print("  Längste Vegetationsperioden (Top 10):")
    for jahr, tage in vp_s.nlargest(10).items():
        print(f"    {int(jahr)}: {int(tage)} Tage")
    print("  Kürzeste Vegetationsperioden (Top 10):")
    for jahr, tage in vp_s.nsmallest(10).items():
        print(f"    {int(jahr)}: {int(tage)} Tage")

    # Grafik
    fig, axes = plt.subplots(3, 1, figsize=(14, 13), sharex=True)

    configs = [
        (sf_s, "Letzter Spätfrost im Frühjahr (Jan–Jun)", "steelblue",
         [1, 32, 60, 91, 121, 152], ["1. Jan","1. Feb","1. Mär","1. Apr","1. Mai","1. Jun"]),
        (ff_s, "Erster Frühfrost im Herbst (Jul–Dez)", "darkorange",
         [183, 213, 244, 274, 305, 335], ["1. Jul","1. Aug","1. Sep","1. Okt","1. Nov","1. Dez"]),
        (vp_s, "Länge der Vegetationsperiode (Tage)", "forestgreen", None, None),
    ]
    for ax, (s, titel, farbe, yticks, ylabels) in zip(axes, configs):
        ax.scatter(s.index, s.values, color=farbe, s=15, alpha=0.6, zorder=3)
        ax.plot(s.rolling(10, center=True).mean(), color="black", linewidth=2,
                label="10-J.-Glättung")
        x = np.arange(len(s))
        m, b = np.polyfit(x, s.values, 1)
        ax.plot(s.index, m * x + b, "--", color="red", linewidth=1.5,
                label=f"Trend: {m*10:+.1f} Tage/Jhz.")
        if yticks:
            ax.set_yticks(yticks)
            ax.set_yticklabels(ylabels)
        else:
            ax.set_ylabel("Tage")
        ax.set_title(titel)
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)

    axes[-1].set_xlabel("Jahr")
    plt.suptitle("Spätfröste, Frühfröste & Vegetationsperiode – Bremen (1890–2026)",
                 fontsize=13)
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "13_vegetationsperiode.png", dpi=150)
    plt.close(fig)
    print(f"\n→ Gespeichert: 13_vegetationsperiode.png")


# ---------------------------------------------------------------------------
# 15. Rekord-Zeitachse
# ---------------------------------------------------------------------------
def rekord_zeitachse(df: pd.DataFrame):
    """
    Zeigt, an welchen Tagen bisherige Rekorde gebrochen wurden:
      - Tagesmaximum Temperatur (laufendes Maximum)
      - Tagesminimum Temperatur (laufendes Minimum)
      - Tagesniederschlag (laufendes Maximum)
    Zusätzlich: kumulative Anzahl neuer Rekorde pro Jahr.
    """
    kenngroessen = [
        ("Max_Temperatur_Celsius",  "Hitzerekord (Tmax)",      "max", "firebrick"),
        ("Min_Temperatur_Celsius",  "Kälterekord (Tmin)",      "min", "steelblue"),
        ("Niederschlagsmenge_mm",   "Niederschlagsrekord",     "max", "royalblue"),
    ]

    fig, axes = plt.subplots(len(kenngroessen), 2, figsize=(18, 14))

    print()
    print("=" * 65)
    print("REKORD-ZEITACHSE – wann wurden Rekorde gebrochen?")
    print("=" * 65)

    for row_ax, (col, titel, art, farbe) in zip(axes, kenngroessen):
        s = df[col].dropna()

        # Laufendes Extremum
        if art == "max":
            lauf = s.cummax()
            neu  = s[s > s.shift(1).cummax()].dropna()
            # erstes Element ist immer Rekord
            neu  = s[(s == lauf) & (s != lauf.shift(1))].dropna()
        else:
            lauf = s.cummin()
            neu  = s[(s == lauf) & (s != lauf.shift(1))].dropna()

        # Linkes Teilbild: Rekordwert-Zeitachse
        ax_l = row_ax[0]
        ax_l.plot(s.index, lauf.values, color="gray", linewidth=1,
                  alpha=0.6, label="laufendes Extremum")
        ax_l.scatter(neu.index, neu.values, color=farbe, s=20, zorder=4,
                     label=f"Neuer Rekord ({len(neu)} gesamt)")
        ax_l.set_title(f"{titel} – laufender Rekordwert")
        ax_l.set_ylabel("°C" if "Temperatur" in col else "mm")
        ax_l.legend(fontsize=8); ax_l.grid(alpha=0.3)

        # Rechtes Teilbild: Rekorde pro Jahrzehnt
        ax_r = row_ax[1]
        pro_jahrzehnt = neu.resample("10YE").count()
        pro_jahrzehnt.index = (pro_jahrzehnt.index.year // 10) * 10
        ax_r.bar(pro_jahrzehnt.index, pro_jahrzehnt.values,
                 width=8, color=farbe, alpha=0.75, edgecolor="white")
        ax_r.set_title(f"{titel} – neue Rekorde pro Jahrzehnt")
        ax_r.set_ylabel("Anzahl")
        ax_r.set_xlabel("Jahrzehnt")
        ax_r.grid(axis="y", alpha=0.3)

        # Konsolausgabe
        aktueller_rekord = lauf.iloc[-1]
        rekord_datum     = neu.index[-1].date()
        print(f"\n  {titel}:")
        print(f"    Aktueller Rekord: {aktueller_rekord:.1f}  (seit {rekord_datum})")
        print(f"    Rekorde gesamt:   {len(neu)}")
        print(f"    Letzte 5 Rekorde:")
        for datum, wert in neu.iloc[-5:].items():
            print(f"      {datum.date()}  {wert:.1f}")

    plt.suptitle("Rekord-Zeitachse – Bremen (1890–2026)", fontsize=13)
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "14_rekord_zeitachse.png", dpi=150)
    plt.close(fig)
    print(f"\n→ Gespeichert: 14_rekord_zeitachse.png")


# ---------------------------------------------------------------------------
# 11. Frühlingsbeginn-Verschiebung
# ---------------------------------------------------------------------------
def fruehlingsbeginn(df: pd.DataFrame):
    """
    Phänologischer Frühlingsbeginn nach drei Definitionen:
      A) Erster Tag im Jahr (Jan–Mai) mit Tmax >= 10 °C
      B) Erster Tag mit 5 aufeinanderfolgenden Tagen Tmax >= 10 °C
      C) Letzter Frosttag im Frühjahr (Tmin < 0 °C, Jan–Jun)
    Ausgabe: Tagesnummer (DOY) pro Jahr + Trendlinie
    """
    tmax = df["Max_Temperatur_Celsius"].dropna()
    tmin = df["Min_Temperatur_Celsius"].dropna()

    ergebnisse_a, ergebnisse_b, ergebnisse_c = {}, {}, {}

    for jahr in range(df.index.year.min(), df.index.year.max() + 1):
        # A: erster Tag Tmax >= 10 °C (Jan–Mai)
        fruehj = tmax[(tmax.index.year == jahr) & (tmax.index.month <= 5)]
        kandidaten = fruehj[fruehj >= 10]
        if not kandidaten.empty:
            ergebnisse_a[jahr] = kandidaten.index[0].day_of_year

        # B: erste 5 konsekutive Tage Tmax >= 10 °C
        alle = tmax[tmax.index.year == jahr]
        warm = (alle >= 10).astype(int)
        rollsum = warm.rolling(5).sum()
        treffer = rollsum[rollsum == 5]
        if not treffer.empty:
            erster_tag = treffer.index[0] - pd.Timedelta(days=4)
            ergebnisse_b[jahr] = erster_tag.day_of_year

        # C: letzter Frosttag im Frühjahr (Jan–Jun)
        frost = tmin[(tmin.index.year == jahr) & (tmin.index.month <= 6) & (tmin < 0)]
        if not frost.empty:
            ergebnisse_c[jahr] = frost.index[-1].day_of_year

    a = pd.Series(ergebnisse_a).dropna()
    b = pd.Series(ergebnisse_b).dropna()
    c = pd.Series(ergebnisse_c).dropna()

    def trend(s):
        x = np.arange(len(s))
        m, b_int = np.polyfit(x, s.values, 1)
        return m * 10, m * x + b_int

    # Konsolausgabe
    print()
    print("=" * 60)
    print("FRÜHLINGSBEGINN PRO JAHR (Tag des Jahres, DOY)")
    print("=" * 60)
    ref = pd.Timestamp("2000-01-01")
    for label, s, defi in [
        ("A", a, "1. Tag Tmax≥10°C      "),
        ("B", b, "5 konsek. Tage ≥10°C "),
        ("C", c, "Letzter Frosttag      "),
    ]:
        datum = (ref + pd.Timedelta(days=int(s.mean()) - 1)).strftime("%d. %b")
        t_dez, _ = trend(s)
        print(f"  Def. {label} ({defi}): Ø DOY {s.mean():.0f} (≈ {datum})  Trend: {t_dez:+.1f} Tage/Jhz.")

    # Grafik
    fig, axes = plt.subplots(3, 1, figsize=(14, 13), sharex=True)
    configs = [
        (a, "A – Erster Tag Tmax ≥ 10 °C (Jan–Mai)", "forestgreen"),
        (b, "B – Erste 5 konsekutive Tage Tmax ≥ 10 °C", "darkorange"),
        (c, "C – Letzter Frosttag im Frühjahr (Jan–Jun)", "steelblue"),
    ]
    for ax, (s, titel, farbe) in zip(axes, configs):
        ax.scatter(s.index, s.values, color=farbe, s=15, alpha=0.7, zorder=3)
        ax.plot(s.rolling(10, center=True).mean(), color="black", linewidth=2,
                label="10-J.-Glättung")
        t_dez, trendlinie = trend(s)
        ax.plot(s.index, trendlinie, "--", color="red", linewidth=1.5,
                label=f"Trend: {t_dez:+.1f} Tage/Jahrzehnt")
        ax.set_yticks([1, 32, 60, 91, 121, 152])
        ax.set_yticklabels(["1. Jan", "1. Feb", "1. Mär", "1. Apr", "1. Mai", "1. Jun"])
        ax.set_ylabel("Datum")
        ax.set_title(titel)
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)

    axes[-1].set_xlabel("Jahr")
    plt.suptitle("Frühlingsbeginn-Verschiebung – Bremen (1890–2026)", fontsize=13)
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "10_fruehlingsbeginn.png", dpi=150)
    plt.close(fig)
    print(f"\n→ Gespeichert: 10_fruehlingsbeginn.png")


# ---------------------------------------------------------------------------
# 16. Klimatische Wasserbalance (vereinfachter Duerreindikator)
# ---------------------------------------------------------------------------
def wasserbalance(df: pd.DataFrame):
    """
    Vereinfachter Wasserbilanz-Ansatz auf Tagesbasis:
      PET_approx = max(0, 0.6 * (Tmean + 5))  [mm/Tag]
      Wasserbalance = Niederschlag - PET_approx
    Hinweis: Das ist ein Screening-Indikator, keine vollstaendige ET0-Berechnung.
    """
    t = df["Temperatur_Celsius"].astype(float)
    p = df["Niederschlagsmenge_mm"].astype(float)

    # Monatliche Summen/Mittel als Basis fuer Thornthwaite-PET
    mon = pd.DataFrame({
        "T": t.resample("ME").mean(),
        "P": p.resample("ME").sum(),
    }).dropna()
    mon["Jahr"] = mon.index.year
    mon["Monat"] = mon.index.month

    # Mittlere Tageslaenge pro Monat fuer ~53N (Bremen), Stunden
    daylen = {
        1: 8.3, 2: 10.0, 3: 11.9, 4: 14.1, 5: 15.8, 6: 16.6,
        7: 16.0, 8: 14.5, 9: 12.6, 10: 10.5, 11: 8.8, 12: 7.8,
    }

    pet_vals = []
    for jahr, g in mon.groupby("Jahr"):
        g = g.copy()
        t_pos = g["T"].clip(lower=0)
        I = ((t_pos / 5) ** 1.514).sum()
        if I <= 0:
            g["PET"] = 0.0
        else:
            a = (6.75e-7) * (I ** 3) - (7.71e-5) * (I ** 2) + (1.792e-2) * I + 0.49239

            def pet_month(row):
                tm = max(row["T"], 0)
                if tm == 0:
                    return 0.0
                m = int(row["Monat"])
                n_days = row.name.days_in_month
                heat = (10 * tm / I) ** a
                return 16 * (daylen[m] / 12) * (n_days / 30) * heat

            g["PET"] = g.apply(pet_month, axis=1)
        pet_vals.append(g)

    mon = pd.concat(pet_vals).sort_index()
    mon["WB"] = mon["P"] - mon["PET"]

    jahres_wb = mon["WB"].resample("YE").sum().dropna()
    jahres_wb.index = jahres_wb.index.year

    sommer_mon = mon[mon["Monat"].isin([4, 5, 6, 7, 8, 9])]
    sommer_wb = sommer_mon["WB"].resample("YE").sum().dropna()
    sommer_wb.index = sommer_wb.index.year

    print()
    print("=" * 62)
    print("KLIMATISCHE WASSERBILANZ (vereinfachter Indikator)")
    print("=" * 62)
    print(f"  Jahresbilanz Mittel:  {jahres_wb.mean():+.1f} mm/Jahr")
    print(f"  Sommerbilanz Mittel:  {sommer_wb.mean():+.1f} mm (Apr-Sep)")
    print(f"  Trockenstes Jahr:     {jahres_wb.idxmin()} ({jahres_wb.min():+.1f} mm)")
    print(f"  Nassestes Jahr:       {jahres_wb.idxmax()} ({jahres_wb.max():+.1f} mm)")

    fig, axes = plt.subplots(2, 1, figsize=(14, 9), sharex=True)

    ax = axes[0]
    colors = ["firebrick" if v < 0 else "steelblue" for v in jahres_wb.values]
    ax.bar(jahres_wb.index, jahres_wb.values, color=colors, width=0.8, alpha=0.8)
    ax.plot(jahres_wb.rolling(10, center=True).mean(), color="black", linewidth=2,
            label="10-J.-Glättung")
    ax.axhline(0, color="gray", linestyle="--", linewidth=1)
    ax.set_title("Jährliche Wasserbalance: Niederschlag - PET (Thornthwaite)")
    ax.set_ylabel("mm/Jahr")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)

    ax2 = axes[1]
    colors2 = ["firebrick" if v < 0 else "seagreen" for v in sommer_wb.values]
    ax2.bar(sommer_wb.index, sommer_wb.values, color=colors2, width=0.8, alpha=0.8)
    ax2.plot(sommer_wb.rolling(10, center=True).mean(), color="black", linewidth=2,
             label="10-J.-Glättung")
    ax2.axhline(0, color="gray", linestyle="--", linewidth=1)
    ax2.set_title("Sommer-Wasserbalance (Apr-Sep, Thornthwaite)")
    ax2.set_ylabel("mm")
    ax2.set_xlabel("Jahr")
    ax2.legend(fontsize=8)
    ax2.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "15_wasserbalance.png", dpi=150)
    plt.close(fig)
    print("→ Gespeichert: 15_wasserbalance.png")


# ---------------------------------------------------------------------------
# 17. Autokorrelation & Persistenz
# ---------------------------------------------------------------------------
def persistenzanalyse(df: pd.DataFrame):
    temp = df["Temperatur_Celsius"].dropna()
    rain = df["Niederschlagsmenge_mm"].dropna()

    lags = range(1, 31)
    ac_temp = [temp.autocorr(lag=l) for l in lags]
    ac_rain = [rain.autocorr(lag=l) for l in lags]

    def run_lengths(mask: pd.Series):
        lengths = []
        cur = 0
        for v in mask.astype(int).values:
            if v == 1:
                cur += 1
            elif cur > 0:
                lengths.append(cur)
                cur = 0
        if cur > 0:
            lengths.append(cur)
        return lengths

    hitze_runs = run_lengths(df["Max_Temperatur_Celsius"].fillna(-999) >= 30)
    regen_runs = run_lengths(df["Niederschlagsmenge_mm"].fillna(0) >= 1.0)

    print()
    print("=" * 55)
    print("AUTOKORRELATION & PERSISTENZ")
    print("=" * 55)
    print(f"  Temp-Autokorr Lag1: {ac_temp[0]:.3f}")
    print(f"  Regen-Autokorr Lag1: {ac_rain[0]:.3f}")
    print(f"  Längste Hitzewelle (Tmax>=30): {max(hitze_runs) if hitze_runs else 0} Tage")
    print(f"  Längste Regenserie (>=1mm):    {max(regen_runs) if regen_runs else 0} Tage")

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    axes[0, 0].bar(list(lags), ac_temp, color="tomato", alpha=0.8)
    axes[0, 0].axhline(0, color="black", linewidth=0.8)
    axes[0, 0].set_title("Autokorrelation Temperatur (Lags 1-30)")
    axes[0, 0].set_ylabel("r")
    axes[0, 0].grid(axis="y", alpha=0.3)

    axes[0, 1].bar(list(lags), ac_rain, color="royalblue", alpha=0.8)
    axes[0, 1].axhline(0, color="black", linewidth=0.8)
    axes[0, 1].set_title("Autokorrelation Niederschlag (Lags 1-30)")
    axes[0, 1].set_ylabel("r")
    axes[0, 1].grid(axis="y", alpha=0.3)

    axes[1, 0].hist(hitze_runs, bins=range(1, 20), color="firebrick", alpha=0.8)
    axes[1, 0].set_title("Verteilung Hitzewellen-Längen")
    axes[1, 0].set_xlabel("Tage")
    axes[1, 0].set_ylabel("Häufigkeit")
    axes[1, 0].grid(axis="y", alpha=0.3)

    axes[1, 1].hist(regen_runs, bins=range(1, 20), color="steelblue", alpha=0.8)
    axes[1, 1].set_title("Verteilung Regenserien-Längen")
    axes[1, 1].set_xlabel("Tage")
    axes[1, 1].set_ylabel("Häufigkeit")
    axes[1, 1].grid(axis="y", alpha=0.3)

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "16_persistenzanalyse.png", dpi=150)
    plt.close(fig)
    print("→ Gespeichert: 16_persistenzanalyse.png")


# ---------------------------------------------------------------------------
# 18. Temperatur-Heatmap (Monat x Jahr)
# ---------------------------------------------------------------------------
def temperatur_heatmap(df: pd.DataFrame):
    mon = df["Temperatur_Celsius"].resample("ME").mean().dropna()
    table = mon.to_frame(name="T")
    table["Jahr"] = table.index.year
    table["Monat"] = table.index.month
    pivot = table.pivot(index="Jahr", columns="Monat", values="T")

    fig, ax = plt.subplots(figsize=(12, 10))
    im = ax.imshow(pivot.values, aspect="auto", cmap="coolwarm")
    ax.set_title("Monatliche Temperaturmittel – Heatmap")
    ax.set_xlabel("Monat")
    ax.set_ylabel("Jahr")
    ax.set_xticks(range(12))
    ax.set_xticklabels(["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
                        "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"])

    y_ticks = np.linspace(0, len(pivot.index) - 1, 12, dtype=int)
    ax.set_yticks(y_ticks)
    ax.set_yticklabels([str(pivot.index[i]) for i in y_ticks])

    plt.colorbar(im, ax=ax, label="°C")
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "17_temperatur_heatmap.png", dpi=150)
    plt.close(fig)
    print("→ Gespeichert: 17_temperatur_heatmap.png")


# ---------------------------------------------------------------------------
# 19. Wind-Rose (Windstaerken-Klassen)
# ---------------------------------------------------------------------------
def windrose_klassen(df: pd.DataFrame):
    """
    Ohne Windrichtung wird eine Klassen-Rose dargestellt:
    Kreis-Segmente repraesentieren Windgeschwindigkeitsklassen (km/h).
    """
    w = df["Mittel_Windgeschwindigkeit_kmh"].dropna()

    bins = [0, 2, 4, 6, 8, 10, 12, 16, 100]
    labels = ["0-2", "2-4", "4-6", "6-8", "8-10", "10-12", "12-16", ">16"]
    cats = pd.cut(w, bins=bins, labels=labels, right=False)
    freq = cats.value_counts(normalize=True).reindex(labels).fillna(0) * 100

    n = len(labels)
    theta = np.linspace(0, 2 * np.pi, n, endpoint=False)
    width = 2 * np.pi / n

    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection="polar")
    bars = ax.bar(theta, freq.values, width=width * 0.95, bottom=0,
                  color=plt.cm.Blues(np.linspace(0.4, 0.95, n)), alpha=0.9)
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_xticks(theta)
    ax.set_xticklabels(labels)
    ax.set_title("Wind-Rose (Häufigkeit nach Windstärkenklassen)")
    ax.set_ylabel("%")

    for bar, v in zip(bars, freq.values):
        if v > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.4,
                    f"{v:.1f}%", ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "18_windrose_klassen.png", dpi=150)
    plt.close(fig)

    print()
    print("WINDKLASSEN-HÄUFIGKEITEN:")
    for lab, val in freq.items():
        print(f"  {lab:>5} km/h: {val:5.1f}%")
    print("→ Gespeichert: 18_windrose_klassen.png")


# ---------------------------------------------------------------------------
# 20. Jahresgang-Baender (Temperatur)
# ---------------------------------------------------------------------------
def jahresgang_baender(df: pd.DataFrame):
    temp = df["Temperatur_Celsius"].dropna()
    doy = temp.index.dayofyear

    clim_mean = temp.groupby(doy).mean()
    clim_p10 = temp.groupby(doy).quantile(0.10)
    clim_p90 = temp.groupby(doy).quantile(0.90)

    perioden = {
        "1890-1939": (1890, 1939),
        "1940-1989": (1940, 1989),
        "1990-2026": (1990, 2026),
    }
    farben = {"1890-1939": "steelblue", "1940-1989": "darkorange", "1990-2026": "firebrick"}

    fig, ax = plt.subplots(figsize=(15, 6))
    x = np.arange(1, 367)

    y_mean = clim_mean.reindex(x).interpolate(limit_direction="both")
    y_p10 = clim_p10.reindex(x).interpolate(limit_direction="both")
    y_p90 = clim_p90.reindex(x).interpolate(limit_direction="both")

    ax.fill_between(x, y_p10, y_p90, color="lightgray", alpha=0.5, label="P10-P90 (alle Jahre)")
    ax.plot(x, y_mean, color="black", linewidth=2, label="Mittel (alle Jahre)")

    for label, (y1, y2) in perioden.items():
        s = temp[(temp.index.year >= y1) & (temp.index.year <= y2)]
        p = s.groupby(s.index.dayofyear).mean().reindex(x).interpolate(limit_direction="both")
        ax.plot(x, p, color=farben[label], linewidth=1.8, label=label)

    month_starts = np.cumsum([1, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30])
    ax.set_xticks(month_starts)
    ax.set_xticklabels(["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
                        "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"])
    ax.set_xlim(1, 366)
    ax.set_ylabel("°C")
    ax.set_title("Jahresgang-Bänder der Temperatur")
    ax.legend(ncol=2, fontsize=8)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "19_jahresgang_baender.png", dpi=150)
    plt.close(fig)
    print("→ Gespeichert: 19_jahresgang_baender.png")


# ---------------------------------------------------------------------------
# Haupt
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"Lade Daten: {DATA_FILE}")
    df = lade_daten(DATA_FILE)

    uebersicht(df)
    temperaturtrend(df)
    niederschlag(df)
    sonnenschein(df)
    extremwerte(df)
    saisonale_boxplots(df)
    korrelation(df)
    hitzeextreme_pro_jahr(df)
    niederschlag_extremwerte_pro_jahr(df)
    klimanormalperioden(df)
    temperaturanomalie(df)
    fruehlingsbeginn(df)
    saisonale_trends(df)
    trockenperioden(df)
    vegetationsperiode(df)
    rekord_zeitachse(df)
    wasserbalance(df)
    persistenzanalyse(df)
    temperatur_heatmap(df)
    windrose_klassen(df)
    jahresgang_baender(df)

    print()
    print(f"Alle Grafiken gespeichert in: {OUTPUT_DIR}")
