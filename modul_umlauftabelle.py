# =====================================================================================================
# modul_umlauftabelle.py – Funktionen zur Berechnung und Anzeige von Umlauf- und TDS-Daten
# =====================================================================================================

import pandas as pd
import streamlit as st

# 🔧 Formatierungsfunktionen für Zeit- und Zahlenwerte
from modul_hilfsfunktionen import to_hhmmss, to_dezimalstunden, to_dezimalminuten, format_de

# 🔍 Berechnungsfunktionen für Kennzahlen und TDS-Werte
from modul_umlauf_kennzahl import berechne_umlauf_kennzahlen
from modul_berechnungen import berechne_tds_aus_werte, berechne_umlauf_auswertung


# -----------------------------------------------------------------------------------------------------
# 📊 Gesamtzeiten dynamisch anzeigen – abhängig vom gewählten Zeitformat
# -----------------------------------------------------------------------------------------------------
def show_gesamtzeiten_dynamisch(summe_leerfahrt, summe_baggern, summe_vollfahrt, summe_verklapp, summe_umlauf, 
                                 zeitformat="hh:mm:ss", title="Gesamtzeiten"):
    format_mapper = {
        "hh:mm:ss": to_hhmmss,
        "dezimalminuten": to_dezimalminuten,
        "dezimalstunden": to_dezimalstunden,
    }
    formatter = format_mapper.get(zeitformat, to_hhmmss)

    # 1. Zeile: gewähltes Format
    summen_format1 = [formatter(d) for d in [summe_leerfahrt, summe_baggern, summe_vollfahrt, summe_verklapp, summe_umlauf]]
    # 2. Zeile: zusätzlich immer in Dezimalstunden
    summen_stunden = [to_dezimalstunden(d) for d in [summe_leerfahrt, summe_baggern, summe_vollfahrt, summe_verklapp, summe_umlauf]]

    columns = ["Leerfahrt", "Baggern", "Vollfahrt", "Verklappen", "Umlauf"]
    gesamtzeiten_df = pd.DataFrame([summen_format1, summen_stunden], columns=columns)
    gesamtzeiten_df.index = ["", ""]
    return gesamtzeiten_df


