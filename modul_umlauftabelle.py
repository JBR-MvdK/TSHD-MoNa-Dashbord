# =====================================================================================================
# modul_umlauftabelle.py – Funktionen zur Berechnung und Anzeige von Umlauf- und TDS-Daten
# =====================================================================================================

import pandas as pd
import streamlit as st

# 🔧 Formatierungsfunktionen für Zeit- und Zahlenwerte
from modul_hilfsfunktionen import to_hhmmss, to_dezimalstunden, to_dezimalminuten, format_de, convert_timestamp, format_dauer, uhrzeit_spaltenlabel

# 🔍 Berechnungsfunktionen für Kennzahlen und TDS-Werte
from modul_umlauf_kennzahl import berechne_umlauf_kennzahlen
from modul_berechnungen import berechne_tds_aus_werte, berechne_umlauf_auswertung, berechne_mittlere_gemischdichte

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

    # ✅ panels brauchen hh:mm:ss (für Anzeige in den KPI-Panels)
    summen_format1 = [to_hhmmss(d) for d in [summe_leerfahrt, summe_baggern, summe_vollfahrt, summe_verklapp, summe_umlauf]]

    # 📊 Zeile 2: immer zusätzlich in Dezimalstunden
    summen_stunden = [to_dezimalstunden(d) for d in [summe_leerfahrt, summe_baggern, summe_vollfahrt, summe_verklapp, summe_umlauf]]

    columns = ["Leerfahrt", "Baggern", "Vollfahrt", "Verklappen", "Umlauf"]
    gesamtzeiten_df = pd.DataFrame([summen_format1, summen_stunden], columns=columns)
    gesamtzeiten_df.index = ["", ""]  # ohne Indexbeschriftung

    return gesamtzeiten_df



