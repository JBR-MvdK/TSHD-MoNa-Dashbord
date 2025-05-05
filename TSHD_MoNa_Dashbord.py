# ==============================================================================================================================
# 🔵 IMPORTS & HILFSFUNKTIONEN
# Dieses Modul importiert alle zentralen Abhängigkeiten – sowohl Standardbibliotheken, externe Pakete als auch eigene Module.
# Die Einteilung erfolgt thematisch: Basisfunktionen, Visualisierung, Geodatenverarbeitung und modulare Analyseschritte.
# ==============================================================================================================================

# === 🔧 BASIS-MODULE (Standardbibliothek & Basisdatenverarbeitung) ===
import os              # Datei- und Verzeichnisoperationen (z. B. Pfadprüfungen, Dateiexistenz etc.)
import json            # Verarbeitung von JSON-Dateien (z. B. Laden von Konfigurationsdaten oder Schiffseinstellungen)
import pandas as pd    # Tabellenverarbeitung und Datenanalyse (z. B. Filtern, Gruppieren, Zeitreihen)
import numpy as np     # Mathematische Funktionen (z. B. Mittelwerte, NaN-Erkennung, Array-Operationen)
import pytz            # Zeitzonen-Verarbeitung und Konvertierung von Timestamps
import traceback       # Lesbare Fehler-Stacks für Debugging und Fehleranalyse

# === 📊 UI & VISUALISIERUNG ===
import streamlit as st               # Haupt-Framework zur Erstellung der interaktiven Web-Oberfläche
import plotly.graph_objects as go    # Interaktive Diagramme (z. B. Zeitreihen, Karten, Tooltips)

# === 🌍 GEODATEN & GEOMETRIE ===
from shapely.geometry import Point   # Geometrische Abfragen, z. B. Punkt-in-Polygon-Prüfungen


# === 🧩 EIGENE MODULE (Modularisierte Funktionsbausteine für einzelne Analyseschritte) ===

# 🟡 Import und Berechnung technischer TDS-Parameter (z. B. Volumen, Masse, Konzentration)
from modul_tshd_mona_import import parse_mona, berechne_tds_parameter

# 🟦 Segmentierung der Fahrtdaten in einzelne Umläufe (Statuslogik)
from modul_umlaeufe import nummeriere_umlaeufe, extrahiere_umlauf_startzeiten

# ⚓ Erkennung der aktiven Baggerseite (Backbord/Steuerbord oder beide)
from modul_baggerseite import erkenne_baggerseite

# 🌐 Automatische EPSG-Code-Erkennung (für korrekte Geo-Referenzierung)
from modul_koordinatenerkennung import erkenne_koordinatensystem

# 📥 XML-Import von Baggerfeld-Definitionen (Polygone mit Solltiefe)
from modul_baggerfelder_xml_import import parse_baggerfelder

# 📏 Berechnung von Solltiefen entlang des Tracks (basierend auf Polygonzuordnung)
from modul_solltiefe_tshd import berechne_solltiefe_fuer_df

# 🚢 Streckenberechnung nach Status (Leerfahrt, Baggerfahrt, Verbringen)
from modul_strecken import berechne_strecken

# 📊 Kennzahlen je Umlauf berechnen (z. B. Verdrängung, Ladevolumen, Konzentration)
from modul_umlauf_kennzahl import berechne_umlauf_kennzahlen

# 🎯 Strategie zur Erkennung geeigneter Start- und Endzeitpunkte (z. B. min/max, Plateaus)
from modul_startend_strategie import berechne_start_endwerte

