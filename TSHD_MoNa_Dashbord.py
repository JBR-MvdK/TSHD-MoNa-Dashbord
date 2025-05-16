# === 🔧 BASIS-MODULE (Standardbibliothek & Basisdatenverarbeitung) ===
import json            # Verarbeitung von JSON-Dateien (z. B. Laden von Konfigurationsdaten oder Schiffseinstellungen)
import os              # Datei- und Verzeichnisoperationen (z. B. Pfadprüfungen, Dateiexistenz etc.)
import pandas as pd    # Tabellenverarbeitung und Datenanalyse (z. B. Filtern, Gruppieren, Zeitreihen)
import numpy as np     # Mathematische Funktionen (z. B. Mittelwerte, NaN-Erkennung, Array-Operationen)
import pytz            # Zeitzonen-Verarbeitung und Konvertierung von Timestamps
import traceback       # Lesbare Fehler-Stacks für Debugging und Fehleranalyse
from datetime import datetime  # Verarbeitung und Formatierung von Zeitstempeln

# === 📊 UI & VISUALISIERUNG ===
import plotly.graph_objects as go    # Interaktive Diagramme (z. B. für Zeitverläufe, Tiefenprofile)
import streamlit as st               # Haupt-Framework zur Erstellung der interaktiven Web-Oberfläche

# === 🌍 GEODATEN & GEOMETRIE ===
from shapely.geometry import Point   # Geometrische Punkt-Objekte für Koordinatenberechnungen, z. B. Punkt-in-Polygon

# === 🧩 EIGENE MODULE (Modularisierte Funktionsbausteine für einzelne Analyseschritte) ===

# 🟡 Import und Berechnung technischer TDS-Parameter (z. B. Volumen, Masse, Konzentration aus Rohdaten)
from modul_tshd_hpa_import import konvertiere_hpa_ascii  # Konvertierung von HPA-Dateien in MoNa-Format
from modul_tshd_mona_import import parse_mona, berechne_tds_parameter

# 🟦 Segmentierung der Fahrtdaten in einzelne Umläufe (Statuslogik, Phasenübergänge, Status_neu)
from modul_umlaeufe import nummeriere_umlaeufe, extrahiere_umlauf_startzeiten, berechne_status_neu

# ⚓ Erkennung der aktiven Baggerseite (automatische Analyse BB/SB auf Basis Sensoraktivität)
from modul_baggerseite import erkenne_baggerseite

# 🌐 Automatische EPSG-Code-Erkennung (zur Georeferenzierung der Positionsdaten)
from modul_koordinatenerkennung import erkenne_koordinatensystem

# 📥 XML-Import von Baggerfeld-Definitionen (Polygon-Grenzen und Solltiefen je Feld)
from modul_baggerfelder_xml_import import parse_baggerfelder

# 📏 Berechnung von Solltiefen entlang der Fahrtstrecke auf Basis der Baggerfeld-Zuordnung
from modul_solltiefe_tshd import berechne_solltiefe_fuer_df

# 🚢 Streckenberechnung nach Betriebsstatus (z. B. Strecke während Leerfahrt, Baggerfahrt etc.)
from modul_strecken import berechne_strecken

# 📊 Berechnung von Kennzahlen pro Umlauf (z. B. Menge, Masse, Dauer, Dichtekennwerte)
from modul_umlauf_kennzahl import berechne_umlauf_kennzahlen

# 🎯 Strategie zur Erkennung von Start-/Endzeitpunkten je Parameter (z. B. Ladungsvolumen, Verdrängung)
from modul_startend_strategie import berechne_start_endwerte

# 🧰 Allgemeine Hilfsfunktionen (Zeitumrechnung, Datenprüfung, Spaltenwahl, Formatierung etc.)
from modul_hilfsfunktionen import (
    convert_timestamp,                # Umwandlung von Timestamps inkl. Zeitzonenbehandlung
    erkenne_datenformat,              # Erkennung des Dateiformats (z. B. MoNa oder HPA)
    erkenne_schiff_aus_dateiname,     # Extraktion des Schiffnamens aus Dateinamen
    format_dauer, sichere_dauer, sichere_zeit,  # Sichere Berechnung und Anzeige von Zeitdifferenzen
    format_de, format_time,           # Formatierung von Zeit- und Zahlenwerten für Anzeige
    get_spaltenname,                  # Dynamischer Zugriff auf BB/SB-Spaltennamen je nach Seite
    lade_schiffsparameter,            # Laden der JSON-Schiffsparameterdatei
    plot_x,                           # Erzeugung der Zeitachse für Plotly-Grafiken
    pruefe_werte_gegen_schiffsparameter,  # Überprüfung der Rohdaten auf Plausibilität anhand Schiffsdaten
    setze_schiff_manuell_wenn_notwendig,  # Ermöglicht manuelle Auswahl des Schiffs, falls automatischer Abgleich fehlschlägt
    split_by_gap,                     # Segmentierung der Daten bei zeitlichen Lücken
    to_dezimalstunden, to_dezimalminuten, to_hhmmss  # Zeitformatkonvertierung in verschiedene Darstellungen
)

# === 🪟 STREAMLIT UI-PANELS (visuelle Komponenten für Status, Kennzahlen, Strecken etc.) ===
from modul_ui_panels import (
    feld_panel_template,
    panel_template,
    status_panel_template_mit_strecke,
    strecken_panel_template,
    dichte_panel_template,
    zeige_bagger_und_verbringfelder,   # Einfärbung von Bagger- und Verbringfeldern auf der Karte
    zeige_baggerwerte_panels,          # Anzeigen von Baggerparametern wie Volumen, Masse, Dichte
    zeige_statuszeiten_panels,         # Visualisierung der Phasenzeiten je Umlauf
    zeige_statuszeiten_panels_mit_strecke,  # Erweiterte Darstellung inkl. zurückgelegter Strecken
    zeige_strecken_panels              # Anzeige der Strecken je Phase (Leerfahrt, Baggern, Vollfahrt, Verklappung)
)

# === 📈 Interaktive Zeitreihengrafiken zur Prozessdatendarstellung
from modul_prozessgrafik import zeige_baggerkopftiefe_grafik, zeige_prozessgrafik_tab

# 🔄 Auswertung: Aufenthaltsdauer in Polygonen (z. B. je Baggerfeld)
from modul_polygon_auswertung import berechne_punkte_und_zeit

# 🧮 Erweiterte Berechnung für TDS-/Betriebskennzahlen pro Umlauf
from modul_berechnungen import berechne_umlauf_auswertung

# 🗂️ Erzeugung der Tabellenansichten für Statuszeiten und TDS-Kennzahlen
from modul_umlauftabelle import (
    berechne_gesamtzeiten,        # Aufsummieren der Phasen über alle Umläufe
    erzeuge_tds_tabelle,          # Tabelle mit berechneten TDS-Werten pro Umlauf
    erzeuge_verbring_tabelle,     # Verbringstellen je Umlauf + Export für WSA
    erstelle_umlauftabelle,       # Erzeugung der Detailtabelle aller Umläufe
    show_gesamtzeiten_dynamisch   # Gesamtdauer je Phase
)

# 🗺️ Visualisierung der Fahrtspuren + Baggerfelder auf der Karte
from modul_karten import plot_karte, zeige_umlauf_info_karte

# 📥 Tagesberichte aus Excel importieren (z. B. Feststoffmengen)
from modul_daten_import import lade_excel_feststoffdaten



#==============================================================================================================================
# 🔵 Start der Streamlit App
#==============================================================================================================================

# Streamlit Seiteneinstellungen (Titel und Layout)
st.set_page_config(page_title="TSHD Monitoring – Baggerdatenanalyse", layout="wide")
st.title("🚢 TSHD Monitoring – Baggerdatenanalyse")

# === 📂 Datei-Upload mit automatischer Format-Erkennung ===
with st.sidebar.expander("📂 Dateien hochladen / auswählen", expanded=True):
    uploaded_files = st.file_uploader(
        "Datendateien (.txt) auswählen", 
        type=["txt"], 
        accept_multiple_files=True,
        key="daten_upload"
    )

    upload_status = st.empty()

    datenformat = None  # Initialisierung

    if uploaded_files:
        datenformat = erkenne_datenformat(uploaded_files)

        if datenformat in ["MoNa", "HPA"]:
            st.info(f"📄 Erkanntes Datenformat: **{datenformat}**")
        else:
            st.warning("❓ Format konnte nicht eindeutig erkannt werden.")
            datenformat = st.radio("🔄 Format manuell wählen:", ["MoNa", "HPA"], horizontal=True)

    uploaded_xml_files = st.file_uploader(
        "Baggerfeldgrenzen (XML)", 
        type=["xml"], 
        accept_multiple_files=True,
        key="xml_upload"
    )
    
    xml_status = st.empty()

   
