import pandas as pd
import streamlit as st
from modul_strecken import berechne_strecken
from modul_startend_strategie import berechne_start_endwerte
from modul_hilfsfunktionen import sichere_dauer


# ------------------------------------------------------------
# 🧮 TDS-Berechnung basierend auf 4 Start/End-Werten
# ------------------------------------------------------------
def berechne_tds_aus_werte(verd_leer, verd_voll, vol_leer, vol_voll, pf, pw, pb):
    """
    Berechnet die TDS-Kennzahlen aus den Differenzen der Verdrängung und des Ladungsvolumens
    unter Berücksichtigung der Dichteparameter.

    Parameter:
    - verd_leer: Verdrängung zu Beginn (t)
    - verd_voll: Verdrängung am Ende (t)
    - vol_leer: Volumen zu Beginn (m³)
    - vol_voll: Volumen am Ende (m³)
    - pf: Feststoffdichte (t/m³)
    - pw: Wasserdichte (t/m³)
    - pb: Bodendichte zur Volumenberechnung (t/m³)

    Rückgabe:
    - dict mit Masse, Volumen, Dichte und berechneten TDS-Werten
    """

    # ❌ Bei fehlenden Werten wird ein Dictionary mit None zurückgegeben
    if None in [verd_leer, verd_voll, vol_leer, vol_voll]:
        return {k: None for k in [
            "ladungsmasse", "ladungsvolumen", "ladungsdichte", "feststoffkonzentration",
            "feststoffvolumen", "feststoffmasse", "bodenvolumen"
        ]}

    # 💡 Grundlegende Berechnungen
    ladungsmasse = verd_voll - verd_leer
    ladungsvolumen = vol_voll - vol_leer
    ladungsdichte = ladungsmasse / ladungsvolumen if ladungsvolumen else None

    # 📈 Feststoffkonzentration = (ρ_mix - ρ_wasser) / (ρ_feststoff - ρ_wasser)
    feststoffkonzentration = (ladungsdichte - pw) / (pf - pw) if ladungsdichte else None
    feststoffvolumen = feststoffkonzentration * ladungsvolumen if feststoffkonzentration else None
    feststoffmasse = feststoffvolumen * pf if feststoffvolumen else None

    # 🧮 Umrechnung in Bodenvolumen (geologisch bewertbar)
    bodenvolumen = ((pf - pw) / (pf * (pb - pw))) * feststoffmasse if feststoffmasse and pb else None

    return {
        "ladungsmasse": ladungsmasse,
        "ladungsvolumen": ladungsvolumen,
        "ladungsdichte": ladungsdichte,
        "feststoffkonzentration": feststoffkonzentration,
        "feststoffvolumen": feststoffvolumen,
        "feststoffmasse": feststoffmasse,
        "bodenvolumen": bodenvolumen
    }


# ------------------------------------------------------------
# 📊 Mittlere Gemischdichte für Umläufe bestimmen
# ------------------------------------------------------------
def berechne_mittlere_gemischdichte(df, umlauf_info_df, debug=False):
    """
    Berechnet die mittlere Gemischdichte (BB + SB) für jeden Umlauf.
    Basis: Status == 2 oder Status_neu == "Baggern"
    Nur Werte > 0.99 werden berücksichtigt (Filter gegen leere/falsche Werte).

    Rückgabe:
    - DataFrame mit "Umlauf" und "Mittlere_Gemischdichte"
    """

    gemischdichte = []

    # 📌 Spaltenwahl abhängig von Status-Definition im DF
    status_col = "Status_neu" if "Status_neu" in df.columns else "Status"
    gueltige_status = "Baggern" if status_col == "Status_neu" else 2

    for _, row in umlauf_info_df.iterrows():
        start = pd.to_datetime(row["Start Leerfahrt"], utc=True)
        ende = pd.to_datetime(row["Ende"], utc=True)

        # ⏱ Auswahl der Messwerte im Zeitfenster des Umlaufs
        df_umlauf = df[(df["timestamp"] >= start) & (df["timestamp"] <= ende)]

        # 🎯 Filter: Nur Zeilen mit gültigem Status
        df_aktiv = df_umlauf[df_umlauf[status_col] == gueltige_status]

        # 🔬 Nur realistische Werte (>0.99) berücksichtigen
        gueltige_bb = df_aktiv["Gemischdichte_BB"][df_aktiv["Gemischdichte_BB"] > 0.99]
        gueltige_sb = df_aktiv["Gemischdichte_SB"][df_aktiv["Gemischdichte_SB"] > 0.99]

        # 🔗 Zusammenführen und Mittelwert berechnen
        alle = pd.concat([gueltige_bb, gueltige_sb])
        mittelwert = alle.mean() if not alle.empty else None

        gemischdichte.append({
            "Umlauf": row["Umlauf"],
            "Mittlere_Gemischdichte": mittelwert
        })

    return pd.DataFrame(gemischdichte)