# -----------------------------------------------------------------------------------------------------
# 📅 Erzeugt eine Umlauftabelle mit Zeitpunkten und Zeitdauern je Phase
# -----------------------------------------------------------------------------------------------------
def erstelle_umlauftabelle(umlauf_info_df, zeitzone, zeitformat):

    # ✅ Jetzt ist zeitzone verfügbar
    uhrzeit_label = uhrzeit_spaltenlabel(zeitzone)

    # Strukturierte Spalten mit MultiIndex
    columns = pd.MultiIndex.from_tuples([
        ("Umlauf", "Nr."),
        ("Datum", ""),
        ("Leerfahrt", uhrzeit_label), ("Leerfahrt", "Dauer"),
        ("Baggern", uhrzeit_label), ("Baggern", "Dauer"),
        ("Vollfahrt", uhrzeit_label), ("Vollfahrt", "Dauer"),
        ("Verklappen", uhrzeit_label), ("Verklappen", "Dauer"),
        ("Umlauf", uhrzeit_label), ("Umlauf", "Dauer")
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
    # 📊 Ergebnislisten initialisieren
    daten = []          # Für Anzeige in der UI (formatiert)
    daten_export = []   # Für CSV-Export (Rohdaten)
    kumuliert_abrechnung = 0  # Zwischensumme für abrechnungsrelevantes Volumen

    # 📉 Durchschnittliche Gemischdichte je Umlauf berechnen (nur informativ)
    df_mittelwerte = berechne_mittlere_gemischdichte(df, umlauf_info_df, debug=False)

    # 📥 Manuelle Feststoffdaten aus Session holen (zuvor per Editor geladen/eingegeben)
    df_manuell = st.session_state.get("df_manuell", pd.DataFrame())
    # Optional: Berechnung entfernen, da Berechnung jetzt direkt in berechne_umlauf_auswertung integriert ist
    # df_manuell = berechne_feststoff_manuell(df_manuell)

    # 💾 Wieder speichern – falls andere Module darauf zugreifen
    st.session_state["df_manuell"] = df_manuell

    # ➕ Neue kumulierte Summe für Feststoffmengen
    kumuliert_feststoff_summe = 0.0

    # 🔁 Jeder einzelne Umlauf wird nun ausgewertet
    for _, row in umlauf_info_df.iterrows():
        try:
            # 🕒 Kontextzeitfenster erweitern (15 min Puffer vorne & hinten)
            t_start = pd.to_datetime(row["Start Leerfahrt"], utc=True) - pd.Timedelta(minutes=15)
            t_ende = pd.to_datetime(row["Ende"], utc=True) + pd.Timedelta(minutes=15)
            df_context = df[(df["timestamp"] >= t_start) & (df["timestamp"] <= t_ende)].copy()

            # 📊 Zentrale Berechnung des Umlaufs – TDS + manuelle Daten bereits integriert
            tds, werte, *_, dichtewerte, _ = berechne_umlauf_auswertung(
                df_context, row, schiffsparameter, strategie, pf, pw, pb, zeitformat, epsg_code,
                df_manuell=df_manuell
            )

            # 🧾 Manuelle Werte aus dem zurückgegebenen tds-Dictionary holen
            feststoff_manuell = tds.get("feststoff_manuell")
            proz = tds.get("proz")
            voll_vol = tds.get("voll_volumen")
            feststoff_gemisch = tds.get("feststoff_gemisch")
            feststoff_volumen = tds.get("feststoff_gesamt")
            gemisch = voll_vol - feststoff_manuell if voll_vol and feststoff_manuell else None

            # ➕ Kumulierte Summe berechnen (wird manuell aufsummiert)
            if pd.notna(feststoff_volumen):
                kumuliert_feststoff_summe += feststoff_volumen
            kumuliert_feststoff = kumuliert_feststoff_summe

            # 🔢 Weitere technische Kennwerte
            ortsdichte = dichtewerte.get("Ortsdichte")
            leer_masse = werte.get("Verdraengung Start")
            voll_masse = werte.get("Verdraengung Ende")
            diff_masse = voll_masse - leer_masse if None not in [leer_masse, voll_masse] else None
            leer_vol = werte.get("Ladungsvolumen Start")
            voll_vol = werte.get("Ladungsvolumen Ende")
            diff_vol = voll_vol - leer_vol if None not in [leer_vol, voll_vol] else None

            # 💰 Abrechnungsvolumen kumulieren
            abrechnungsvolumen = tds.get("abrechnungsvolumen")
            if abrechnungsvolumen is not None:
                kumuliert_abrechnung += abrechnungsvolumen

            # 📋 Formatierte Zeile für UI
            zeile = [
                row["Umlauf"],
                format_de(leer_masse, 0) + " t",
                format_de(voll_masse, 0) + " t",
                format_de(diff_masse, 0) + " t",
                format_de(leer_vol, 0) + " m³",
                format_de(voll_vol, 0) + " m³",
                format_de(diff_vol, 0) + " m³",
                format_de(tds.get("ladungsdichte"), 3) + " t/m³",
                format_de(ortsdichte, 3) + " t/m³" if ortsdichte else "-",
                format_de(tds.get("feststoffkonzentration") * 100, 1) + " %" if tds.get("feststoffkonzentration") is not None else "-",
                format_de(tds.get("feststoffvolumen"), 0) + " m³",
                format_de(tds.get("feststoffmasse"), 0) + " t",
                format_de(tds.get("abrechnungsfaktor"), 3) if tds.get("abrechnungsfaktor") is not None else "-",
                format_de(abrechnungsvolumen, 0) + " m³" if abrechnungsvolumen else "-",
                format_de(kumuliert_abrechnung, 0) + " m³",
                format_de(feststoff_manuell, 0) + " m³" if feststoff_manuell else "-",
                format_de(gemisch, 0) + " m³" if gemisch else "-",
                format_de(proz, 1) + " %" if proz else "-",
                format_de(feststoff_gemisch, 0) + " m³" if feststoff_gemisch else "-",
                format_de(feststoff_volumen, 0) + " m³" if feststoff_volumen else "-",
                format_de(kumuliert_feststoff, 0) + " m³"
            ]

            # 📤 Export-Zeile (Rohdaten, ohne Formatierung)
            zeile_export = [
                row["Umlauf"], leer_masse, voll_masse, diff_masse,
                leer_vol, voll_vol, diff_vol,
                tds.get("ladungsdichte"),
                ortsdichte,
                tds.get("feststoffkonzentration") * 100 if tds.get("feststoffkonzentration") is not None else None,
                tds.get("feststoffvolumen"),
                tds.get("feststoffmasse"),
                tds.get("abrechnungsfaktor"),
                abrechnungsvolumen,
                kumuliert_abrechnung,
                feststoff_manuell,
                gemisch,
                proz,
                feststoff_gemisch,
                feststoff_volumen,
                kumuliert_feststoff
            ]

        except Exception as e:
            # ❌ Fehlerbehandlung für einzelne Umläufe (z. B. fehlende Daten)
            st.error(f"❌ Fehler bei Umlauf {row.get('Umlauf')}: {e}")
            zeile = [row["Umlauf"]] + ["-"] * 20
            zeile_export = [row["Umlauf"]] + [None] * 20

        # ➕ Ergebnisse zur Gesamtliste hinzufügen
        daten.append(zeile)
        daten_export.append(zeile_export)

    # 🧾 Spaltenstruktur mit MultiIndex (für Anzeige & Export)
    spalten = pd.MultiIndex.from_tuples([
        ("Umlauf", "Nr."),
        ("Ladungsmasse", "leer"),
        ("Ladungsmasse", "voll"),
        ("Ladungsmasse", "Differenz"),
        ("Ladungsvolumen", "leer"),
        ("Ladungsvolumen", "voll"),
        ("Ladungsvolumen", "Differenz"),
        ("Ladungs-", "dichte"),
        ("Ortdichte", ""),  
        ("Feststoff", "Konzentr."),
        ("Feststoff", "Volumen"),
        ("Feststoff", "Masse"),
        ("Abrechnung", "Faktor"),
        ("Abrechnung", "Volumen"),
        ("Abrechnung", "kumuliert"),
        ("Ladung", "Feststoff"),
        ("Gemisch", ""),
        ("Zentrifuge", ""),
        ("Feststoff", "Gemisch"),
        ("Feststoff", "Gesamt"),
        ("Feststoff", "Kumuliert")
    ])

    # ✅ Rückgabe der fertigen Tabellen
    return (
        pd.DataFrame(daten, columns=spalten),
        pd.DataFrame(daten_export, columns=spalten)
    )



# -----------------------------------------------------------------------------------------------------
# 📈 Tabelle - Verbringstelle mit TDS-Feststoffgesamtwert
# -----------------------------------------------------------------------------------------------------
def erzeuge_verbring_tabelle(df, umlauf_info_df, transformer, zeitzone, status_col="Status"):
    uhrzeit_label = uhrzeit_spaltenlabel(zeitzone)

    rows = []

    spalten = pd.MultiIndex.from_tuples([
        ("Umlauf", "Nr."),
        ("Verbringstelle", ""),
        ("Schiff", ""),
        ("Verbringbeginn", "Datum"),
        ("Verbringbeginn", uhrzeit_label),
        ("Verbringbeginn", "Pos. Nord"),
        ("Verbringbeginn", "Pos. Ost"),
        ("Verbringende", "Datum"),
        ("Verbringende", uhrzeit_label),
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

            # 👉 Aktive Status-Spalte bestimmen
            aktive_status_col = status_col
            if status_col == "Status" and "Status_neu" in df_umlauf.columns:
                aktive_status_col = "Status_neu"

            # Gültige Werte je nach Statusfeld
            gueltige_statuswerte = [4, 5, 6] if aktive_status_col == "Status" else ["Verbringen"]

            # ✅ Nur Verbringpunkte mit Polygon und gültigem Status
            df_verb = df_umlauf[
                df_umlauf[aktive_status_col].isin(gueltige_statuswerte) &
                df_umlauf["Polygon_Name"].notna()
            ]

            if df_verb.empty:
                continue

            df_verb = df_verb.sort_values("timestamp")
            polygon = df_verb["Polygon_Name"].iloc[0]
            ts_start = df_verb.iloc[0]["timestamp"]
            ts_end = df_verb.iloc[-1]["timestamp"]

            def ts_parts(ts):
                if pd.isna(ts):
                    return "-", "-"
                ts_conv = convert_timestamp(pd.to_datetime(ts), zeitzone)
                return ts_conv.strftime("%d.%m.%Y"), ts_conv.strftime("%H:%M:%S")

            # Koordinaten transformieren
            try:
                lon_start, lat_start = transformer.transform(df_verb.iloc[0]["RW_Schiff"], df_verb.iloc[0]["HW_Schiff"])
                lon_end, lat_end = transformer.transform(df_verb.iloc[-1]["RW_Schiff"], df_verb.iloc[-1]["HW_Schiff"])
            except:
                lat_start = lon_start = lat_end = lon_end = "-"

            # Volumen (Backup)
            voll_vol = df_verb["Feststoffvolumen"].dropna().max()

            # Bodenklasse über Dichte
            dichte = None
            if tds_available:
                tds_zeile = df_tds_export[df_tds_export[("Umlauf", "Nr.")] == umlauf_nr]
                if not tds_zeile.empty:
                    dichte = tds_zeile.iloc[0][("Ladungs-", "dichte")]

            klasse = "Schlick" if pd.notna(dichte) and dichte < 1.6 else "Sand" if pd.notna(dichte) else "-"

            # Gesamtvolumen aus TDS oder Fallback
            laderaumvolumen = "-"
            if tds_available and not tds_zeile.empty:
                wert = tds_zeile.iloc[0][("Feststoff", "Gesamt")]
                if pd.notna(wert):
                    laderaumvolumen = f"{int(round(wert, 0)):,}".replace(",", ".")
            elif voll_vol:
                laderaumvolumen = "-"

            # 👉 Zeile zur Tabelle hinzufügen
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