#==============================================================================================================================
# 🔵 Berechnungs-Parameter in der Sidebar
#==============================================================================================================================

# --- Dichteparameter Setup ---
with st.sidebar.expander("⚙️ Setup - Berechnungen"):
    pf = st.number_input(
        "Feststoffdichte pf [t/m³]",
        min_value=2.0, max_value=3.0,
        value=2.643, step=0.001, format="%.3f"
    )
    pw = st.number_input(
        "Wasserdichte pw [t/m³]",
        min_value=1.0, max_value=1.1,
        value=1.025, step=0.001, format="%.3f"
    )

    pb = st.number_input(
        "Angenommene Bodendichte pb [t/m³]",
        min_value=1.0, max_value=2.5,
        value=1.98, step=0.01, format="%.2f"
    )

    min_fahr_speed = st.number_input(
        "Mindestgeschwindigkeit für Leerfahrt (knt)",
        min_value=0.0, max_value=2.0,
        value=0.30, step=0.01, format="%.2f"
    )

    min_vollfahrt_dauer_min = st.number_input(
        "⏱ Minimale Dauer für gültige Vollfahrtphase nach Status 2→3 (Minuten)",
        min_value=0.1,
        max_value=10.0,
        value=6.0,
        step=0.1,
        format="%.1f"
    )

    nutze_gemischdichte = st.radio(
        "Gemischdichte für Startzeitpunkt Baggern und Vollfahrt verwenden?",
        ["Ja", "Nein"],
        index=0,
        horizontal=True
    ) == "Ja"

    dichte_grenze = st.number_input(
        "🔎 Grenzwert Gemischdichte für Ende Baggern",
        min_value=1.0, max_value=1.2, step=0.01, value=1.10,
        format="%.2f"
    )
    
    rueckblick_minute = st.slider(
        "⏱️ Rückblickzeit für Dichteprüfung (Minuten)", 
        min_value=0.0, max_value=4.0, step=0.5, value=2.0
    )

    nutze_schiffstrategie = st.radio(
        "Start-/Endstrategien aus Schiffsdaten verwenden?",
        ["Ja", "Nein"],
        horizontal=True
    ) == "Ja"

# --- Solltiefen-Setup ---
with st.sidebar.expander("📉 Setup - Solltiefen"):
    solltiefe_slider = st.number_input(
        "**Solltiefe (m)** \n_Nur falls keine XML mit gültiger Tiefe geladen wird_", 
        min_value=-30.0, max_value=0.0, 
        value=0.0, step=0.1, format="%.2f"
    )
    toleranz_oben = st.slider(
        "Obere Toleranz (m)", min_value=0.0, max_value=2.0, value=0.5, step=0.1
    )
    toleranz_unten = st.slider(
        "Untere Toleranz (m)", min_value=0.0, max_value=2.0, value=0.5, step=0.1
    )

# Platzhalter für Erkennungsinfo Koordinatensystem
koordsys_status = st.sidebar.empty()
#==============================================================================================================================
# 🔵 MoNa-Daten verarbeiten und vorbereiten
#==============================================================================================================================
if uploaded_files:
    try:
        if datenformat == "MoNa":
            df, rw_max, hw_max = parse_mona(uploaded_files)
        elif datenformat == "HPA":
            hpa_files = konvertiere_hpa_ascii(uploaded_files)
            df, rw_max, hw_max = parse_mona(hpa_files)

    except Exception as e:
        st.error(f"Fehler beim Laden der Daten: {e}")
        st.text(traceback.format_exc())

    else:
        # ✅ Dieser Block wird nur ausgeführt, wenn KEIN Fehler aufgetreten ist

        # Erfolgsmeldung anzeigen
        upload_status.success(f"{len(df)} Zeilen aus {len(uploaded_files)} Datei(en) geladen")

        # TDS-Parameter berechnen
        df = berechne_tds_parameter(df, pf, pw)

        # Versuche, Schiff automatisch aus Dateinamen zu erkennen
        erkannter_schiffname = erkenne_schiff_aus_dateiname(uploaded_files)
        if erkannter_schiffname:
            df["Schiffsname"] = erkannter_schiffname
            
        # Koordinatensystem erkennen
        if not df.empty:
            proj_system, epsg_code, auto_erkannt = erkenne_koordinatensystem(
                df, st=st, status_element=koordsys_status
            )
            
        df, schiffsnamen = setze_schiff_manuell_wenn_notwendig(df, st)

        # Basisinfos: Schiffe & Zeitraum
        schiffe = df["Schiffsname"].dropna().unique()
        if len(schiffe) == 1:
            schiffsname_text = f"**Schiff:** **{schiffe[0]}**"
        elif len(schiffe) > 1:
            schiffsname_text = f"**Schiffe im Datensatz:** {', '.join(schiffe)}"
        else:
            schiffsname_text = "Keine bekannten Schiffsnamen gefunden."

        zeit_min = df["timestamp"].min()
        zeit_max = df["timestamp"].max()

        zeitraum_text = "Zeitraum: Unbekannt" if pd.isnull(zeit_min) else f"{zeit_min.strftime('%d.%m.%Y %H:%M:%S')} – {zeit_max.strftime('%d.%m.%Y %H:%M:%S')} UTC"
        
        st.markdown(f"{schiffsname_text}  \n**Zeitraum:** {zeitraum_text}")

        # Schiffsparameter laden und prüfen
        schiffsparameter = lade_schiffsparameter()

        if schiffsparameter:
            if len(schiffsnamen) == 1:
                st.sidebar.success(f"Schiffsparameter geladen ({len(schiffsparameter)} Schiffe) – {schiffsnamen[0]}")
            else:
                st.sidebar.success(f"Schiffsparameter geladen ({len(schiffsparameter)} Schiffe)")
        else:
            st.sidebar.info("ℹ️ Keine Schiffsparameter-Datei gefunden oder leer.")

        # Plausibilitätsprüfung, falls ein Schiff eindeutig erkannt wurde
        if len(schiffsnamen) == 1:
            schiff = schiffsnamen[0]
            df, fehlerhafte = pruefe_werte_gegen_schiffsparameter(df, schiff, schiffsparameter)
            if fehlerhafte:
                for spalte, anzahl in fehlerhafte:
                    st.warning(f"⚠️ {anzahl} Werte in **{spalte}** außerhalb gültiger Grenzen für **{schiff}** – wurden entfernt.")