# ------------------------------------------------------------
# 🧪 AMOB-Zeitberechnung auf Basis Gemischdichte + Status
# ------------------------------------------------------------
def berechne_amob_dauer(df, seite="BB"):
    """
    Berechnet die AMOB-Gesamtdauer für eine Seite (BB oder SB).
    Berücksichtigt nur:
    - Status_neu == "Baggern"
    - Gemischdichte > 1.06 t/m³
    - vorhandene AMOB-Zeitangaben

    Rückgabe:
    - Gesamt-AMOB-Zeit in Sekunden
    """

    if df.empty:
        return 0.0

    status_col = "Status_neu" if "Status_neu" in df.columns else "Status"
    dichte_col = f"Gemischdichte_{seite}"
    amob_col = f"AMOB_Zeit_{seite}"

    # ✅ Prüfung, ob notwendige Spalten überhaupt existieren
    if not all(col in df.columns for col in [status_col, dichte_col, amob_col]):
        return 0.0

    # 🎯 Filter anwenden: Nur bei "Baggern", hoher Dichte und vorhandener AMOB-Zeit
    df_filtered = df[
        (df[status_col] == "Baggern") &
        (df[dichte_col] > 1.06) &
        (df[amob_col].notna())
    ]

    if df_filtered.empty:
        return 0.0

    # ➕ Summe aller AMOB-Werte dieser Seite im betrachteten Zeitraum
    return df_filtered[amob_col].sum()


  