# 🧰 Allgemeine Hilfsfunktionen (z. B. Zeitumrechnung, Formatierung, Spaltenwahl)
from modul_hilfsfunktionen import (
    split_by_gap,                     # Segmentierung bei Zeitlücken
    convert_timestamp,                # Zeitzonenbewusste Umrechnung von Timestamps
    format_time, format_de,           # Formatierung von Zahlen und Uhrzeiten
    plot_x,                           # Zeitachse für Plotly
    lade_schiffsparameter,            # Laden schiffsspezifischer Parameter (z. B. TDS)
    pruefe_werte_gegen_schiffsparameter,  # Plausibilitätsprüfung
    to_hhmmss, to_dezimalstunden, to_dezimalminuten,  # Zeitformat-Konvertierung
    format_dauer, sichere_dauer, sichere_zeit,        # Sichere Berechnung von Zeitdifferenzen
    get_spaltenname                  # Dynamischer Zugriff auf BB/SB-Spalten
)

# === 🪟 STREAMLIT UI-PANELS (zur Visualisierung von Kennzahlen, Strecken, Baggerfeldern etc.) ===
from modul_ui_panels import (
    zeige_statuszeiten_panels,         # Zeitliche Aufschlüsselung pro Status
    zeige_baggerwerte_panels,          # Volumen, Masse, Konzentration, etc.
    zeige_strecken_panels,             # Darstellung der zurückgelegten Strecken
    zeige_bagger_und_verbringfelder,   # Interaktive Anzeige der betroffenen Polygone
    zeige_statuszeiten_panels_mit_strecke,
    panel_template, strecken_panel_template, dichte_panel_template, feld_panel_template, status_panel_template_mit_strecke
)

# === 📈 Interaktive Zeitreihengrafiken (Prozessdaten über gesamten Umlauf)
from modul_prozessgrafik import zeige_prozessgrafik_tab, zeige_baggerkopftiefe_grafik

# 🔄 Polygonbasierte Auswertungen (z. B. Aufenthaltsdauer je Feld)
from modul_polygon_auswertung import berechne_punkte_und_zeit

# 🧮 Komplexe Auswertung pro Umlauf (TDS-Berechnung, Kennzahlen, Strecken etc.)
from modul_berechnungen import berechne_umlauf_auswertung

# 🗂️ Tabellen für alle Umläufe + Zeit-Summen pro Status
from modul_umlauftabelle import (
    show_gesamtzeiten_dynamisch,
    erstelle_umlauftabelle,
    berechne_gesamtzeiten
)

# 🗺️ Darstellung der Tracks + Polygone auf interaktiven Karten
from modul_karten import plot_karte, zeige_umlauf_info_karte


#==============================================================================================================================
# 🔵 Start der Streamlit App
#==============================================================================================================================

# Streamlit Seiteneinstellungen (Titel und Layout)
st.set_page_config(page_title="TSHD-MoNa Dashboard - MvdK", layout="wide")
st.title("📊 TSHD-MoNa Dashboard - MvdK")

# Sidebar für Datei-Upload
st.sidebar.header("📂 Datei-Upload")

# --- Upload-Expander für MoNa- und XML-Dateien ---
with st.sidebar.expander("📂 Dateien hochladen / auswählen", expanded=True):
    uploaded_files = st.file_uploader(
        "MoNa-Dateien (.txt) auswählen", 
        type=["txt"], 
        accept_multiple_files=True,
        key="mona_upload"
    )
    upload_status = st.empty()  # Dynamischer Platzhalter für spätere Erfolgsmeldungen

    uploaded_xml_files = st.file_uploader(
        "Baggerfeldgrenzen (XML)", 
        type=["xml"], 
        accept_multiple_files=True,
        key="xml_upload"
    )
    xml_status = st.empty()  # Platzhalter für XML-Upload-Status



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
        value=0.3, step=0.01, format="%.2f"
    )

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