#==============================================================================================================================
# 🔵 # 📋 Schiffsparameter bearbeiten und speichern
#==============================================================================================================================

        # 📋 Schiffsparameter bearbeiten und speichern

        with st.sidebar.expander("🔧 Schiffsparameter bearbeiten", expanded=False):
        
            if len(schiffe) == 1:
                schiff = schiffe[0]
                st.markdown(f"**Aktives Schiff:** {schiff}")
        
                # 🧭 Baggerseite wählen
                aktuelle_param = schiffsparameter.get(schiff, {})
                gespeicherte_seite = aktuelle_param.get("Baggerseite", "BB")
                erkannte_seite = erkenne_baggerseite(df)
        
                seite_auswahl = st.selectbox(
                    "🧭 Baggerseite wählen",
                    options=["Auto", "BB", "SB", "BB+SB"],
                    index=["Auto", "BB", "SB", "BB+SB"].index(gespeicherte_seite)
                )
                seite = erkannte_seite if seite_auswahl == "Auto" else seite_auswahl
        

                # 📋 Bearbeitbare Schiffswerte
                alle_spalten = [
                    'Tiefgang_vorne', 'Tiefgang_hinten', 'Verdraengung',
                    'Tiefe_Kopf_BB', 'Tiefe_Kopf_SB',
                    'Gemischdichte_BB', 'Gemischdichte_SB',
                    'Gemischgeschwindigkeit_BB', 'Gemischgeschwindigkeit_SB',
                    'Fuellstand_BB_vorne', 'Fuellstand_SB_vorne',
                    'Fuellstand_BB_mitte', 'Fuellstand_SB_mitte',
                    'Fuellstand_SB_hinten', 'Fuellstand_BB_hinten',
                    'Masse_leeres_Schiff',
                    'Ladungsvolumen',
                    'Druck_vor_Baggerpumpe_BB', 'Druck_vor_Baggerpumpe_SB',
                    'Druck_hinter_Baggerpumpe_BB', 'Druck_hinter_Baggerpumpe_SB',
                    'Druck_Druckwasserpumpe_BB', 'Druck_Druckwasserpumpe_SB',
                ]
        
                daten = []
                for spalte in alle_spalten:
                    min_val = aktuelle_param.get(spalte, {}).get("min", None)
                    max_val = aktuelle_param.get(spalte, {}).get("max", None)
                    daten.append({"Spalte": spalte, "min": min_val, "max": max_val})
                df_edit = pd.DataFrame(daten)
        
                edited_df = st.data_editor(
                    df_edit,
                    column_config={
                        "Spalte": st.column_config.Column(disabled=True),
                        "min": st.column_config.NumberColumn(format="%.3f"),
                        "max": st.column_config.NumberColumn(format="%.3f"),
                    },
                    use_container_width=True,
                    hide_index=True
                )
        

                if st.button("💾 Speichern für dieses Schiff"):
                    # Bestehende Strategie und Baggerseite sichern
                    bestehende_daten = schiffsparameter.get(schiff, {})
                    strategie_alt = bestehende_daten.get("StartEndStrategie", {})
                    bagger_alt = seite_auswahl
                
                    # Neue Parametertabelle aus der Editor-Tabelle
                    neue_param = {
                        row["Spalte"]: {
                            "min": row["min"] if pd.notnull(row["min"]) else None,
                            "max": row["max"] if pd.notnull(row["max"]) else None
                        }
                        for _, row in edited_df.iterrows()
                    }
                
                    # Alles kombinieren und speichern
                    schiffsparameter[schiff] = {
                        **neue_param,
                        "Baggerseite": bagger_alt,
                        "StartEndStrategie": strategie_alt
                    }
                
                    with open("schiffsparameter.json", "w", encoding="utf-8") as f:
                        json.dump(schiffsparameter, f, indent=2, ensure_ascii=False)
                
                    st.success("✅ Parameter gespeichert.")
            else:
                st.info("Bitte lade MoNa-Daten mit eindeutigem Schiffsname.")
                

            # --- Erweiterung: Zeige die Start-/End-Strategie, wenn vorhanden ---
            if len(schiffe) == 1:
                schiff = schiffe[0]
                aktuelle_param = schiffsparameter.get(schiff, {})
            
                if "StartEndStrategie" in aktuelle_param:
                    st.markdown("#### ⚙️ Start-/Endwert-Strategien")
            
                    for parameter, strategie in aktuelle_param["StartEndStrategie"].items():
                        start = strategie.get("Start", "Standard (Statuswechsel)")
                        ende = strategie.get("Ende", "Standard (Statuswechsel)")
            
                        st.markdown(f"""
                        - **{parameter}**  
                          Startwert: _{start}_  
                          Endwert: _{ende}_
                        """)
                else:
                    st.info("ℹ️ Keine speziellen Start-/End-Strategien definiert (Standardverhalten aktiv).")
            
            else:
                st.info("ℹ️ Kein eindeutiges Schiff erkannt – Start-/Endwert-Strategien werden nicht geladen.")



#==============================================================================================================================
# 🔵 Filterleiste und Grundeinstellungen
#==============================================================================================================================

        # ------------------------------------------------------------------------------------------------
        # 🔢 1. Vier Spalten nebeneinander: Startwert, Umlaufauswahl, Zeitformat, Zeitzone
        # ------------------------------------------------------------------------------------------------
        st.markdown("---")
        col_startwert, col_umlauf, col_zeitformat, col_zeitzone = st.columns([1, 1, 1, 1])
        
        # 👈 Auswahl: Startwert der Umlaufzählung (z. B. ab 1 oder höher beginnen)
        with col_startwert:
            startwert = st.number_input("🔢 Startwert Umlaufzählung", min_value=1, step=1, value=1)
        
        
        # ------------------------------------------------------------------------------------------------
        # 🔄 2. Berechne die Umläufe aus dem Datensatz (Leerfahrt → Baggern → Verbringen ...)
        #     → nutzt Statuswechsel, Geschwindigkeit, Gemischdichte etc.
        # ------------------------------------------------------------------------------------------------
        umlauf_info_df = extrahiere_umlauf_startzeiten(
            df,
            startwert=startwert,
            min_fahr_speed=min_fahr_speed,
            nutze_gemischdichte=nutze_gemischdichte,
            seite=seite,
            dichte_grenze=dichte_grenze,
            rueckblick_minute=rueckblick_minute,
            min_vollfahrt_dauer_min=min_vollfahrt_dauer_min
        )
        
        # 🧪 Kopie zur späteren parallelen Verwendung
        umlauf_info_df_all = umlauf_info_df.copy()
        
        # 📊 Ergänze df um Status_neu-Spalte: Kennzeichnet z. B. 'Leerfahrt', 'Baggern' ...
        df = berechne_status_neu(df, umlauf_info_df)
        
        
        # ------------------------------------------------------------------------------------------------
        # 📅 3. Ergänze Spalten für spätere Visualisierungen (Start-/Endzeit als eigene Spalten)
        # ------------------------------------------------------------------------------------------------
        if not umlauf_info_df.empty:
            if "Start Leerfahrt" in umlauf_info_df.columns:
                umlauf_info_df["start"] = umlauf_info_df["Start Leerfahrt"]
            if "Ende" in umlauf_info_df.columns:
                umlauf_info_df["ende"] = umlauf_info_df["Ende"]
        
        
        # ------------------------------------------------------------------------------------------------
        # 🔁 4. Auswahlbox: Welcher einzelne Umlauf soll betrachtet werden?
        # ------------------------------------------------------------------------------------------------
        with col_umlauf:
            umlauf_options = ["Alle"]
            if not umlauf_info_df.empty and "Umlauf" in umlauf_info_df.columns:
                umlauf_options += [int(u) for u in umlauf_info_df["Umlauf"]]
        
            # 🧠 Wenn Session-Flag aktiv ist, setze Auswahl automatisch auf "Alle"
            if st.session_state.get("bereit_fuer_berechnung", False):
                selected_index = 0
            else:
                selected_index = umlauf_options.index(
                    st.session_state.get("umlauf_auswahl", "Alle")
                ) if st.session_state.get("umlauf_auswahl", "Alle") in umlauf_options else 0
        
            # 📌 Auswahlfeld anzeigen
            umlauf_auswahl = st.selectbox(
                "🔁 Umlauf auswählen",
                options=umlauf_options,
                index=selected_index,
                key="umlauf_auswahl"
            )
        
        
        # ------------------------------------------------------------------------------------------------
        # ⏱️ 5. Formatierung für Zeitwerte: klassisch oder dezimal
        # ------------------------------------------------------------------------------------------------
        with col_zeitformat:
            zeitformat = st.selectbox(
                "🕒 Zeitformat",
                options=["hh:mm:ss", "dezimalminuten", "dezimalstunden"],
                index=1,
                format_func=lambda x: {
                    "hh:mm:ss": "hh:mm:ss",
                    "dezimalminuten": "Dezimalminuten",
                    "dezimalstunden": "Dezimalstunden"
                }[x]
            )
        
        
        # ------------------------------------------------------------------------------------------------
        # 🌍 6. Zeitzone für Anzeige wählen (UTC oder Lokalzeit)
        # ------------------------------------------------------------------------------------------------
        with col_zeitzone:
            zeitzone = st.selectbox(
                "🌍 Zeitzone",
                ["UTC", "Lokal (Europe/Berlin)"],
                index=0
            )



        # ------------------------------------------------------------------------------------------------
        # 🕓 7. Zeitzonen prüfen und ggf. auf UTC setzen
        # ------------------------------------------------------------------------------------------------
        # Wenn die Zeitstempel noch keine Zeitzone haben (naiv), → auf UTC setzen.
        if df["timestamp"].dt.tz is None:
            df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
        
        # ------------------------------------------------------------------------------------------------
        # 🔁 8. Umläufe im DataFrame nummerieren
        # ------------------------------------------------------------------------------------------------
        # → wichtig, da danach die Zuordnung zu 'Umlauf' für Filterung & Anzeige erfolgt
        df = nummeriere_umlaeufe(df, startwert=startwert)
        
        # ------------------------------------------------------------------------------------------------
        # 🧾 9. Liste der verfügbaren Umläufe vorbereiten (z. B. für Dropdown-Auswahl)
        # ------------------------------------------------------------------------------------------------
        verfuegbare_umlaeufe = df["Umlauf"].dropna().unique()
        verfuegbare_umlaeufe.sort()
        
        # ------------------------------------------------------------------------------------------------
        # 🔍 10. Initialisierung für Einzelanzeige: gewählte Zeile + zugehörige Kennzahlen
        # ------------------------------------------------------------------------------------------------
        kennzahlen = {}  # Leeres Dictionary – wird nur bei Auswahl eines Umlaufs gefüllt
        row = None       # Platzhalter für gewählte Umlaufzeile (eine einzelne Zeile aus der Tabelle)
        
        if umlauf_auswahl != "Alle":
            # 👉 Hole die Zeile, die dem gewählten Umlauf entspricht
            zeile = umlauf_info_df[umlauf_info_df["Umlauf"] == umlauf_auswahl]
            if not zeile.empty:
                row = zeile.iloc[0]  # 🎯 Erste und einzige Treffer-Zeile extrahieren
                # 📊 Kennzahlen aus dieser Zeile und dem gesamten df berechnen (Volumen, Masse etc.)
                kennzahlen = berechne_umlauf_kennzahlen(row, df)
        
        # ------------------------------------------------------------------------------------------------
        # 📊 11 Zeitbereich für Detailgrafiken setzen (z. B. Prozessgrafik, Tiefe etc.)
        # ------------------------------------------------------------------------------------------------
        # Erweitere den Bereich großzügig um +/- 15 Minuten für Kontextanzeige
        if row is not None:
            t_start = pd.to_datetime(row["Start Leerfahrt"], utc=True) - pd.Timedelta(minutes=15)
            t_ende = pd.to_datetime(row["Ende"], utc=True) + pd.Timedelta(minutes=15)
        
            # 👉 Filtere den DataFrame für genau diesen Zeitraum → df_context = Fokusbereich
            df_context = df[(df["timestamp"] >= t_start) & (df["timestamp"] <= t_ende)].copy()
        else:
            # Fallback: kein Umlauf ausgewählt → ganzen Datensatz verwenden
            df_context = df.copy()

     