# -----------------------------------------------------------------------------------------------------
# 📅 Erzeugt eine Umlauftabelle mit Zeitpunkten und Zeitdauern je Phase
# -----------------------------------------------------------------------------------------------------
def erstelle_umlauftabelle(umlauf_info_df, zeitzone, zeitformat):
    from modul_hilfsfunktionen import convert_timestamp, format_dauer

    # Strukturierte Spalten mit MultiIndex
    columns = pd.MultiIndex.from_tuples([
        ("Umlauf", "Nr."),
        ("Datum", ""),
        ("Leerfahrt", "Beginn"), ("Leerfahrt", "Dauer"),
        ("Baggern", "Beginn"), ("Baggern", "Dauer"),
        ("Vollfahrt", "Beginn"), ("Vollfahrt", "Dauer"),
        ("Verklappen", "Beginn"), ("Verklappen", "Dauer"),
        ("Umlauf", "Ende"), ("Umlauf", "Dauer")
    ])

    rows = []
    dauer_leerfahrt_list, dauer_baggern_list = [], []
    dauer_vollfahrt_list, dauer_verklapp_list, dauer_umlauf_list = [], [], []

    for _, row in umlauf_info_df.iterrows():
        # Zeitwerte sicher konvertieren (inkl. Zeitzone)
        def safe_ts(key):
            t = row.get(key)
            return convert_timestamp(pd.Timestamp(t) if pd.notnull(t) else None, zeitzone) if t else None

        # Zeitpunkte extrahieren
        anzeige_start_leerfahrt = safe_ts("Start Leerfahrt")
        anzeige_start_baggern = safe_ts("Start Baggern")
        anzeige_start_vollfahrt = safe_ts("Start Vollfahrt")
        anzeige_start_verklapp = safe_ts("Start Verklappen/Pump/Rainbow")
        anzeige_ende_umlauf = safe_ts("Ende")

        # Zeitdifferenzen berechnen (je Phase)
        dauer_leerfahrt = (anzeige_start_baggern - anzeige_start_leerfahrt) if anzeige_start_baggern and anzeige_start_leerfahrt else None
        dauer_baggern = (anzeige_start_vollfahrt - anzeige_start_baggern) if anzeige_start_vollfahrt and anzeige_start_baggern else None
        dauer_vollfahrt = (anzeige_start_verklapp - anzeige_start_vollfahrt) if anzeige_start_verklapp and anzeige_start_vollfahrt else None
        dauer_verklapp = (anzeige_ende_umlauf - anzeige_start_verklapp) if anzeige_ende_umlauf and anzeige_start_verklapp else None
        dauer_umlauf = (anzeige_ende_umlauf - anzeige_start_leerfahrt) if anzeige_ende_umlauf and anzeige_start_leerfahrt else None

        # Dauer-Listen befüllen
        if dauer_leerfahrt: dauer_leerfahrt_list.append(dauer_leerfahrt)
        if dauer_baggern: dauer_baggern_list.append(dauer_baggern)
        if dauer_vollfahrt: dauer_vollfahrt_list.append(dauer_vollfahrt)
        if dauer_verklapp: dauer_verklapp_list.append(dauer_verklapp)
        if dauer_umlauf: dauer_umlauf_list.append(dauer_umlauf)

        # Zeile für Tabelle aufbauen
        rows.append([
            row.get("Umlauf", "-"),
            anzeige_start_leerfahrt.strftime("%d.%m.%Y") if anzeige_start_leerfahrt else "-",
            anzeige_start_leerfahrt.strftime("%H:%M:%S") if anzeige_start_leerfahrt else "-",
            format_dauer(dauer_leerfahrt, zeitformat),
            anzeige_start_baggern.strftime("%H:%M:%S") if anzeige_start_baggern else "-",
            format_dauer(dauer_baggern, zeitformat),
            anzeige_start_vollfahrt.strftime("%H:%M:%S") if anzeige_start_vollfahrt else "-",
            format_dauer(dauer_vollfahrt, zeitformat),
            anzeige_start_verklapp.strftime("%H:%M:%S") if anzeige_start_verklapp else "-",
            format_dauer(dauer_verklapp, zeitformat),
            anzeige_ende_umlauf.strftime("%H:%M:%S") if anzeige_ende_umlauf else "-",
            format_dauer(dauer_umlauf, zeitformat)
        ])

    df_alle_umlaeufe = pd.DataFrame(rows, columns=columns)

    return df_alle_umlaeufe, dauer_leerfahrt_list, dauer_baggern_list, dauer_vollfahrt_list, dauer_verklapp_list, dauer_umlauf_list


# -----------------------------------------------------------------------------------------------------
# ⏳ Gesamtzeiten über alle Umläufe zusammenfassen
# -----------------------------------------------------------------------------------------------------
def berechne_gesamtzeiten(dauer_leerfahrt_list, dauer_baggern_list, dauer_vollfahrt_list, dauer_verklapp_list, dauer_umlauf_list):
    return {
        "leerfahrt": sum(dauer_leerfahrt_list, pd.Timedelta(0)),
        "baggern":   sum(dauer_baggern_list, pd.Timedelta(0)),
        "vollfahrt": sum(dauer_vollfahrt_list, pd.Timedelta(0)),
        "verklapp":  sum(dauer_verklapp_list, pd.Timedelta(0)),
        "umlauf":    sum(dauer_umlauf_list, pd.Timedelta(0))
    }