# --- Einlesen der MoNa-Dateien ---
if uploaded_files:
    try:
        # Daten aus den hochgeladenen Dateien parsen
        df, rw_max, hw_max = parse_mona(uploaded_files)
        
        # Erfolgsmeldung anzeigen: Wie viele Zeilen wurden geladen?
        upload_status.success(f"{len(df)} Zeilen aus {len(uploaded_files)} Datei(en) geladen")
        
        # Berechnung zusätzlicher TDS-Parameter (z.B. Dichte, Konzentrationen)
        df = berechne_tds_parameter(df, pf, pw)
        schiffsnamen = df["Schiffsname"].dropna().unique()
                
        # Automatische Erkennung des Koordinatensystems (z.B. UTM, GK)
        if 'df' in locals() and not df.empty:
            proj_system, epsg_code, auto_erkannt = erkenne_koordinatensystem(
                df, st=koordsys_status, sidebar=st.sidebar
            )
        
        # --- Basis-Infos extrahieren (Schiffsname, Zeitbereich) ---
        schiffe = df["Schiffsname"].dropna().unique()
        if len(schiffe) == 1:
            schiffsname_text = f"**Schiff:** **{schiffe[0]}**"
        elif len(schiffe) > 1:
            schiffsname_text = f"**Schiffe im Datensatz:** {', '.join(schiffe)}"
        else:
            schiffsname_text = "Keine bekannten Schiffsnamen gefunden."
        
        meta_info = st.empty()  # Platzhalter für dynamische Metadaten

        # Zeitbereich absichern, damit bei NaT (z.B. bei leerem df nach Filter) keine Fehler auftreten
        zeit_min = df["timestamp"].min()
        zeit_max = df["timestamp"].max()
        
        if pd.isnull(zeit_min) or pd.isnull(zeit_max):
            zeitraum_text = "Zeitraum: Unbekannt"
        else:
            zeitraum_text = f"{zeit_min.strftime('%d.%m.%Y %H:%M:%S')} – {zeit_max.strftime('%d.%m.%Y %H:%M:%S')} UTC"

        
        meta_info.markdown(f"""
        {schiffsname_text}  
        **Zeitraum:** {df["timestamp"].min().strftime('%d.%m.%Y %H:%M:%S')} – {df["timestamp"].max().strftime('%d.%m.%Y %H:%M:%S')} UTC  
        **Baggerseite:** *(wird noch erkannt...)*
        """)
        
        # 🎯 Schiffsparameter laden und prüfen
        schiffsparameter = lade_schiffsparameter()
        
        if schiffsparameter:
            if len(schiffsnamen) == 1:
                st.sidebar.success(f"Schiffsparameter geladen ({len(schiffsparameter)} Schiffe) – {schiffsnamen[0]}")
            else:
                st.sidebar.success(f"Schiffsparameter geladen ({len(schiffsparameter)} Schiffe)")

        else:
            st.sidebar.info("ℹ️ Keine Schiffsparameter-Datei gefunden oder leer.")
        

        if len(schiffsnamen) == 1:
            schiff = schiffsnamen[0]
            df, fehlerhafte = pruefe_werte_gegen_schiffsparameter(df, schiff, schiffsparameter)
            if fehlerhafte:
                for spalte, anzahl in fehlerhafte:
                    st.warning(f"⚠️ {anzahl} Werte aus Spalte **{spalte}** außerhalb der gültigen Grenzen für **{schiff}** – wurden entfernt.")


#==============================================================================================================================
# 🔵 # 📋 Schiffsparameter bearbeiten und speichern
#==============================================================================================================================

        # 📋 Schiffsparameter bearbeiten und speichern
        with st.sidebar.expander("🔧 Schiffsparameter bearbeiten", expanded=False):
        
            if len(schiffe) == 1:
                schiff = schiffe[0]
                st.markdown(f"**Aktives Schiff:** {schiff}")
        
                # Bestehende Werte laden oder leeres Template anlegen
                aktuelle_param = schiffsparameter.get(schiff, {})
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
        
                # Parameter in DataFrame umwandeln für Editierung
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
                    # Update JSON-Objekt
                    schiffsparameter[schiff] = {
                        row["Spalte"]: {
                            "min": row["min"] if pd.notnull(row["min"]) else None,
                            "max": row["max"] if pd.notnull(row["max"]) else None
                        }
                        for _, row in edited_df.iterrows()
                    }
                    # Schreiben in JSON-Datei
                    with open("schiffsparameter.json", "w", encoding="utf-8") as f:
                        json.dump(schiffsparameter, f, indent=2, ensure_ascii=False)
                    st.success("✅ Parameter gespeichert.")
            else:
                st.info("Bitte lade MoNa-Daten mit eindeutigem Schiffsname.")

            # --- Erweiterung: Zeige die Start-/End-Strategie, wenn vorhanden ---
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