#==============================================================================================================================
# 🔵 Baggerseite erkennen und auswählen
#==============================================================================================================================

# Auswahl der Baggerseite (Auto / BB / SB / BB+SB)

        seite_auswahl = locals().get("seite_auswahl", "Auto")
        erkannte_seite = locals().get("erkannte_seite", "BB")
        seite = erkannte_seite if seite_auswahl == "Auto" else seite_auswahl

        

#==============================================================================================================================
# 🔵 Rechtswerte normalisieren (nur für UTM)
#==============================================================================================================================

        def normalisiere_rechtswert(wert):
            if proj_system == "UTM" and auto_erkannt and wert > 30_000_000:
                return wert - int(epsg_code[-2:]) * 1_000_000
            return wert

        # Anwenden auf relevante Spalten
        for col in ["RW_Schiff", "RW_BB", "RW_SB"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].apply(normalisiere_rechtswert)

#==============================================================================================================================
# 🔵 XML-Dateien (Baggerfelder) einlesen
#==============================================================================================================================

        baggerfelder = []
        if uploaded_xml_files:
            try:
                for uploaded_xml in uploaded_xml_files:
                    try:
                        felder = parse_baggerfelder(uploaded_xml, epsg_code)
                        baggerfelder.extend(felder)
                    except Exception as e:
                        st.sidebar.warning(f"{uploaded_xml.name} konnte nicht geladen werden: {e}")
                if baggerfelder:
                    xml_status.success(f"{len(baggerfelder)} Baggerfelder geladen")
                else:
                    xml_status.info("Keine Baggerfelder erkannt.")
            except Exception as e:
                xml_status.error(f"Fehler beim Verarbeiten der XML-Dateien: {e}")

#==============================================================================================================================
# 🔵 Solltiefe auf Basis der Baggerfelder berechnen
#==============================================================================================================================

        df = berechne_solltiefe_fuer_df(
            df, baggerfelder, seite, epsg_code, toleranz_oben, toleranz_unten, solltiefe_slider
        )

        # Solltiefe analysieren und Herkunft feststellen
        if "Solltiefe_Aktuell" in df.columns and df["Solltiefe_Aktuell"].notnull().any():
            gueltige = df["Solltiefe_Aktuell"].dropna()
            if (gueltige == gueltige.iloc[0]).all():
                solltiefe_wert = gueltige.iloc[0]
            else:
                solltiefe_wert = "variabel"
        else:
            solltiefe_wert = None

        if solltiefe_wert is None:
            solltiefe_herkunft = "nicht definiert"
        elif solltiefe_wert == solltiefe_slider:
            solltiefe_herkunft = "manuelle Eingabe"
        elif solltiefe_wert == "variabel":
            solltiefe_herkunft = "aus XML - mehrere Werte"
        else:
            solltiefe_herkunft = "aus XML-Datei übernommen"

        # Ausgabe vorbereiten
        if isinstance(solltiefe_wert, (int, float)):
            anzeige_solltiefe = f"{solltiefe_wert:.2f}"
            anzeige_m = " m"
        elif solltiefe_wert == "variabel":
            anzeige_solltiefe = "variabel"
            anzeige_m = ""
        else:
            anzeige_solltiefe = " "
            anzeige_m = ""


        # ------------------------------------------------------------------------------------------------------------------
        # 🎨 HTML-Styling für KPI-Panels
        # ------------------------------------------------------------------------------------------------------------------
        st.markdown("""
        <style>
            .big-num {font-size: 2.5rem; font-weight: bold;}
            .panel {background: #f4f8fc; border-radius: 16px; padding: 20px; margin-bottom: 1.5rem;}
            .caption {font-size: 1rem; color: #555;}
            .highlight {font-weight: bold; font-size: 1.2rem; color: #0353a4;}
        </style>
        """, unsafe_allow_html=True)
        
        # 👉 Auswahlzeile vorbereiten, falls ein einzelner Umlauf gewählt ist
        zeile = umlauf_info_df[umlauf_info_df["Umlauf"] == umlauf_auswahl] if umlauf_auswahl != "Alle" else pd.DataFrame()

        df_ungefiltert = df.copy()

        
        

#==============================================================================================================================
# 🔵 Tabs definieren
#==============================================================================================================================

# Tabs für die verschiedenen Visualisierungen
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "🗺️ Karte",
            "📊 Prozessdaten",
            "🌊 Tiefenprofil",
            "🧾 Umlauftabellen",
            "🧾 Umlauftabellen - TDS",
            "🧪 Debug",
            "💾 Export"
        ])
      