# -----------------------------------------------------------------------------------------------------
# 📈 TDS-Tabelle erzeugen (inkl. manuelle Eingaben und Berechnungen)
# -----------------------------------------------------------------------------------------------------
def erzeuge_tds_tabelle(df, umlauf_info_df, schiffsparameter, strategie, pf, pw, pb, zeitformat, epsg_code):
    daten = []          # Formatierte Werte mit Einheiten (für Anzeige)
    daten_export = []   # Rohdaten (für Excel-Export ohne Formatierung)
    kumuliert_feststoff = 0  # Zwischenspeicher für aufsummiertes Feststoffvolumen

    df_manuell = st.session_state.get("df_manuell", pd.DataFrame())

    # ⏰ Timestamp-Spalte normieren (falls z.B. aus CSV/Excel eingelesen)
    if not df_manuell.empty:
        if not pd.api.types.is_datetime64_any_dtype(df_manuell["timestamp_beginn_baggern"]):
            df_manuell["timestamp_beginn_baggern"] = pd.to_datetime(df_manuell["timestamp_beginn_baggern"], errors="coerce")
        if df_manuell["timestamp_beginn_baggern"].dt.tz is None:
            df_manuell["timestamp_beginn_baggern"] = df_manuell["timestamp_beginn_baggern"].dt.tz_localize("UTC", ambiguous="NaT")
        else:
            df_manuell["timestamp_beginn_baggern"] = df_manuell["timestamp_beginn_baggern"].dt.tz_convert("UTC")

    # 🔁 Umläufe durchlaufen
    for _, row in umlauf_info_df.iterrows():
        feststoff_manuell, proz = None, None
        row_time = pd.to_datetime(row.get("Start Baggern"), utc=True)

        # 🔍 Passende manuelle Eingabe suchen
        if not df_manuell.empty:
            treffer = df_manuell[df_manuell["timestamp_beginn_baggern"] == row_time]
            if not treffer.empty:
                feststoff_manuell = treffer.iloc[0].get("feststoff")
                proz = treffer.iloc[0].get("proz_wert")

        try:
            # Kontext: Zeitraum rund um den Umlauf
            t_start = pd.to_datetime(row["Start Leerfahrt"], utc=True) - pd.Timedelta(minutes=15)
            t_ende = pd.to_datetime(row["Ende"], utc=True) + pd.Timedelta(minutes=15)
            df_context = df[(df["timestamp"] >= t_start) & (df["timestamp"] <= t_ende)].copy()

            # Berechnung der TDS-Werte
            tds, werte, _, *_ = berechne_umlauf_auswertung(
                df_context, row, schiffsparameter, strategie, pf, pw, pb, zeitformat, epsg_code
            )

            # 🌊 Basiswerte extrahieren
            leer_masse = werte.get("Verdraengung Start")
            voll_masse = werte.get("Verdraengung Ende")
            diff_masse = voll_masse - leer_masse if None not in [leer_masse, voll_masse] else None

            leer_vol = werte.get("Ladungsvolumen Start")
            voll_vol = werte.get("Ladungsvolumen Ende")
            diff_vol = voll_vol - leer_vol if None not in [leer_vol, voll_vol] else None

            # ➕ Manuelle Ergänzung durch Eingabewerte
            if feststoff_manuell is not None and proz is not None and voll_vol is not None:
                gemisch = voll_vol - feststoff_manuell
                feststoff_gemisch = gemisch * (proz / 100)
                feststoff_volumen = feststoff_manuell + feststoff_gemisch
            else:
                gemisch = feststoff_gemisch = feststoff_volumen = None

            if feststoff_volumen is not None:
                kumuliert_feststoff += feststoff_volumen

            # 📋 Darstellungstabelle (mit Einheiten + Formatierung)
            zeile = [
                row["Umlauf"],
                format_de(leer_masse, 0) + " t",
                format_de(voll_masse, 0) + " t",
                format_de(diff_masse, 0) + " t",
                format_de(leer_vol, 0) + " m³",
                format_de(voll_vol, 0) + " m³",
                format_de(diff_vol, 0) + " m³",
                format_de(tds.get("ladungsdichte"), 2) + " t/m³",
                format_de(tds.get("feststoffkonzentration") * 100, 1) + " %" if tds.get("feststoffkonzentration") is not None else "-",
                format_de(tds.get("feststoffvolumen"), 0) + " m³",
                format_de(tds.get("feststoffmasse"), 0) + " t",
                format_de(feststoff_manuell, 0) + " m³" if feststoff_manuell else "-",
                format_de(gemisch, 0) + " m³" if gemisch else "-",
                format_de(proz, 1) + " %" if proz else "-",
                format_de(feststoff_gemisch, 0) + " m³" if feststoff_gemisch else "-",
                format_de(feststoff_volumen, 0) + " m³" if feststoff_volumen else "-",
                format_de(kumuliert_feststoff, 0) + " m³" if kumuliert_feststoff else "-"
            ]
        except Exception:
            # Fehlerhafte Zeile abfangen
            zeile = [row["Umlauf"]] + ["-"] * 17

        daten.append(zeile)

        # Exportzeile mit reinen Werten (für Excel)
        zeile_export = [
            row["Umlauf"],
            leer_masse,
            voll_masse,
            diff_masse,
            leer_vol,
            voll_vol,
            diff_vol,
            tds.get("ladungsdichte"),
            tds.get("feststoffkonzentration") * 100 if tds.get("feststoffkonzentration") is not None else None,
            tds.get("feststoffvolumen"),
            tds.get("feststoffmasse"),
            feststoff_manuell,
            gemisch,
            proz,
            feststoff_gemisch,
            feststoff_volumen,
            kumuliert_feststoff
        ]
        daten_export.append(zeile_export)

    # Strukturierter MultiIndex für Anzeige und Export
    spalten = pd.MultiIndex.from_tuples([
        ("Umlauf", "Nr."),
        ("Ladungsmasse", "leer"),
        ("Ladungsmasse", "voll"),
        ("Ladungsmasse", "Differenz"),
        ("Ladungsvolumen", "leer"),
        ("Ladungsvolumen", "voll"),
        ("Ladungsvolumen", "Differenz"),
        ("Ladungs-", "dichte"),
        ("Feststoff", "Konzentr."),
        ("Feststoff", "Volumen"),
        ("Feststoff", "Masse"),
        ("Ladung", "Feststoff"),
        ("Gemisch", ""),
        ("Zentrifuge", ""),
        ("Feststoff", "Gemisch"),
        ("Feststoff", "Gesamt"),
        ("Feststoff", "Kumuliert")
    ])

    # 🧾 Rückgabe: Anzeige- und Exporttabelle
    return (
        pd.DataFrame(daten, columns=spalten),
        pd.DataFrame(daten_export, columns=spalten)
    )
