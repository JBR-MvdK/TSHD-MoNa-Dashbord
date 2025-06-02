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


# ------------------------------------------------------------
# 🧪 Hauptfunktion zur Auswertung eines Umlaufs
# ------------------------------------------------------------
def berechne_umlauf_auswertung(df, row, schiffsparameter, strategie, pf, pw, pb, zeitformat, epsg_code, df_manuell=None, nutze_schiffstrategie=True, nutze_gemischdichte=True):

    """
    Vollständige Auswertung eines Umlaufs:
    - Filtert Daten auf den Zeitbereich des Umlaufs
    - Ermittelt Start-/Endwerte nach Strategie
    - Berechnet TDS-Kennzahlen (Volumen, Masse, Konzentration usw.)
    - Misst Strecken (Leerfahrt, Baggern, Verbringen)
    - Liefert formatierte Werte für UI
    - Integriert manuelle Eingaben (Feststoff / Zentrifuge) aus df_manuell
    """

    # ------------------------------------------------------------
    # 🕓 Zeitbereich definieren (Start/Ende) + Zeitzonen prüfen
    # ------------------------------------------------------------
    t_start = pd.to_datetime(row["Start Leerfahrt"])
    t_ende = pd.to_datetime(row["Ende"])

    # Sicherstellen, dass Zeitstempel Zeitzonen enthalten (UTC)
    if t_start.tzinfo is None:
        t_start = t_start.tz_localize("UTC")
    if t_ende.tzinfo is None:
        t_ende = t_ende.tz_localize("UTC")
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")

    # 🔍 Eingrenzen der Daten auf das aktuelle Umlaufs-Zeitfenster
    df_umlauf = df[(df["timestamp"] >= t_start) & (df["timestamp"] <= t_ende)]

    # ------------------------------------------------------------
    # 📍 Aktive Polygone erfassen (für Analyse und Info-Zwecke)
    # ------------------------------------------------------------
    # Baggergebiete (Status == 2)
    if "Polygon_Name" in df_umlauf.columns and "Status" in df_umlauf.columns:
        bagger_namen = df_umlauf[df_umlauf["Status"] == 2]["Polygon_Name"].dropna().unique()
    else:
        bagger_namen = []

    # Verbringstellen (Status 4, 5, 6)
    if "Polygon_Name" in df_umlauf.columns and "Status" in df_umlauf.columns:
        verbring_namen = df_umlauf[df_umlauf["Status"].isin([4, 5, 6])]["Polygon_Name"].dropna().unique()
    else:
        verbring_namen = []

    # ------------------------------------------------------------
    # 🔍 Ermittlung von Start-/Endwerten nach gewählter Strategie
    # ------------------------------------------------------------
    if "Verdraengung" in df_umlauf.columns and "Ladungsvolumen" in df_umlauf.columns:
        # Start-/Endwerte per Strategie berechnen (z. B. Median, Glättung)
        werte, debug_info = berechne_start_endwerte(df_umlauf, strategie, df_gesamt=df, nutze_schiffstrategie=nutze_schiffstrategie, nutze_gemischdichte=nutze_gemischdichte)

        # ⛴️ Aus den Werten TDS-Kennzahlen berechnen (z. B. Konzentration, Volumen, Masse)
        tds_werte = berechne_tds_aus_werte(
            werte.get("Verdraengung Start"),
            werte.get("Verdraengung Ende"),
            werte.get("Ladungsvolumen Start"),
            werte.get("Ladungsvolumen Ende"),
            pf, pw, pb
        )
    else:
        # ❌ Fallback bei fehlenden Spalten
        werte = {
            "Verdraengung Start": None,
            "Verdraengung Ende": None,
            "Ladungsvolumen Start": None,
            "Ladungsvolumen Ende": None
        }
        tds_werte = berechne_tds_aus_werte(None, None, None, None, pf, pw, pb)
        debug_info = ["⚠️ Spalten fehlen – keine Strategieauswertung möglich."]

    # ------------------------------------------------------------------------------
    # ➕ Manuelle Feststoffdaten (falls vorhanden) integrieren
    # ------------------------------------------------------------------------------
    feststoff = proz = voll_vol = feststoff_gemisch = gesamt = None

    if df_manuell is not None:
        try:
            # 🕓 Passenden Datensatz im df_manuell anhand Startzeit Baggern finden
            ts = pd.to_datetime(row["Start Baggern"], utc=True)
            eintrag = df_manuell[df_manuell["timestamp_beginn_baggern"] == ts]

            if not eintrag.empty:
                eintrag = eintrag.iloc[0]
                feststoff = eintrag.get("feststoff")
                proz = eintrag.get("proz_wert")
                voll_vol = werte.get("Ladungsvolumen Ende")

                # 🔬 Berechnung: gemischtes Volumen, Zusatzvolumen, Gesamtfeststoff
                if pd.notna(feststoff) and pd.notna(proz) and pd.notna(voll_vol):
                    gemisch = voll_vol - feststoff
                    feststoff_gemisch = gemisch * (proz / 100)
                    gesamt = feststoff + feststoff_gemisch

        except Exception as e:
            st.warning(f"⚠️ Fehler bei manuellen Werten: {e}")

    # 🔁 Ergänzung des TDS-Wert-Dictionaries um manuelle Eingaben
    tds_werte["feststoff_manuell"] = feststoff
    tds_werte["proz"] = proz
    tds_werte["voll_volumen"] = voll_vol
    tds_werte["feststoff_gemisch"] = feststoff_gemisch
    tds_werte["feststoff_gesamt"] = gesamt


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
        return f"{val:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".") if val is not None else "-"

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
        "Mindichte": None,
        "Maxdichte": None
    }
    
    alle_dichten = st.session_state.get("bonus_dichtewerte", [])
    
    # Aus Messdaten versuchen, den häufigsten Polygonnamen zu finden
    df_baggern = df_umlauf[df_umlauf[status_col] == "Baggern"]
    polygon_name = None
    if "Dichte_Polygon_Name" in df_baggern.columns:
        haeufigster_polygon = df_baggern["Dichte_Polygon_Name"].mode(dropna=True)
        polygon_name = haeufigster_polygon.iloc[0] if not haeufigster_polygon.empty else None
    
    # Passenden Dichtewert aus geladenen / manuell eingegebenen Daten wählen
    if polygon_name:
        eintrag = next((p for p in alle_dichten if p.get("name") == polygon_name), None)
    else:
        eintrag = alle_dichten[0] if alle_dichten else None
    
    # Dichtewerte einlesen (zentrale Quelle für HPA & MoNa)
    if eintrag:
        dichtewerte = {
            "Dichte_Polygon_Name": eintrag.get("name", polygon_name or "manuell"),
            "Ortsdichte": eintrag.get("ortsdichte"),
            "Ortsspezifisch": eintrag.get("ortspezifisch"),
            "Mindichte": eintrag.get("mindichte"),
            "Maxdichte": eintrag.get("maxdichte")
        }
    
    # 🧪 Optionales Debugging (auskommentieren bei Bedarf)
    # st.write("📊 Dichtewerte (gültig):", dichtewerte)
    bonus_methode = st.session_state.get("bonus_methode", "hpa")

    # ------------------------------------------------------------
    # 💶 Bonusabrechnung – zwei Methoden: HPA oder MoNa
    # ------------------------------------------------------------
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
        p_min = dichtewerte.get("Mindichte")
        p_max = dichtewerte.get("Maxdichte")
        
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