#==============================================================================================================================
# Tab 1 - Übersichtskarten 
#==============================================================================================================================

        

        from pyproj import Transformer
        
        with tab1:
            transformer = Transformer.from_crs(epsg_code, "EPSG:4326", always_xy=True)
        
            if umlauf_auswahl != "Alle":
                zeile = umlauf_info_df[umlauf_info_df["Umlauf"] == umlauf_auswahl]
        
                if not zeile.empty:
                    row = zeile.iloc[0]
        
                    # 👇 Nur ein einziger Aufruf hier!
                    df, _ = zeige_umlauf_info_karte(umlauf_auswahl, zeile, zeitzone, epsg_code, df)
        
                    # Kennzahlen, Strecken etc. berechnen
                    tds_werte, werte, kennzahlen, strecken, strecke_disp, dauer_disp, debug_info, bagger_namen, verbring_namen = berechne_umlauf_auswertung(
                        df, row, schiffsparameter, strategie, pf, pw, pb, zeitformat, epsg_code
                    )
                    
                    
                    # Berechnung der Zeiten aus Polygonauswertung
                    bagger_df = berechne_punkte_und_zeit(df, statuswert=2)
                    bagger_zeiten = bagger_df["Zeit_Minuten"].to_dict()
                    
                    verbring_df = berechne_punkte_und_zeit(df, statuswert=4)
                    verbring_zeiten = verbring_df["Zeit_Minuten"].to_dict()
                    
                # --------------------------------------------------------------------------------------------------------------------
                # 📌 Anzeige Bagger- und Verbringfelder in Panel-Stil
                # --------------------------------------------------------------------------------------------------------------------                   
                    
                    zeige_bagger_und_verbringfelder(
                        bagger_namen=bagger_namen,
                        verbring_namen=verbring_namen,
                        df=df,
                        baggerfelder=baggerfelder  # ❗️wichtig!
                    )

                     
  
            # Kartenansicht vorbereiten
            zeit_suffix = "UTC" if zeitzone == "UTC" else "Lokal"
            col1, col2 = st.columns(2)
  
        # -------------------------------------------------------------------------------------------------------------------------
        # Darstellung der Kartenansichten in zwei Spalten (links = Baggern, rechts = Verbringen)
        # -------------------------------------------------------------------------------------------------------------------------
        
            # -------------------------------------------------------------------------------------------------------------------------
            # Linke Karte: Darstellung der Baggerstelle (Status 2)
            # -------------------------------------------------------------------------------------------------------------------------
            with col1:
                # Karte für Status 2 (Baggern) erstellen

                fig, df_status2, df_456 = plot_karte(
                    df=df,
                    transformer=transformer,
                    seite=seite,
                    status2_label="Status 2 (Baggern)",
                    tiefe_spalte="Abs_Tiefe_Kopf_BB" if seite in ["BB", "BB+SB"] else "Abs_Tiefe_Kopf_SB",
                    mapbox_center={"lat": 53.5, "lon": 8.2},
                    zeitzone=zeitzone,
                    zeit_suffix=zeit_suffix,
                    baggerfelder=baggerfelder
                )
                # Wenn Status 2-Daten vorhanden sind → Zoome auf den ersten Punkt

                if not df_status2.empty and not df_456.empty:
                    first_latlon = transformer.transform(df_status2.iloc[0]["RW_Schiff"], df_status2.iloc[0]["HW_Schiff"])
                    last_latlon = transformer.transform(df_456.iloc[-1]["RW_Schiff"], df_456.iloc[-1]["HW_Schiff"])
                
                    fig.update_layout(
                        mapbox_center={"lat": first_latlon[1], "lon": first_latlon[0]},
                        mapbox_zoom=13
                    )
                elif df_status2.empty:
                    st.info("Keine Daten mit Status 2 verfügbar.")
                elif df_456.empty:
                    st.info("Keine letzten Punkte für Status 4-6 verfügbar.")

            
                # Überschrift und Karte darstellen
                #st.markdown("#### Baggerstelle")
                st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True}, key="karte_baggerstelle")

            
            
            # -------------------------------------------------------------------------------------------------------------------------
            # Rechte Karte: Darstellung der Verbringstelle (Status 4, 5, 6)
            # -------------------------------------------------------------------------------------------------------------------------
            with col2:
                # Karte für Status 4/5/6 (Verbringen) erstellen
                fig, df_status2, df_456 = plot_karte(
                    df=df,
                    transformer=transformer,
                    seite=seite,
                    status2_label="Status 2 (Baggern)",
                    tiefe_spalte="Abs_Tiefe_Kopf_BB" if seite in ["BB", "BB+SB"] else "Abs_Tiefe_Kopf_SB",
                    mapbox_center={"lat": 53.5, "lon": 8.2},
                    zeitzone=zeitzone,
                    zeit_suffix=zeit_suffix,
                    baggerfelder=baggerfelder
                )
                # Wenn Status 4/5/6-Daten vorhanden sind → Zoome auf den ersten Punkt

                if not df_456.empty:
                    first_latlon = transformer.transform(df_456.iloc[0]["RW_Schiff"], df_456.iloc[0]["HW_Schiff"])
                    last_latlon = transformer.transform(df_456.iloc[-1]["RW_Schiff"], df_456.iloc[-1]["HW_Schiff"])
                    fig.update_layout(
                        mapbox_center={"lat": last_latlon[1], "lon": last_latlon[0]},
                        mapbox_zoom=13
                    )
                else:
                    st.info("Keine Daten mit Status 4, 5 oder 6 verfügbar.")

            
                # Überschrift und Karte darstellen
                #st.markdown("#### Verbringstelle")
                st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True}, key="karte_verbringstelle")


                
            # ----------------------------------------------------------------------------------------------------------------------
            # 📍 Streckenanzeige pro Umlauf
            # ----------------------------------------------------------------------------------------------------------------------
            
            if kennzahlen: 
                st.markdown("#### Strecken im Umlauf")               
                zeige_strecken_panels(
                    strecke_disp["leerfahrt"], strecke_disp["baggern"], strecke_disp["vollfahrt"],
                    strecke_disp["verbringen"], strecke_disp["gesamt"],
                    dauer_disp["leerfahrt"], dauer_disp["baggern"], dauer_disp["vollfahrt"],
                    dauer_disp["verbringen"], dauer_disp["umlauf"],
                    strecken_panel_template
                )

#==============================================================================================================================
# Tab 2 - Diagramm Prozessdaten
#==============================================================================================================================

        
        with tab2:
            st.markdown("#### 📈 Umlaufgrafik – Prozessdaten")
        
            if umlauf_auswahl != "Alle":
                # Hole die Zeile zum gewählten Umlauf
                row_df = umlauf_info_df[umlauf_info_df["Umlauf"] == umlauf_auswahl]
        
                if not row_df.empty:
                    row = row_df.iloc[0]
        
                    # Hole Strategie und führe Auswertung durch
                    
                    if nutze_schiffstrategie:
                        strategie = schiffsparameter.get(schiff, {}).get("StartEndStrategie", {})
                    else:
                        strategie = {
                            "Verdraengung": {"Start": None, "Ende": None},
                            "Ladungsvolumen": {"Start": None, "Ende": None}
                        }

                    tds_werte, werte, kennzahlen, strecken, strecke_disp, dauer_disp, debug_info, bagger_namen, verbring_namen = berechne_umlauf_auswertung(
                        df, row, schiffsparameter, strategie, pf, pw, pb, zeitformat, epsg_code
                    )

        
                # ----------------------------------------------------------------------------------------------------------------------
                # 📦 Baggerdaten anzeigen: Masse, Volumen, Feststoffe, Bodenvolumen, Dichten
                # ----------------------------------------------------------------------------------------------------------------------
                    zeige_baggerwerte_panels(kennzahlen, tds_werte, zeitzone, pw, pf, pb, panel_template, dichte_panel_template)
                    
                # ----------------------------------------------------------------------------------------------------------------------
                # 📦 Baggerdaten als Diagramm
                # ----------------------------------------------------------------------------------------------------------------------                    
                    zeige_prozessgrafik_tab(df_context, zeitzone, row, schiffsparameter, schiff, werte, seite, plot_key="prozessgrafik_tab2")

                # ----------------------------------------------------------------------------------------------------------------------
                # 📊 Zeitliche Phasen anzeigen (Leerfahrt, Baggern und Strecken)
                # ----------------------------------------------------------------------------------------------------------------------
                    zeige_statuszeiten_panels_mit_strecke(row, zeitzone, zeitformat, strecken=strecke_disp, panel_template=status_panel_template_mit_strecke)
        
        
                else:
                    st.warning("⚠️ Kein Datensatz zum gewählten Umlauf gefunden.")
        
            else:
                st.info("Bitte einen konkreten Umlauf auswählen.")


# ==============================================================================================================================
# Tab 3 - Diagramm Tiefe Baggerkopf (Modularisiert)
# ==============================================================================================================================
       
        with tab3:
            st.markdown("#### Baggerkopftiefe")
            if umlauf_auswahl != "Alle":
                zeige_baggerkopftiefe_grafik(
                    df,
                    zeitzone,
                    seite,
                    solltiefe=solltiefe_slider if solltiefe_wert is None else None,
                    toleranz_oben=toleranz_oben,
                    toleranz_unten=toleranz_unten
                )

        
            else:
                st.info("Bitte einen konkreten Umlauf auswählen.")