def berechne_umlauf_auswertung(df, row, schiffsparameter, strategie, pf, pw, pb, zeitformat, epsg_code):
    """
    Vollständige Auswertung eines Umlaufs:
    - Filtert Daten auf den Zeitbereich des Umlaufs
    - Ermittelt Start-/Endwerte nach Strategie
    - Berechnet TDS-Kennzahlen (Volumen, Masse, Konzentration usw.)
    - Misst Strecken (Leerfahrt, Baggern, Verbringen)
    - Liefert formatierte Werte für UI
    """

    # ------------------------------------------------------------
    # 🕓 Zeitbereich definieren und sicherstellen, dass alles timezone-aware ist
    # ------------------------------------------------------------
    t_start = pd.to_datetime(row["Start Leerfahrt"])
    t_ende = pd.to_datetime(row["Ende"])
    if t_start.tzinfo is None:
        t_start = t_start.tz_localize("UTC")
    if t_ende.tzinfo is None:
        t_ende = t_ende.tz_localize("UTC")
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")

    # 🔍 Filter: Zeitfenster des Umlaufs extrahieren
    df_umlauf = df[(df["timestamp"] >= t_start) & (df["timestamp"] <= t_ende)]

    # ------------------------------------------------------------
    # 📍 Aktive Polygone extrahieren (für Info-Ausgabe)
    # ------------------------------------------------------------
    bagger_namen = df_umlauf[df_umlauf["Status"] == 2]["Polygon_Name"].dropna().unique()
    verbring_namen = df_umlauf[df_umlauf["Status"].isin([4, 5, 6])]["Polygon_Name"].dropna().unique()

    # ------------------------------------------------------------
    # 🔍 Start-/Endwerte nach gewählter Strategie ermitteln
    # ------------------------------------------------------------
    if "Verdraengung" in df_umlauf.columns and "Ladungsvolumen" in df_umlauf.columns:
        werte, debug_info = berechne_start_endwerte(df_umlauf, strategie, df_gesamt=df)
        tds_werte = berechne_tds_aus_werte(
            werte.get("Verdraengung Start"),
            werte.get("Verdraengung Ende"),
            werte.get("Ladungsvolumen Start"),
            werte.get("Ladungsvolumen Ende"),
            pf, pw, pb
        )
    else:
        werte = {
            "Verdraengung Start": None, "Verdraengung Ende": None,
            "Ladungsvolumen Start": None, "Ladungsvolumen Ende": None
        }
        tds_werte = berechne_tds_aus_werte(None, None, None, None, pf, pw, pb)
        debug_info = ["⚠️ Spalten fehlen – keine Strategieauswertung möglich."]

    # ------------------------------------------------------------
    # 📦 Basiswerte + Differenzen berechnen
    # ------------------------------------------------------------
    kennzahlen = {
        "verdraengung_leer": werte.get("Verdraengung Start"),
        "verdraengung_voll": werte.get("Verdraengung Ende"),
        "volumen_leer": werte.get("Ladungsvolumen Start"),
        "volumen_voll": werte.get("Ladungsvolumen Ende"),
    }
    kennzahlen["delta_verdraengung"] = (
        werte.get("Verdraengung Ende") - werte.get("Verdraengung Start")
        if None not in [werte.get("Verdraengung Start"), werte.get("Verdraengung Ende")] else None
    )
    kennzahlen["delta_volumen"] = (
        werte.get("Ladungsvolumen Ende") - werte.get("Ladungsvolumen Start")
        if None not in [werte.get("Ladungsvolumen Start"), werte.get("Ladungsvolumen Ende")] else None
    )

    # ------------------------------------------------------------
    # 📏 Streckenberechnung (inkl. Pufferzeit für Starterkennung)
    # ------------------------------------------------------------
    df_umlauf_ext = df[(df["timestamp"] >= (t_start - pd.Timedelta("15min"))) & (df["timestamp"] <= t_ende)]
    status_col = "Status_neu" if "Status_neu" in df_umlauf_ext.columns else "Status"
    strecken = berechne_strecken(df_umlauf_ext, "RW_Schiff", "HW_Schiff", status_col, epsg_code)

    def format_km(val):
        return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if val is not None else "-"

    strecke_disp = {
        "leerfahrt": format_km(strecken.get("leerfahrt")),
        "baggern": format_km(strecken.get("baggern")),
        "vollfahrt": format_km(strecken.get("vollfahrt")),
        "verbringen": format_km(strecken.get("verbringen")),
        "gesamt": format_km(sum(v for v in strecken.values() if v is not None))
    }

    # ------------------------------------------------------------
    # ⚙️ AMOB-Dauer (BB/SB je nach Schiffsparametern)
    # ------------------------------------------------------------
    nutze_bb = schiffsparameter.get("Einstellungen", {}).get("Nutze_BB", True)
    nutze_sb = schiffsparameter.get("Einstellungen", {}).get("Nutze_SB", False)

    amob_dauer = 0.0
    if nutze_bb:
        amob_dauer += berechne_amob_dauer(df_umlauf, seite="BB")
    if nutze_sb:
        amob_dauer += berechne_amob_dauer(df_umlauf, seite="SB")

    kennzahlen["amob_dauer_s"] = amob_dauer
    kennzahlen["dauer_baggern_s"] = (row["Start Vollfahrt"] - row["Start Baggern"]).total_seconds()

    # ------------------------------------------------------------
    # 🧊 Dominante Dichtewerte ermitteln (nur bei Status_neu == "Baggern")
    # ------------------------------------------------------------
    dichtewerte = {
        "Dichte_Polygon_Name": None,
        "Ortsdichte": None,
        "Ortsspezifisch": None,
        "Mindichte": None
    }

    df_baggern = df_umlauf[df_umlauf[status_col] == "Baggern"]
    if not df_baggern.empty:
        for spalte in dichtewerte.keys():
            if spalte in df_baggern.columns:
                haeufigster = df_baggern[spalte].mode(dropna=True)
                dichtewerte[spalte] = haeufigster.iloc[0] if not haeufigster.empty else None

    # ------------------------------------------------------------
    # 💶 Bonusabrechnung – zwei Methoden: HPA oder MoNa
    # ------------------------------------------------------------
    bonus_methode = st.session_state.get("bonus_methode", "hpa")
    if bonus_methode == "mona":
        mona_werte = st.session_state.get("bonus_mona_werte", {})
        dichtewerte.update({
            "Dichte_Polygon_Name": "manuell",
            "Ortsdichte": mona_werte.get("ortsdichte"),
            "Ortsspezifisch": mona_werte.get("ortspezifisch"),
            "Mindichte": mona_werte.get("mindichte"),
            "Maxdichte": mona_werte.get("maxdichte")
        })

    abrechnung = {
        "faktor": None,
        "volumen": None,
        "strecke": None
    }

    konzentration = tds_werte.get("feststoffkonzentration")
    ladungsdichte = tds_werte.get("ladungsdichte")
    volumen_diff = kennzahlen.get("delta_volumen")
    strecken_summe = sum(v for k, v in strecken.items() if k in ["leerfahrt", "vollfahrt", "verbringen"] and v)

    if bonus_methode == "hpa":
        ortswert = dichtewerte.get("Ortsspezifisch")
        mindichte = dichtewerte.get("Mindichte")
        if ladungsdichte is not None and mindichte is not None and ladungsdichte < mindichte:
            abrechnung["faktor"] = 0.0
            abrechnung["volumen"] = 0.0
            abrechnung["strecke"] = 0.0
        elif konzentration is not None and ortswert:
            tds_dichte = konzentration * pf
            faktor = tds_dichte / ortswert
            faktor = min(max(faktor, 0.85), 1.15)
            abrechnung["faktor"] = faktor
            abrechnung["volumen"] = volumen_diff * faktor if volumen_diff else None
            abrechnung["strecke"] = strecken_summe * faktor if strecken_summe else None

    elif bonus_methode == "mona":
        mona_werte = st.session_state.get("bonus_mona_werte", {})
        p_min = mona_werte.get("mindichte")
        p_max = mona_werte.get("maxdichte")
        af_min = 0.85
        af_max = 1.15

        if ladungsdichte is None or p_min is None or p_max is None:
            abrechnung["faktor"] = None
        else:
            if ladungsdichte < p_min:
                faktor = 0.0
            elif ladungsdichte > p_max:
                faktor = af_max
            else:
                maf = (af_max - af_min) / (p_max - p_min)
                faktor = maf * (ladungsdichte - p_min) + af_min
                faktor = min(max(faktor, af_min), af_max)

            abrechnung["faktor"] = faktor
            abrechnung["volumen"] = volumen_diff * faktor if volumen_diff else None
            abrechnung["strecke"] = strecken_summe * faktor if strecken_summe else None

    # ------------------------------------------------------------
    # ⏱ Dauerwerte für UI (als Strings)
    # ------------------------------------------------------------
    dauer_disp = {
        "leerfahrt": sichere_dauer(row.get("Start Leerfahrt"), row.get("Start Baggern"), zeitformat),
        "baggern": sichere_dauer(row.get("Start Baggern"), row.get("Start Vollfahrt"), zeitformat),
        "vollfahrt": sichere_dauer(row.get("Start Vollfahrt"), row.get("Start Verklappen/Pump/Rainbow"), zeitformat),
        "verbringen": sichere_dauer(row.get("Start Verklappen/Pump/Rainbow"), row.get("Ende"), zeitformat),
        "umlauf": sichere_dauer(row.get("Start Leerfahrt"), row.get("Ende"), zeitformat),
    }

    # ➕ Bonuswerte mit in tds-Werte einpflegen
    tds_werte["abrechnungsfaktor"] = abrechnung.get("faktor")
    tds_werte["abrechnungsvolumen"] = abrechnung.get("volumen")

    # ------------------------------------------------------------
    # 🔁 Alles zurückgeben
    # ------------------------------------------------------------
    return (
        tds_werte, werte, kennzahlen, strecken,
        strecke_disp, dauer_disp, debug_info,
        bagger_namen, verbring_namen,
        amob_dauer, dichtewerte, abrechnung
    )


# 🔚 Modulexport (optional, aber korrekt)
__all__ = ["berechne_tds_aus_werte", "berechne_umlauf_auswertung"]