# -----------------------------------------------------------------------------------------------------
# 📈 Tabelle - Verbringstelle mit TDS-Feststoffgesamtwert
# -----------------------------------------------------------------------------------------------------
def erzeuge_verbring_tabelle(df, umlauf_info_df, transformer):
    import streamlit as st

    rows = []

    spalten = pd.MultiIndex.from_tuples([
        ("Umlauf", "Nr."),
        ("Verbringstelle", ""),
        ("Schiff", ""),
        ("Verbringbeginn", "Datum"),
        ("Verbringbeginn", "Uhrzeit"),
        ("Verbringbeginn", "Pos. Nord"),
        ("Verbringbeginn", "Pos. Ost"),
        ("Verbringende", "Datum"),
        ("Verbringende", "Uhrzeit"),
        ("Verbringende", "Pos. Nord"),
        ("Verbringende", "Pos. Ost"),
        ("Laderaumvolumen", "m³"),
        ("Bodenklasse", "")
    ])

    # TDS-Tabelle aus Session laden, falls vorhanden
    df_tds_export = st.session_state.get("tds_df_export", pd.DataFrame())
    tds_available = not df_tds_export.empty and ("Umlauf", "Nr.") in df_tds_export.columns

    # 🔁 Jeder Umlauf einzeln
    for _, row in umlauf_info_df.iterrows():
        try:
            umlauf_nr = int(row["Umlauf"]) if pd.notna(row["Umlauf"]) else "-"
            t_start = pd.to_datetime(row["Start Leerfahrt"], utc=True)
            t_ende = pd.to_datetime(row["Ende"], utc=True)
            df_umlauf = df[(df["timestamp"] >= t_start) & (df["timestamp"] <= t_ende)].copy()

            # Schiffsnamen extrahieren
            schiffsnamen = df_umlauf["Schiffsname"].dropna().unique() if "Schiffsname" in df_umlauf.columns else []
            schiff = schiffsnamen[0] if len(schiffsnamen) > 0 else "-"

            # Nur Verbringen (Status 4–6) mit Polygon
            df_verb = df_umlauf[df_umlauf["Status"].isin([4, 5, 6]) & df_umlauf["Polygon_Name"].notna()]
            if df_verb.empty:
                continue

            df_verb = df_verb.sort_values("timestamp")
            polygon = df_verb["Polygon_Name"].iloc[0]
            ts_start = df_verb.iloc[0]["timestamp"]
            ts_end = df_verb.iloc[-1]["timestamp"]

            def ts_parts(ts):
                return ts.strftime("%d.%m.%Y"), ts.strftime("%H:%M:%S")

            # Koordinaten konvertieren
            try:
                lon_start, lat_start = transformer.transform(df_verb.iloc[0]["RW_Schiff"], df_verb.iloc[0]["HW_Schiff"])
                lon_end, lat_end = transformer.transform(df_verb.iloc[-1]["RW_Schiff"], df_verb.iloc[-1]["HW_Schiff"])
            except:
                lat_start = lon_start = lat_end = lon_end = "-"

            # Volumen-Fallback, falls kein TDS vorhanden
            voll_vol = df_verb["Feststoffvolumen"].dropna().max()

            # Bodenklasse via Dichte aus TDS (falls vorhanden)
            dichte = None
            if tds_available:
                tds_zeile = df_tds_export[df_tds_export[("Umlauf", "Nr.")] == umlauf_nr]
                if not tds_zeile.empty:
                    dichte = tds_zeile.iloc[0][("Ladungs-", "dichte")]
            klasse = "Schlick" if pd.notna(dichte) and dichte < 1.6 else "Sand" if pd.notna(dichte) else "-"

            # TDS-Gesamtwert
            laderaumvolumen = "-"
            if tds_available:
                tds_zeile = df_tds_export[df_tds_export[("Umlauf", "Nr.")] == umlauf_nr]
                if not tds_zeile.empty:
                    wert = tds_zeile.iloc[0][("Feststoff", "Gesamt")]
                    if pd.notna(wert):
                        laderaumvolumen = f"{int(round(wert, 0)):,}".replace(",", ".")
                elif voll_vol:
                    laderaumvolumen = f"{int(round(voll_vol, 0)):,}".replace(",", ".")

            # Zeile zur Tabelle hinzufügen
            rows.append([
                umlauf_nr,
                polygon,
                schiff,
                *ts_parts(ts_start),
                f"{lat_start:.6f}" if isinstance(lat_start, (float, int)) else "-",
                f"{lon_start:.6f}" if isinstance(lon_start, (float, int)) else "-",
                *ts_parts(ts_end),
                f"{lat_end:.6f}" if isinstance(lat_end, (float, int)) else "-",
                f"{lon_end:.6f}" if isinstance(lon_end, (float, int)) else "-",
                laderaumvolumen,
                klasse
            ])

        except Exception as e:
            print(f"⚠️ Fehler bei Umlauf {row.get('Umlauf')}: {e}")
            continue

    return pd.DataFrame(rows, columns=spalten)