#==============================================================================================================================
# Tab 4 - Umlauftabelle - gesamt 
#==============================================================================================================================


        with tab4:
            st.markdown("#### Auflistung aller Umläufe")
        
            if not umlauf_info_df.empty:
                # ✅ Extrahiere ALLE Umlauf-Startzeiten (unabhängig von Filtersicht)
                #umlauf_info_df_all = extrahiere_umlauf_startzeiten(df, startwert=startwert).copy()
        
                # 📅 Erzeuge Tabelle mit einzelnen Umläufen und ihren Zeitabschnitten
                df_umlaeufe, list_leer, list_bagg, list_voll, list_verk, list_umlauf = erstelle_umlauftabelle(
                    umlauf_info_df, zeitzone, zeitformat
                )
        
                # ⏱️ Berechne aufaddierte Gesamtzeiten
                gesamtzeiten = berechne_gesamtzeiten(list_leer, list_bagg, list_voll, list_verk, list_umlauf)
        
                # 🧾 Zeige Tabellen für Umläufe und Gesamtzeiten
                df_gesamt = show_gesamtzeiten_dynamisch(
                    gesamtzeiten["leerfahrt"], gesamtzeiten["baggern"],
                    gesamtzeiten["vollfahrt"], gesamtzeiten["verklapp"],
                    gesamtzeiten["umlauf"], zeitformat=zeitformat
                )
                st.dataframe(df_umlaeufe, use_container_width=True, hide_index=True)
                st.markdown("#### Aufsummierte Dauer")
                st.dataframe(df_gesamt, use_container_width=True, hide_index=True)
        
                
            else:
                st.info("⚠️ Es wurden keine vollständigen Umläufe erkannt.")
          