#==============================================================================================================================
# 🔵 Filterleiste und Grundeinstellungen
#==============================================================================================================================

# --- Filteroptionen direkt vor der Hauptanzeige ---
        st.markdown("---")
        col_startwert, col_umlauf, col_zeitformat, col_zeitzone = st.columns([1, 1, 1, 1])

        # Startwert der Umlaufzählung setzen
        with col_startwert:
            startwert = st.number_input("🔢 Startwert Umlaufzählung", min_value=1, step=1, value=1)

        # --- Umläufe berechnen und Umlauftabelle extrahieren ---
        df = nummeriere_umlaeufe(df, startwert=startwert)
        umlauf_info_df = extrahiere_umlauf_startzeiten(df, startwert=startwert)

        if not umlauf_info_df.empty:
            if "Start Leerfahrt" in umlauf_info_df.columns:
                umlauf_info_df["start"] = umlauf_info_df["Start Leerfahrt"]
            if "Ende" in umlauf_info_df.columns:
                umlauf_info_df["ende"] = umlauf_info_df["Ende"]

        # Umlauf-Auswahl
        with col_umlauf:
            umlauf_options = ["Alle"]
            if not umlauf_info_df.empty and "Umlauf" in umlauf_info_df.columns:
                umlauf_options += [int(u) for u in umlauf_info_df["Umlauf"]]
            
            umlauf_auswahl = st.selectbox(
                "🔁 Umlauf auswählen",
                options=umlauf_options
            )

        # Zeitformat wählen (hh:mm:ss, Dezimalminuten, Dezimalstunden)
        with col_zeitformat:
            zeitformat = st.selectbox(
                "🕒 Zeitformat für Summenanzeige",
                options=["hh:mm:ss", "dezimalminuten", "dezimalstunden"],
                index=1,
                format_func=lambda x: {
                    "hh:mm:ss": "hh:mm:ss",
                    "dezimalminuten": "Dezimalminuten",
                    "dezimalstunden": "Dezimalstunden"
                }[x]
            )

        # Zeitzone auswählen
        with col_zeitzone:
            zeitzone = st.selectbox(
                "🌍 Zeitzone anzeigen",
                ["UTC", "Lokal (Europe/Berlin)"],
                index=0
            )

        # Zeitzonenanpassung auf Timestamps im DataFrame
        if df["timestamp"].dt.tz is None:
            df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")

        # Verfügbare Umläufe vorbereiten
        verfuegbare_umlaeufe = df["Umlauf"].dropna().unique()
        verfuegbare_umlaeufe.sort()

        # Einzelne Umlaufzeile und zugehörige Kennzahlen vorbereiten
        kennzahlen = {}  # Leeres Dict für Kennzahlen, falls "Alle" gewählt wurde
        row = None       # Platzhalter für die ausgewählte Zeile (einzelner Umlauf)

        if umlauf_auswahl != "Alle":
            # Zeile aus der Umlauftabelle extrahieren, die dem gewählten Umlauf entspricht
            zeile = umlauf_info_df[umlauf_info_df["Umlauf"] == umlauf_auswahl]
            if not zeile.empty:
                row = zeile.iloc[0]  # Erste (und einzige) Zeile herausziehen
                # Kennzahlen (z. B. Mengen, Zeiten, Verdraengung etc.) berechnen
                kennzahlen = berechne_umlauf_kennzahlen(row, df)
   
            

#==============================================================================================================================
# 🔵 Baggerseite erkennen und auswählen
#==============================================================================================================================

# Auswahl der Baggerseite (Auto / BB / SB / BB+SB)
        seite_auswahl = st.sidebar.selectbox(
            "🧭 Baggerseite wählen",
            options=["Auto", "BB", "SB", "BB+SB"],
            index=1
        )

        # Automatische Erkennung der Seite (aus den Daten)
        erkannte_seite = erkenne_baggerseite(df)
        seite = erkannte_seite if seite_auswahl == "Auto" else seite_auswahl

        # Metadaten aktualisieren
        meta_info.markdown(f"""
        {schiffsname_text}  
        **Zeitraum:** {df["timestamp"].min().strftime('%d.%m.%Y %H:%M:%S')} – {df["timestamp"].max().strftime('%d.%m.%Y %H:%M:%S')} UTC  
        **Baggerseite:** {seite}
        """)

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

        meta_info.markdown(f"""
        {schiffsname_text}  
        **Zeitraum:** {df["timestamp"].min().strftime('%d.%m.%Y %H:%M:%S')} – {df["timestamp"].max().strftime('%d.%m.%Y %H:%M:%S')} UTC  
        **Baggerseite:** {seite}  
        **Solltiefe:** {anzeige_solltiefe}{anzeige_m} ({solltiefe_herkunft})
        """)
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

#==============================================================================================================================
# 🔵 Tabs definieren
#==============================================================================================================================

# Tabs für die verschiedenen Visualisierungen
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🗺️ Karte",
            "📊 Prozessdaten",
            "🌊 Tiefenprofil",
            "🧾 Umlauftabelle",
            "🧮 Umlaufanalyse",
            "🧷 Übersicht + Details"
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
        
                    # Panels und Felder
                    #zeige_statuszeiten_panels(row, zeitzone, zeitformat, panel_template)
                    #st.markdown("---")
                    
                    zeige_bagger_und_verbringfelder(
                        bagger_namen=bagger_namen,
                        verbring_namen=verbring_namen,
                        df=df,
                        baggerfelder=baggerfelder  # ❗️wichtig!
                    )

                    
                    #zeige_bagger_und_verbringfelder(bagger_namen, verbring_namen, df)
                    
                    #st.markdown("---")        
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
                if not df_status2.empty:
                    first_latlon = transformer.transform(df_status2.iloc[0]["RW_Schiff"], df_status2.iloc[0]["HW_Schiff"])
                    last_latlon = transformer.transform(df_456.iloc[-1]["RW_Schiff"], df_456.iloc[-1]["HW_Schiff"])

                    fig.update_layout(
                        mapbox_center={"lat": first_latlon[1], "lon": first_latlon[0]},
                        mapbox_zoom=13
                    )
                else:
                    st.info("Keine Daten mit Status 2 verfügbar.")
            
                # Überschrift und Karte darstellen
                #st.markdown("#### Baggerstelle")
                st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})
            
            
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
                st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})


        
#==============================================================================================================================
# Tab 2 - Diagramm Prozessdaten
#==============================================================================================================================
        
        with tab2:
            
            # Nur anzeigen, wenn ein einzelner Umlauf ausgewählt ist
            if umlauf_auswahl != "Alle" and row is not None:
                st.markdown("#### 📈 Umlaufgrafik – Prozessdaten")
                zeige_prozessgrafik_tab(df, zeitzone, row, schiffsparameter, schiff, seite, plot_key="prozessgrafik_tab2")


            else:
                st.info("Bitte einen konkreten Umlauf auswählen.")

# ==============================================================================================================================
# Tab 3 - Diagramm Tiefe Baggerkopf (Modularisiert)
# ==============================================================================================================================
       
        with tab3:
            st.markdown("#### Baggerkopftiefe")
            if umlauf_auswahl != "Alle":
                zeige_baggerkopftiefe_grafik(df, zeitzone, seite)
        
            else:
                st.info("Bitte einen konkreten Umlauf auswählen.")