# ======================================================================================================================
# # Tab 5 - Umlauftabelle - TDS 
# ======================================================================================================================

        # Dieser Tab dient der Anzeige, Eingabe und Berechnung von TDS-Kennzahlen pro Umlauf
        
        with tab5:
        
            st.markdown("#### TDS Berechnung pro Umlauf")
        
            if not umlauf_info_df.empty:
        
                # -------------------------------------------------------------------------------------------------------------
                # 📂 Importfunktion: Manuelle Feststoffdaten aus CSV oder Excel-Datei laden
                # -------------------------------------------------------------------------------------------------------------
                col_upload, col_export = st.columns([1, 1])
        
                with col_upload:
                    with st.expander("📂 Import von manuellen Feststoffwerten (CSV oder Excel)"):
                        uploaded_file = st.file_uploader(
                            label="",
                            type=["csv", "xlsx"],
                            key="upload_manuell",
                            help="CSV oder Excel mit: timestamp_beginn_baggern ODER Datum/Uhrzeit, Feststoff, Zentrifuge"
                        )
        
                        if uploaded_file:
        
                            # CSV-Import
                            if uploaded_file.name.endswith(".csv"):
                                df_csv = pd.read_csv(uploaded_file, parse_dates=["timestamp_beginn_baggern"])
                                if df_csv["timestamp_beginn_baggern"].dt.tz is None:
                                    df_csv["timestamp_beginn_baggern"] = df_csv["timestamp_beginn_baggern"].dt.tz_localize("Europe/Berlin").dt.tz_convert("UTC")
                                else:
                                    df_csv["timestamp_beginn_baggern"] = df_csv["timestamp_beginn_baggern"].dt.tz_convert("UTC")
                                merge_typ = "exact"
        
                            # Excel-Import
                            elif uploaded_file.name.endswith(".xlsx"):
                                df_csv = lade_excel_feststoffdaten(uploaded_file, zeitzone="Europe/Berlin")
                                merge_typ = "tolerant"
        
                            else:
                                st.warning("Nur CSV oder Excel-Dateien sind erlaubt.")
                                st.stop()
        
                            # Vorbereiten der Basisdaten für den Merge
                            df_basis = umlauf_info_df_all[["Umlauf", "Start Baggern"]].copy()
                            df_basis = df_basis.rename(columns={"Start Baggern": "timestamp_beginn_baggern"})
                            df_basis["timestamp_beginn_baggern"] = pd.to_datetime(df_basis["timestamp_beginn_baggern"], utc=True)
        
                            df_csv = df_csv[df_csv["timestamp_beginn_baggern"].notna()].copy()
                            df_csv["timestamp_beginn_baggern"] = pd.to_datetime(df_csv["timestamp_beginn_baggern"], utc=True)
        
                            df_basis = df_basis.sort_values("timestamp_beginn_baggern")
                            df_csv = df_csv.sort_values("timestamp_beginn_baggern")
        
                            # Merge je nach Typ (exakt oder tolerant)
                            if merge_typ == "exact":
                                df_merged = pd.merge(
                                    df_basis,
                                    df_csv.drop(columns=["Umlauf"], errors="ignore"),
                                    on="timestamp_beginn_baggern",
                                    how="left"
                                )
                            else:
                                df_merged = pd.merge_asof(
                                    df_basis,
                                    df_csv.drop(columns=["Umlauf"], errors="ignore"),
                                    on="timestamp_beginn_baggern",
                                    direction="nearest",
                                    tolerance=pd.Timedelta("5min")
                                )
        
                            # Eventuelle *_csv-Spalten mit echten Spalten kombinieren
                            if "feststoff_csv" in df_merged.columns:
                                df_merged["feststoff"] = df_merged["feststoff"].combine_first(df_merged["feststoff_csv"])
                            if "proz_wert_csv" in df_merged.columns:
                                df_merged["proz_wert"] = df_merged["proz_wert"].combine_first(df_merged["proz_wert_csv"])
        
                            # Warnung bei unzugeordneten Werten
                            anzahl_fehlend = df_merged[["feststoff", "proz_wert"]].isna().any(axis=1).sum()
                            if anzahl_fehlend > 0:
                                st.warning(f"⚠️ {anzahl_fehlend} Einträge konnten nicht zugeordnet werden.")
        
                            # Finalen DataFrame sichern
                            df_final = df_merged[["Umlauf", "timestamp_beginn_baggern", "feststoff", "proz_wert"]]
                            st.session_state["df_manuell"] = df_final
                            st.session_state["editor_alle_umlaeufe_generieren"] = True
                            st.success(f"📥 {df_csv.shape[0]} Einträge aus Datei geladen und gemerged.")
        
                # -------------------------------------------------------------------------------------------------------------
                # 🔄 Neuaufbau von df_manuell, falls neue Umläufe vorhanden sind
                # -------------------------------------------------------------------------------------------------------------
                neue_umlaeufe = set(umlauf_info_df_all["Umlauf"])
                vorhandene_umlaeufe = set(st.session_state.get("df_manuell", pd.DataFrame()).get("Umlauf", []))
        
                if neue_umlaeufe != vorhandene_umlaeufe:
                    df_manuell = umlauf_info_df_all[["Umlauf", "Start Baggern"]].copy()
                    df_manuell = df_manuell.rename(columns={"Start Baggern": "timestamp_beginn_baggern"})
                    df_manuell["feststoff"] = None
                    df_manuell["proz_wert"] = None
                    st.session_state["df_manuell"] = df_manuell

        
                # -------------------------------------------------------------------------------------------------------------
                # ✏️ Eingabeformular für manuelle Werte + Berechnung + Export
                # -------------------------------------------------------------------------------------------------------------
                with st.expander("✏️ Eingabe manueller Feststoffwerte und Berechnung der TDS-Tabelle"):
                
                
                    # Initialaufbau der manuell bearbeitbaren Tabelle, falls nicht vorhanden
                    if "df_manuell" not in st.session_state:
                        if "Start Baggern" in umlauf_info_df_all.columns:
                            df_manuell = umlauf_info_df_all[["Umlauf", "Start Baggern"]].copy()
                            df_manuell = df_manuell.rename(columns={"Start Baggern": "timestamp_beginn_baggern"})
                            df_manuell["feststoff"] = None
                            df_manuell["proz_wert"] = None
                            st.session_state["df_manuell"] = df_manuell
                        else:
                            st.warning("⚠️ 'Start Baggern' nicht vorhanden.")
                            st.stop()
                

                    # Formular zur Eingabe & Anzeige der manuellen Werte
                    with st.form("eingabe_und_berechnung_form"):
                    
                        df_editor = st.session_state["df_manuell"].copy()
                        df_editor_display = st.data_editor(
                            df_editor,
                            num_rows="dynamic",
                            use_container_width=True,
                            column_config={
                                "timestamp_beginn_baggern": st.column_config.DatetimeColumn("Start Baggern"),
                                "feststoff": st.column_config.NumberColumn("Ladung - Feststoff (m³)", format="%.0f"),
                                "proz_wert": st.column_config.NumberColumn("Zentrifuge (%)", format="%.1f")
                            },
                            hide_index=True
                        )
                    
                        # Session-Flag initialisieren (nur beim ersten Aufruf)
                        if "bereit_fuer_berechnung" not in st.session_state:
                            st.session_state["bereit_fuer_berechnung"] = False
                    
                        submitted = False
                    
                        # 👉 Auswahl aus Selectbox lesen
                        selected_umlauf = st.session_state.get("umlauf_auswahl", "Alle")
                    
                        # 🔄 Button-Logik je nach Auswahl
                        if selected_umlauf == "Alle":
                            submitted = st.form_submit_button("💾 Speichern + Berechnen + Exportieren")
                        else:
                            if not st.session_state.get("bereit_fuer_berechnung", False):
                                submitted = st.form_submit_button("⏳ Berechnung starten")
                                if submitted:
                                    st.session_state["bereit_fuer_berechnung"] = True
                                    st.rerun()
                            else:
                                submitted = st.form_submit_button("💾 Speichern + Berechnen + Exportieren")

                
                # 🔁 Nach der Formulareingabe
                if submitted:
                    # 🔄 Reset des Session-Flags für Doppel-Logik
                    st.session_state["bereit_fuer_berechnung"] = False
                
                    # 🔁 Übernahme der Eingabedaten aus dem Editor
                    st.session_state["df_manuell"] = df_editor_display.copy()
                
                    # 🔍 Lade Strategie aus Schiffsparametern oder nutze Standardwerte
                    if nutze_schiffstrategie:
                        strategie = schiffsparameter.get(schiffsnamen[0], {}).get("StartEndStrategie", {})
                    else:
                        strategie = {
                            "Verdraengung": {"Start": None, "Ende": None},
                            "Ladungsvolumen": {"Start": None, "Ende": None}
                        }

                
                    with st.spinner("Berechne TDS-Kennzahlen für alle Umläufe..."):
                        # 🔢 TDS-Berechnung für alle Umläufe → Anzeige & Export
                        df_tabelle, df_tabelle_export = erzeuge_tds_tabelle(
                            df, umlauf_info_df_all, schiffsparameter, strategie, pf, pw, pb, zeitformat, epsg_code
                        )
                        st.session_state["tds_df"] = df_tabelle
                        st.session_state["tds_df_export"] = df_tabelle_export  # ❗ wichtig für andere Tabellen
                
                        # 📁 Vorbereitung der Excel-Datei
                        import io
                        from datetime import datetime
                
                        now_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        excel_buffer = io.BytesIO()
                
                        # 🔧 Flache Spaltennamen für Export
                        df_export_flat = df_tabelle_export.copy()
                        spalten_flat = [" - ".join(col).strip() if isinstance(col, tuple) else col for col in df_export_flat.columns]
                        df_export_flat.columns = spalten_flat
                
                        # 📏 Einheiten-Zeile passend zu den Spalten
                        einheiten = [
                            "", "t", "t", "t", "m³", "m³", "m³", "t/m³", "t/m³", "%",
                            "m³", "t", "m³", "m³", "m³", "%", "m³", "m³", "m³"
                        ]
                
                        with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
                            # 📄 Blatt 1: TDS-Werte (Rohdaten)
                            sheetname = "TDS-Werte"
                            df_export_flat.to_excel(writer, sheet_name=sheetname, startrow=2, index=False, header=False)
                            worksheet = writer.sheets[sheetname]
                
                            # ➕ Kopfzeile & Einheiten manuell ergänzen
                            for col_num, header in enumerate(spalten_flat):
                                worksheet.write(0, col_num, header)
                            for col_num, einheit in enumerate(einheiten):
                                worksheet.write(1, col_num, einheit)
                
                            # 📄 Blatt 2: Anzeige-Tabelle (formatiert)
                            df_anzeige = st.session_state["tds_df"].copy()
                            df_anzeige.columns = [" - ".join(col).strip() if isinstance(col, tuple) else col for col in df_anzeige.columns]
                            df_anzeige.to_excel(writer, sheet_name="TDS-Anzeige", index=False)
                
                        # 🧠 Excel-Datei und CSV-Export in Session-State speichern
                        st.session_state["export_excel"] = excel_buffer.getvalue()
                        st.session_state["export_excel_filename"] = f"{now_str}_TDS_Tabelle.xlsx"
                
                        df_export = st.session_state["df_manuell"]
                        csv_data = df_export.to_csv(index=False).encode("utf-8")
                        st.session_state["export_ready"] = True
                        st.session_state["export_csv"] = csv_data
                        st.session_state["export_filename"] = f"{now_str}_manuell_feststoff.csv"

                
                # -------------------------------------------------------------------------------------------------------------
                # 💾 Downloadbuttons für CSV + Excel
                # -------------------------------------------------------------------------------------------------------------
                # ⬇️ CSV-Export: manuelle Feststoffdaten
                if st.session_state.get("export_ready"):
                    st.download_button(
                        label="⬇️ Manuelle Feststoffwerte als .csvV speichern",
                        data=st.session_state["export_csv"],
                        file_name=st.session_state["export_filename"],
                        mime="text/csv"
                    )
                    st.session_state["export_ready"] = False
                
                # 📋 Anzeige der TDS-Tabelle
                if "tds_df" in st.session_state:
                    st.dataframe((st.session_state["tds_df"]), use_container_width=True, hide_index=True)
                
                # ⬇️ Excel-Export der TDS-Tabelle
                if st.session_state.get("export_excel"):
                    st.download_button(
                        label="📥 TDS-Tabelle als .xlsx speichern",
                        data=st.session_state["export_excel"],
                        file_name=st.session_state["export_excel_filename"],
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.info("🔹 Noch keine TDS-Tabelle berechnet.")



            # ---------------------------------------------------------------------------------------------------------------------
            # Verbringstellen-Tabelle erzeugen und exportieren
            # ---------------------------------------------------------------------------------------------------------------------
            st.markdown("---")   
            st.markdown("#### Verbringstellen-Tabelle")
            import io
            from datetime import datetime        
            
            if not df.empty:
                # 🔁 Alle Umläufe, unabhängig von Auswahl
                df_verbring_tab = erzeuge_verbring_tabelle(
                    df_ungefiltert,
                    umlauf_info_df_all,
                    transformer,
                    zeitzone=zeitzone,  # oder z. B. st.session_state.get("zeitzone")
                    status_col="Status_neu"
                )

             
            
                if df_verbring_tab.empty:
                    st.warning("⚠️ Es wurden keine Verbringstellen erkannt. Stelle sicher, dass mindestens ein Polygonfeld vorhanden ist und Status 4/5/6 enthalten ist.")
                else:
                    # Anzeige der Tabelle
                    st.dataframe(df_verbring_tab, use_container_width=True, hide_index=True)
            
                    # ⬇️ Excel-Export mit MultiIndex
                    df_verbring_export = df_verbring_tab.copy()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    dateiname = f"Verbringstellen_WSA_{schiff}_{timestamp}.xlsx"
            
                    excel_buffer = io.BytesIO()
                    df_verbring_export.to_excel(excel_buffer, index=True)  # behält MultiIndex
                    excel_buffer.seek(0)
            
                    st.download_button(
                        label="📥 WSA Verbringtabelle als .xlsx speichern",
                        data=excel_buffer,
                        file_name=dateiname,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.info("Bitte zuerst Daten laden.")
 
# ======================================================================================================================
# TAB 6 – Numerische Auswertung Umlaufdaten: Panel-Templates für visuelle Darstellung
# ======================================================================================================================
        
        with tab6:

            if umlauf_auswahl != "Alle":
                row = umlauf_info_df[umlauf_info_df["Umlauf"] == umlauf_auswahl].iloc[0]
                
                if nutze_schiffstrategie:
                    strategie = schiffsparameter.get(schiff, {}).get("StartEndStrategie", {})
                else:
                    strategie = {
                        "Verdraengung": {"Start": None, "Ende": None},
                        "Ladungsvolumen": {"Start": None, "Ende": None}
                    }

                tds_werte, werte, kennzahlen, strecken, strecke_disp, dauer_disp, debug_info, bagger_namen, verbring_namen = berechne_umlauf_auswertung(
                    df, row, schiffsparameter, strategie, pf, pw, pb, zeitformat, epsg_code
                )


                # ----------------------------------------------------------------------------------------------------------------------
                # 📌 Anzeige Bagger- und Verbringfelder in Panel-Stil
                # ----------------------------------------------------------------------------------------------------------------------

                #st.markdown("#### Bagger- und Verbringfelder", unsafe_allow_html=True)
                
                bagger_felder_text = "<br>".join(sorted(bagger_namen)) if len(bagger_namen) > 0 else "-"
                verbring_felder_text = "<br>".join(sorted(verbring_namen)) if len(verbring_namen) > 0 else "-"


                zeige_bagger_und_verbringfelder(
                    bagger_namen=bagger_namen,
                    verbring_namen=verbring_namen,
                    df=df,
                    baggerfelder=baggerfelder  # ❗️wichtig!
                )

                
                # ----------------------------------------------------------------------------------------------------------------------
                # 📊 Zeitliche Phasen anzeigen (Leerfahrt, Baggern etc.)
                # ----------------------------------------------------------------------------------------------------------------------
                st.markdown("---")
                st.markdown("#### Statuszeiten im Umlauf", unsafe_allow_html=True)
                if kennzahlen:
                    zeige_statuszeiten_panels(row, zeitzone, zeitformat, panel_template)
                

                # ----------------------------------------------------------------------------------------------------------------------
                # 📦 Baggerdaten anzeigen: Masse, Volumen, Feststoffe, Bodenvolumen, Dichten
                # ----------------------------------------------------------------------------------------------------------------------
                    st.markdown("---")
                    st.markdown("#### Baggerwerte im Umlauf", unsafe_allow_html=True)
   
                    zeige_baggerwerte_panels(kennzahlen, tds_werte, zeitzone, pw, pf, pb, panel_template, dichte_panel_template)
                
                # ----------------------------------------------------------------------------------------------------------------------
                # 📍 Streckenanzeige pro Umlauf
                # ----------------------------------------------------------------------------------------------------------------------
                    st.markdown("---")
                    st.markdown("#### Strecken im Umlauf")
              
                    zeige_strecken_panels(
                        strecke_disp["leerfahrt"], strecke_disp["baggern"], strecke_disp["vollfahrt"],
                        strecke_disp["verbringen"], strecke_disp["gesamt"],
                        dauer_disp["leerfahrt"], dauer_disp["baggern"], dauer_disp["vollfahrt"],
                        dauer_disp["verbringen"], dauer_disp["umlauf"],
                        strecken_panel_template
                    )
                # ----------------------------------------------------------------------------------------------------------------------
                # 📊 Zeitliche Phasen anzeigen (Leerfahrt, Baggern und Strecken)
                # ----------------------------------------------------------------------------------------------------------------------
                    st.markdown("---")  

                    st.markdown("#### Statuszeiten und Strecken im Umlauf", unsafe_allow_html=True)
                    zeige_statuszeiten_panels_mit_strecke(row, zeitzone, zeitformat, strecken=strecke_disp, panel_template=status_panel_template_mit_strecke)
           
                
                    # ----------------------------------------------------------------------------------------------------------------------
                    # 🛠️ Debug-Infos (ausklappbar) – Strategie-Auswertung und Werte anzeigen
                    # ----------------------------------------------------------------------------------------------------------------------
                    st.markdown("---")   
                    with st.expander("🛠️ Debug-Infos & Strategieergebnisse", expanded=False):
                        st.markdown(f"🔍 **Strategie Verdraengung**: `{strategie.get('Verdraengung', {})}`")
                        st.markdown(f"🔍 **Strategie Ladungsvolumen**: `{strategie.get('Ladungsvolumen', {})}`")
                    
                        for zeile in debug_info:
                            st.markdown(zeile)
                    
                        st.markdown("### 📋 Übersicht Start-/Endwerte laut Strategie")
                    
                        werte_tabelle = pd.DataFrame([
                            {
                                "Parameter": "Verdraengung Start",
                                "Wert": f"{werte['Verdraengung Start']:.2f}" if werte.get("Verdraengung Start") is not None else "-",
                                "Zeitstempel": sichere_zeit(werte.get("Verdraengung Start TS"), zeitzone)
                            },
                            {
                                "Parameter": "Verdraengung Ende",
                                "Wert": f"{werte['Verdraengung Ende']:.2f}" if werte.get("Verdraengung Ende") is not None else "-",
                                "Zeitstempel": sichere_zeit(werte.get("Verdraengung Ende TS"), zeitzone)
                            },
                            {
                                "Parameter": "Ladungsvolumen Start",
                                "Wert": f"{werte['Ladungsvolumen Start']:.2f}" if werte.get("Ladungsvolumen Start") is not None else "-",
                                "Zeitstempel": sichere_zeit(werte.get("Ladungsvolumen Start TS"), zeitzone)
                            },
                            {
                                "Parameter": "Ladungsvolumen Ende",
                                "Wert": f"{werte['Ladungsvolumen Ende']:.2f}" if werte.get("Ladungsvolumen Ende") is not None else "-",
                                "Zeitstempel": sichere_zeit(werte.get("Ladungsvolumen Ende TS"), zeitzone)
                            }
                        ])
                    
                        st.dataframe(werte_tabelle, use_container_width=True, hide_index=True)
                        
                    # ----------------------------------------------------------------------------------------------------------------------
                    # 📊 Debug-Infos (ausklappbar) – Verweilzeiten pro Polygon
                    # ----------------------------------------------------------------------------------------------------------------------
                                        
                    with st.expander("📊 Verweilzeiten pro Polygon"):
                        df_bagger = berechne_punkte_und_zeit(df, statuswert=2)
                        df_verbring = berechne_punkte_und_zeit(df, statuswert=4)
            
                        st.write("**Baggerzeiten pro Feld (Status 2):**")
                        st.dataframe(df_bagger)
            
                        st.write("**Verbringzeiten pro Feld (Status 4):**")
                        st.dataframe(df_verbring) 
                        
                    with st.expander("🔍 Debug: Statusverlauf prüfen (nur gewählter Umlauf)", expanded=False):
                        if row is not None and not df.empty:
                            t_start = pd.to_datetime(row["Start Leerfahrt"], utc=True)
                            t_ende = pd.to_datetime(row["Ende"], utc=True)
                            df_debug = df[(df["timestamp"] >= t_start) & (df["timestamp"] <= t_ende)][["timestamp", "Status"]].copy()
                    
                            if "Status_neu" in df.columns:
                                df_debug["Status_neu"] = df["Status_neu"]
                            else:
                                df_debug["Status_neu"] = "nicht vorhanden"
                    
                            st.dataframe(df_debug, use_container_width=True, hide_index=True)
                    
                            # 🔢 Status_neu-Auswertung
                            if "Status_neu" in df_debug.columns:
                                status_counts = df_debug["Status_neu"].value_counts().reindex(
                                    ["Leerfahrt", "Baggern", "Vollfahrt", "Verbringen"], fill_value=0
                                )
                                unbekannt = df_debug["Status_neu"].isna().sum() + (df_debug["Status_neu"] == "nicht vorhanden").sum()
                    
                                st.markdown("**🧮 Status-Phase-Zählung:**")
                                st.write(f"- 🚢 Leerfahrt: **{status_counts['Leerfahrt']}**")
                                st.write(f"- ⚒️ Baggern: **{status_counts['Baggern']}**")
                                st.write(f"- 🛳️ Vollfahrt: **{status_counts['Vollfahrt']}**")
                                st.write(f"- 🌊 Verbringen: **{status_counts['Verbringen']}**")
                                st.write(f"- ❓ Unbekannt / nicht vorhanden: **{unbekannt}**")
                    
                        else:
                            st.info("Kein Umlauf oder keine Daten geladen.")



            else:
                st.info("Bitte einen konkreten Umlauf auswählen.")


            

#=====================================================================================
elif not uploaded_files:
    st.info("Bitte lade mindestens eine Datei hoch.")