#==============================================================================================================================
# Tab 4 - Umlauftabelle - gesamt 
#==============================================================================================================================
 
        with tab4:
            st.markdown("#### Auflistung aller Umläufe")
        
            if not umlauf_info_df.empty:
                df_umlaeufe, list_leer, list_bagg, list_voll, list_verk, list_umlauf = erstelle_umlauftabelle(
                    umlauf_info_df, zeitzone, zeitformat
                )
        
                gesamtzeiten = berechne_gesamtzeiten(list_leer, list_bagg, list_voll, list_verk, list_umlauf)
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
# TAB 5 – Numerische Auswertung Umlaufdaten: Panel-Templates für visuelle Darstellung
# ======================================================================================================================
        
        with tab5:

            if umlauf_auswahl != "Alle":
                row = umlauf_info_df[umlauf_info_df["Umlauf"] == umlauf_auswahl].iloc[0]
                strategie = schiffsparameter.get(schiff, {}).get("StartEndStrategie", {})
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
                if kennzahlen:
                    zeige_baggerwerte_panels(kennzahlen, tds_werte, zeitzone, pw, pf, pb, panel_template, dichte_panel_template)
                
                # ----------------------------------------------------------------------------------------------------------------------
                # 📍 Streckenanzeige pro Phase
                # ----------------------------------------------------------------------------------------------------------------------
                st.markdown("---")
                st.markdown("#### Strecken im Umlauf")
                if kennzahlen:                
                    zeige_strecken_panels(
                        strecke_disp["leerfahrt"], strecke_disp["baggern"], strecke_disp["vollfahrt"],
                        strecke_disp["verbringen"], strecke_disp["gesamt"],
                        dauer_disp["leerfahrt"], dauer_disp["baggern"], dauer_disp["vollfahrt"],
                        dauer_disp["verbringen"], dauer_disp["umlauf"],
                        strecken_panel_template
                    )

              
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
            else:
                st.info("Bitte einen konkreten Umlauf auswählen.")

#==============================================================================================================================
# Tab - Umlauftabelle - gesamt 
#==============================================================================================================================
            
        with tab6:
            if umlauf_auswahl != "Alle":
                zeige_bagger_und_verbringfelder(bagger_namen, verbring_namen, df)
                st.markdown("---")

                zeige_statuszeiten_panels_mit_strecke(
                    row=row,
                    zeitzone=zeitzone,
                    zeitformat="hh:mm:ss",
                    strecken=strecke_disp,  # z. B. {"leerfahrt": "1,23 km", "gesamt": "5,42 km", ...}
                    panel_template=status_panel_template_mit_strecke
                )
                        
                
                zeige_statuszeiten_panels(row, zeitzone, zeitformat, panel_template)
        
                zeige_prozessgrafik_tab(df, zeitzone, row, schiffsparameter, schiff, seite, plot_key="prozessgrafik_tab6")
        
                zeige_baggerwerte_panels(kennzahlen, tds_werte, zeitzone, pw, pf, pb, panel_template, dichte_panel_template)
        
                with st.expander("📊 Verweilzeiten pro Polygon"):
                    df_bagger = berechne_punkte_und_zeit(df, statuswert=2)
                    df_verbring = berechne_punkte_und_zeit(df, statuswert=4)
        
                    st.write("**Baggerzeiten pro Feld (Status 2):**")
                    st.dataframe(df_bagger)
        
                    st.write("**Verbringzeiten pro Feld (Status 4):**")
                    st.dataframe(df_verbring)
                    
                    
        
            else:
                st.info("Bitte einen konkreten Umlauf auswählen.")

#=====================================================================================
    except Exception as e:
        st.error(f"Fehler: {e}")
        st.text(traceback.format_exc())       
        
else:
    st.info("Bitte lade mindestens eine MoNa-Datei hoch.")
