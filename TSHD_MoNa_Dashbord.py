# === 🔧 BASIS-MODULE (Standardbibliothek & Basisdatenverarbeitung) ===
import json            # Verarbeitung von JSON-Dateien (z. B. Laden von Konfigurationsdaten oder Schiffseinstellungen)
import os              # Datei- und Verzeichnisoperationen (z. B. Pfadprüfungen, Dateiexistenz etc.)
import pandas as pd    # Tabellenverarbeitung und Datenanalyse (z. B. Filtern, Gruppieren, Zeitreihen)
import numpy as np     # Mathematische Funktionen (z. B. Mittelwerte, NaN-Erkennung, Array-Operationen)
import pytz            # Zeitzonen-Verarbeitung und Konvertierung von Timestamps
import traceback       # Lesbare Fehler-Stacks für Debugging und Fehleranalyse
import io              # Pufferobjekte und Dateioperationen im Speicher
from datetime import datetime, timedelta  # Verarbeitung und Formatierung von Zeitstempeln

# === 📊 UI & VISUALISIERUNG ===
import plotly.graph_objects as go    # Interaktive Diagramme (z. B. für Zeitverläufe, Tiefenprofile)
import streamlit as st               # Haupt-Framework zur Erstellung der interaktiven Web-Oberfläche

# === 🌍 GEODATEN & GEOMETRIE ===
from shapely.geometry import Point   # Geometrische Punkt-Objekte für Koordinatenberechnungen (z. B. Punkt-in-Polygon)

# === 🧩 EIGENE MODULE (Modularisierte Funktionsbausteine für einzelne Analyseschritte) ===

# 🟡 Import- & TDS-Berechnung (Rohdaten → Volumen, Masse, Konzentration)
from modul_tshd_hpa_import import konvertiere_hpa_ascii
@st.cache_data
def konvertiere_hpa_ascii_cached(files): return konvertiere_hpa_ascii(files)

from modul_tshd_mona_import import parse_mona, berechne_tds_parameter
@st.cache_data
def parse_mona_cached(files): return parse_mona(files)

# 🟦 Statusbasierte Umlauf-Logik (Leerfahrt, Baggern, etc.)
from modul_umlaeufe import nummeriere_umlaeufe, berechne_status_neu, mappe_umlaufnummer
@st.cache_data
def extrahiere_umlauf_startzeiten_cached(*args, **kwargs):
    from modul_umlaeufe import extrahiere_umlauf_startzeiten
    return extrahiere_umlauf_startzeiten(*args, **kwargs)

@st.cache_data
def berechne_status_neu_cached(df, umlauf_info_df):
    from modul_umlaeufe import berechne_status_neu
    return berechne_status_neu(df, umlauf_info_df)

# ⚓ Baggerseite automatisch erkennen (BB / SB)
from modul_baggerseite import erkenne_baggerseite

# 🌐 EPSG-Code automatisch ermitteln (für Georeferenzierung)
from modul_koordinatenerkennung import erkenne_koordinatensystem

# 📥 XML-Import von Baggerfeldgrenzen
from modul_baggerfelder_xml_import import parse_baggerfelder
@st.cache_data
def parse_baggerfelder_cached(xml_file, epsg_code):
    from modul_baggerfelder_xml_import import parse_baggerfelder
    return parse_baggerfelder(xml_file, epsg_code)

# 📏 Berechnung der Solltiefe entlang der Fahrtspur
from modul_solltiefe_tshd import berechne_solltiefe_fuer_df

# 🚢 Streckenanalyse je Betriebsstatus (Leerfahrt, Baggern, Verklappen ...)
from modul_strecken import berechne_strecken

# 📊 Umlaufkennzahlen berechnen (z. B. Menge, Masse, Dichte, Dauer)
from modul_umlauf_kennzahl import berechne_umlauf_kennzahlen

# 🎯 Start-/Endwertstrategie (z. B. aus Volumen oder Verdrängung)
from modul_startend_strategie import berechne_start_endwerte, STRATEGIE_REGISTRY

# 🧰 Hilfsfunktionen für Formatierung, Konvertierung, Prüfung
from modul_hilfsfunktionen import (
    convert_timestamp,                # Timestamps konvertieren inkl. Zeitzone
    erkenne_datenformat,              # Datenformat automatisch erkennen (MoNa, HPA)
    erkenne_schiff_aus_dateiname,     # Schiffsname aus Dateinamen extrahieren
    format_dauer, sichere_dauer, sichere_zeit,  # Zeitformate sicher darstellen
    format_de, format_time,           # Formatierung von Zahlen und Zeitwerten
    get_spaltenname,                  # Zugriff auf BB/SB-Spaltennamen
    lade_schiffsparameter,            # Schiffsparameter aus JSON laden
    plot_x,                           # Zeitachse für Plotly generieren
    pruefe_werte_gegen_schiffsparameter,  # Wertevalidierung gegen Schiffsdaten
    setze_schiff_manuell_wenn_notwendig,  # Schiff manuell auswählen
    split_by_gap,                     # Datengaps erkennen und segmentieren
    to_dezimalstunden, to_dezimalminuten, to_hhmmss,  # Zeitformat-Konvertierung
    initialisiere_polygon_werte,      # Einmalige Anreicherung mit Polygonattributen
    make_polygon_cache_key            # Erzeugung eindeutiger Schlüssel für Caching
)

# === 🪟 UI-Komponenten für Panels (Kennzahlen, Strecken etc.) ===
from modul_ui_panels import (
    feld_panel_template,
    panel_template,
    status_panel_template_mit_strecke,
    strecken_panel_template,
    dichte_panel_template,
    panel_template_dauer,
    zeige_bagger_und_verbringfelder,
    zeige_baggerwerte_panels,
    zeige_statuszeiten_panels,
    zeige_statuszeiten_panels_mit_strecke,
    zeige_strecken_panels,
    zeige_bonus_abrechnung_panels,
    zeige_aufsummierte_dauer_panels
)

# === 📈 Zeitreihengrafiken: Tiefe & Prozessdaten
from modul_prozessgrafik import zeige_baggerkopftiefe_grafik, zeige_prozessgrafik_tab

# 🔄 Polygon-Auswertung: Aufenthaltsdauer je Status
from modul_polygon_auswertung import berechne_punkte_und_zeit
@st.cache_data
def berechne_punkte_und_zeit_cached(df, statuswert):
    return berechne_punkte_und_zeit(df, statuswert)

# 🧮 Zentrale Auswertung eines Umlaufs
from modul_berechnungen import berechne_umlauf_auswertung

# 🗂️ Tabellen mit Umlaufzeiten, TDS, Verbringung
from modul_umlauftabelle import (
    berechne_gesamtzeiten,
    erzeuge_tds_tabelle,
    erzeuge_verbring_tabelle,
    erstelle_umlauftabelle,
    show_gesamtzeiten_dynamisch
)
@st.cache_data
def erzeuge_umlauftabelle_cached(umlauf_info_df, zeitzone, zeitformat):
    return erstelle_umlauftabelle(umlauf_info_df, zeitzone, zeitformat)

# 🗺️ Kartenansichten und Zentrum/Zoom berechnen
from modul_karten import plot_karte, zeige_umlauf_info_karte, berechne_map_center_zoom

# 📥 Excel-Import für manuelle Feststoffdaten
from modul_daten_import import lade_excel_feststoffdaten
@st.cache_data
def lade_excel_feststoffdaten_cached(file):
    from modul_daten_import import lade_excel_feststoffdaten
    return lade_excel_feststoffdaten(file)

# 📌 Dichtepolygone zuweisen (Schnittpunktprüfung)
from modul_dichtepolygon import weise_dichtepolygonwerte_zu

# 📁 ASCII-Import von Dichtepolygon-Definitionen
@st.cache_data
def parse_dichte_polygone_cached(file_text, referenz_data, epsg_code):
    from modul_dichte_polygon_ascii import parse_dichte_polygone
    file_obj = io.StringIO(file_text)
    return parse_dichte_polygone(file_obj, referenz_data, epsg_code)

# 🗺️ Steuerung der Kartenelemente (Layer)
from modul_layersteuerung import zeige_layer_steuerung

from modul_tds_manager import initialisiere_manuell_df, merge_manuelle_daten


from streamlit_option_menu import option_menu
#============================================================================================
# 🔵 Start der Streamlit App
#============================================================================================

# Streamlit Seiteneinstellungen (Titel und Layout)
st.set_page_config(page_title="TSHD Monitoring – Baggerdatenanalyse", layout="wide")
st.title("🚢 TSHD Monitoring – Baggerdatenanalyse")
st.sidebar.title("⚙️ Datenimport | Einstellungen")


# ============================================================================================
# 🔵 Datei-Upload mit automatischer Format-Erkennung
# ============================================================================================

with st.sidebar.expander("📂 Baggerdaten hochladen / auswählen", expanded=True):
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
            #datenformat = st.radio("🔄 Format manuell wählen:", ["MoNa", "HPA"], horizontal=True)


# ============================================================================================
# 🔵 Datei-Upload für Bagger- und Verbringstellenpolygone
# ============================================================================================
with st.sidebar.expander("🗺️ Polygone- und Solltiefen", expanded=False):

    uploaded_xml_files = st.file_uploader(
        "Baggerfeldgrenzen (XML)", 
        type=["xml"], 
        accept_multiple_files=True,
        key="xml_upload"
    )
    
    xml_status = st.empty()

# --- Solltiefen-Setup ---
    st.markdown("---")
    
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
# ============================================================================================
# 🔵 Bonus-/Malussystem (Trennung von Berechnungsmethode und Importmethode)
# ============================================================================================

with st.sidebar.expander("📈 Bonus-/Malussystem", expanded=False):

    # 1. Berechnungsmethode auswählen (wirkt sich auf spätere TDS-Abrechnung aus)
    berechnungsmethode = st.radio("Berechnungsmethode wählen", ["HPA – Dichtepolygone", "MoNa – Lineare Interpolation"])
    methode_code = "hpa" if "HPA" in berechnungsmethode else "mona"
    st.session_state["bonus_methode"] = methode_code  # 🔧 Für spätere Berechnungen merken



    # 2. Unabhängige Wahl der Importmethode für die Dichtewerte
    import_methode = st.radio("Importmethode der Dichtewerte", ["Dichtepolygone (CSV)", "Manuelle Eingabe"])
    st.session_state["bonus_importmethode"] = import_methode

    dichte_daten = []  # Wird mit Polygon- oder manuellen Daten gefüllt

    # ============================================================================================ 
    # --- Variante: Dichtepolygone aus CSV + optionaler JSON-Referenz importieren ---
    if import_methode == "Dichtepolygone (CSV)":
        uploaded_dichtefile = st.file_uploader("📄 Dichtepolygone (CSV)", type=["csv", "txt", "tsv"])
        uploaded_json_file = st.file_uploader("🔧 Optional: Referenzwerte (JSON)", type=["json"])

        referenz_data = None
        if uploaded_json_file:
            try:
                referenz_data = json.load(uploaded_json_file)
                st.success("✅ JSON geladen.")
            except Exception as e:
                st.warning(f"⚠️ Fehler beim JSON-Import: {e}")

        # Wenn Dichte-Datei vorhanden ist
        if uploaded_dichtefile:
            try:
                epsg_code = st.session_state.get("epsg_code", None)
                file_text = uploaded_dichtefile.getvalue().decode("utf-8")

                # Parsen der Polygoninformationen
                dichte_polygone = parse_dichte_polygone_cached(file_text, referenz_data, epsg_code)
                st.success(f"✅ {len(dichte_polygone)} Dichtepolygone geladen.")

                # In DataFrame für UI-Editor umwandeln
                df_editor = pd.DataFrame([{
                    "Bereich": p["name"],
                    "Ortsdichte": p["ortsdichte"],
                    "Ortsspezifisch": p.get("ortspezifisch", None),
                    "Min. Baggerdichte": p.get("mindichte", None),
                    "Max. Dichte": p.get("maxdichte", None)
                } for p in dichte_polygone])

                # ✏️ Formular zur Bearbeitung der Dichtewerte
                with st.form("dichtepolygon_editor_form"):
                    st.markdown("✏️ Bearbeite die Dichteparameter pro Polygon")
                    df_edit = st.data_editor(
                        df_editor,
                        hide_index=True,
                        use_container_width=True,
                        column_config={
                            "Ortsdichte": st.column_config.NumberColumn(format="%.3f"),
                            "Ortsspezifisch": st.column_config.NumberColumn(format="%.3f"),
                            "Min. Baggerdichte": st.column_config.NumberColumn(format="%.3f"),
                            "Max. Dichte": st.column_config.NumberColumn(format="%.3f"),
                        }
                    )
                    speichern = st.form_submit_button("💾 Änderungen übernehmen & speichern")

                # 🔄 Übernahme der Änderungen ins Polygonobjekt
                if speichern:
                    for i, row in df_edit.iterrows():
                        dichte_polygone[i].update({
                            "ortsdichte": row["Ortsdichte"],
                            "ortspezifisch": row["Ortsspezifisch"],
                            "mindichte": row["Min. Baggerdichte"],
                            "maxdichte": row["Max. Dichte"]
                        })
                    st.success("✅ Änderungen gespeichert.")

                # Speichern in Session-State für spätere Berechnung
                dichte_daten = dichte_polygone
                st.session_state["dichte_polygone"] = dichte_polygone
                st.session_state["bonus_dichtewerte"] = dichte_polygone

                # ➕ Export als TXT-Datei
                if dichte_polygone:
                    export_lines = []
                    for poly in dichte_polygone:
                        name = poly.get("name", "")
                        ortsdichte = poly.get("ortsdichte") or 0
                        ortsspezifisch = poly.get("ortspezifisch") or 0
                        mindichte = poly.get("mindichte") or 0
                        maxdichte = poly.get("maxdichte") or 0
                        coords = poly.get("punkte_original", [])
                        for x, y in coords:
                            line = f"{name}\t{float(x):.2f}\t{float(y):.2f}\t{float(ortsdichte):.2f}\t{float(ortsspezifisch):.2f}\t{float(mindichte):.2f}\t{float(maxdichte):.2f}"
                            export_lines.append(line)

                    export_text = "\n".join(export_lines)

                    st.download_button(
                        label="📥 Geänderte Dichtepolygone als TXT exportieren",
                        data=export_text.encode("utf-8"),
                        file_name="dichtepolygone_export.txt",
                        mime="text/plain"
                    )

            except Exception as e:
                st.error(f"❌ Fehler beim Verarbeiten: {e}")
                st.text(traceback.format_exc())   

    # ============================================================================================    
    # --- Variante: Manuelle Eingabe ---
    elif import_methode == "Manuelle Eingabe":
        st.markdown("### Manuelle Eingabe für Dichtewerte")
        ortsdichte = st.number_input("Ortsdichte (t/m³)", min_value=1.0, max_value=1.5, value=1.23, step=0.01)
        mindichte = st.number_input("Minimale Beladedichte", min_value=1.0, max_value=1.5, value=1.15, step=0.001)
        maxdichte = st.number_input("Maximale Beladedichte", min_value=1.0, max_value=1.5, value=1.29, step=0.001)
        ortsspezifisch = st.number_input("Ortsspezifischer TDS-Wert", min_value=0.0, max_value=1.0, value=0.25, step=0.001)

        if st.button("💾 Manuelle Werte übernehmen"):
            dichte_daten = [{
                "name": "manuell",
                "ortsdichte": ortsdichte,
                "mindichte": mindichte,
                "maxdichte": maxdichte,
                "ortspezifisch": ortsspezifisch
            }]
            st.success("✅ Manuelle Werte gespeichert.")

    # ============================================================================================ 
    # 🔁 Einheitliches Zwischenspeichern aller Dichtewerte
    if dichte_daten:
        st.session_state["bonus_dichtewerte"] = dichte_daten
        st.session_state["dichte_polygone"] = dichte_daten  # 🔧 Für Funktionen wie initialisiere_polygon_werte()

    # ✅ Validierung je nach Berechnungsmethode
    werte_ok = True
    for eintrag in st.session_state.get("bonus_dichtewerte", []):
        if methode_code == "hpa":
            werte_ok = all(eintrag.get(k) not in [None, 0] for k in ["ortsdichte", "mindichte", "ortspezifisch"])
        elif methode_code == "mona":
            werte_ok = all(eintrag.get(k) not in [None, 0] for k in ["ortsdichte", "mindichte", "maxdichte"])
        if not werte_ok:
            break

    if not werte_ok:
        st.warning("⚠️ Für die gewählte Methode fehlen notwendige Werte. Die Bonusberechnung ist derzeit nicht möglich.")


#============================================================================================
# 🔵 Berechnungs-Parameter in der Sidebar
#============================================================================================

# --- Dichteparameter Setup ---
with st.sidebar.expander("⚙️ Setup - Berechnungen"):
    pf = st.number_input(
        "Feststoffdichte pf [t/m³]",
        min_value=2.0, max_value=3.0,
        value=2.45, step=0.001, format="%.3f"
    )
    pw = st.number_input(
        "Wasserdichte pw [t/m³]",
        min_value=0.98, max_value=1.1,
        value=1.000, step=0.001, format="%.3f"
    )

    pb = st.number_input(
        "Angenommene Bodendichte pb [t/m³]",
        min_value=1.0, max_value=2.5,
        value=1.98, step=0.01, format="%.2f"
    )
    
    st.markdown("---") 
    
    min_fahr_speed = st.number_input(
        "Mindestgeschwindigkeit für Leerfahrt (knt)",
        min_value=0.0, max_value=2.0,
        value=0.30, step=0.01, format="%.2f"
    )

    min_vollfahrt_dauer_min = st.number_input(
        "⏱ Minimale Dauer für gültige Vollfahrtphase nach Status 2→3 (Minuten)",
        min_value=0.1,
        max_value=15.0,
        value=11.0,
        step=0.1,
        format="%.1f"
    )
    st.markdown("---") 
    # ✅ Toggle für Nutzung der Gemischdichte
    nutze_gemischdichte = st.toggle(
        "Gemischdichte für Start- und Endzeitpunkt Baggern verwenden?",
        value=True,
        help="Wenn aktiviert, wird die Gemischdichte zur Bestimmung des Beginns und Endes des Baggerns herangezogen."
    )


    dichte_grenze = st.number_input(
        "🔎 min. Grenzwert Gemischdichte [t/m³]",
        min_value=1.0, max_value=1.2, step=0.01, value=1.10,
        format="%.2f"
    )
    
    rueckblick_minute = st.slider(
        "⏱️ Rückblickzeit (min) für Gemischdichteprüfung - Statuswechsel 2 > 3", 
        min_value=0.0, max_value=4.0, step=0.5, value=2.0
    )
    st.markdown("---") 
    # ✅ Toggle korrekt einer Variable zuweisen
    nutze_schiffstrategie = st.toggle(
        "Start-/Endstrategien aus Schiffsdaten verwenden?",
        value=True,
        help="Wenn aktiviert, werden gespeicherte Strategien aus der Schiffsparameterdatei übernommen."
    )

# Platzhalter für Erkennungsinfo Koordinatensystem
koordsys_status = st.sidebar.empty()

#============================================================================================
# 🔵 MoNa-Daten verarbeiten und vorbereiten
#============================================================================================
if uploaded_files and datenformat not in ["MoNa", "HPA"]:
    st.warning("⚠️ Fehlerhafte Datei – bitte überprüfe Format und Inhalt.")
    st.stop()  # sofortiger Abbruch bei falschem Format

# ✅ Nur wenn gültiges Format, wird dieser Teil erreicht:
if uploaded_files:
    try:
        if datenformat == "MoNa":
            df, rw_max, hw_max = parse_mona_cached(uploaded_files)

        elif datenformat == "HPA":
            hpa_files = konvertiere_hpa_ascii_cached(uploaded_files)
            df, rw_max, hw_max = parse_mona_cached(hpa_files)

    except Exception as e:
        st.error("Fehler beim Laden der Daten:")
        st.exception(e)

    else:
        # ✅ Dieser Block wird nur ausgeführt, wenn KEIN Fehler aufgetreten ist
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




            
#============================================================================================
# 🔵 # 📋 Time-Slider
#============================================================================================        
# Zeitbereich ermitteln aus df
        zeit_min = df["timestamp"].min()
        zeit_max = df["timestamp"].max()
        
        # Konvertierung zu nativen datetime-Objekten (wichtig für st.slider!)
        zeit_min = zeit_min.to_pydatetime()
        zeit_max = zeit_max.to_pydatetime()
        
        # Sidebar-Slider für Zeitfilter
        with st.sidebar.expander("🕓 Beobachtungszeitraum", expanded=False):
            zeitbereich = st.slider(
                "Zeitraum auswählen",
                min_value=zeit_min,
                max_value=zeit_max,
                value=(zeit_min, zeit_max),
                format="YYYY-MM-DD HH:mm",
                step=timedelta(minutes=15)  # ← direkt timedelta, nicht datetime.timedelta
            )
       
        # DataFrame auf ausgewählten Zeitraum filtern
        df = df[(df["timestamp"] >= zeitbereich[0]) & (df["timestamp"] <= zeitbereich[1])]
        # Bereite den Text vor
        start, ende = zeitbereich
        # Falls du UTC-Label brauchst, kannst du das hier hartkodiert oder dynamisch anpassen
        zeitraum_text = (
            f"{start.strftime('%d.%m.%Y %H:%M:%S')} – {ende.strftime('%d.%m.%Y %H:%M:%S')} UTC"
        )

#============================================================================================
# 🔵 # 📋 Schiff zuweisen
#============================================================================================

        df, schiffsnamen = setze_schiff_manuell_wenn_notwendig(df, st)

        # Basisinfos: Schiffe & Zeitraum
        schiffe = df["Schiffsname"].dropna().unique()
        if len(schiffe) == 1:
            schiffsname_text = f"**Schiff:** **{schiffe[0]}**"
        elif len(schiffe) > 1:
            schiffsname_text = f"**Schiffe im Datensatz:** {', '.join(schiffe)}"
        else:
            schiffsname_text = "Keine bekannten Schiffsnamen gefunden."

       
        st.markdown(f"{schiffsname_text}  \n**Beobachtungszeitraum:** {zeitraum_text}")

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

#============================================================================================
# 🔵 # 📋 Schiffsparameter bearbeiten und speichern
#============================================================================================

        with st.sidebar.expander("🔧 Schiffsparameter", expanded=False):
            if len(schiffe) == 1:
                schiff = schiffe[0]
                st.markdown(f"**Aktives Schiff:** {schiff}")
        
                aktuelle_param = schiffsparameter.get(schiff, {})
                gespeicherte_seite = aktuelle_param.get("Baggerseite", "BB")
                erkannte_seite = erkenne_baggerseite(df)
        
                with st.form("schiffsparam_form"):
                    # 🧭 Baggerseite
                    seite_auswahl = st.selectbox(
                        "🧭 Baggerseite wählen",
                        options=["Auto", "BB", "SB", "BB+SB"],
                        index=["Auto", "BB", "SB", "BB+SB"].index(gespeicherte_seite)
                    )
                    seite = erkannte_seite if seite_auswahl == "Auto" else seite_auswahl
        
                    # 📋 Min/Max-Werte
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
                    daten = [{"Spalte": s,
                              "min": aktuelle_param.get(s, {}).get("min", None),
                              "max": aktuelle_param.get(s, {}).get("max", None)} for s in alle_spalten]
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
        
                    # 🧭 Strategien
                    from modul_startend_strategie import STRATEGIE_REGISTRY
                    st.markdown("#### ⚙️ Start-/Endwert-Strategien")
        
                    startend_parameter = ["Verdraengung", "Ladungsvolumen"]
                    neue_strategien = {}
        
                    for parameter in startend_parameter:
                        st.markdown(f"**{parameter}**")
                        alte_strategie = aktuelle_param.get("StartEndStrategie", {}).get(parameter, {})
                        start_dict = STRATEGIE_REGISTRY["Start"]
                        start_keys = list(start_dict.keys())
                        start_labels = list(start_dict.values())
        
                        start_default = alte_strategie.get("Start", "standard")
                        start_index = start_keys.index(start_default) if start_default in start_keys else 0
        
                        start_neu_label = st.selectbox(
                            f"Startwert für {parameter}",
                            options=start_labels,
                            index=start_index,
                            key=f"{parameter}_start"
                        )
                        start_neu = start_keys[start_labels.index(start_neu_label)]
        
                        ende_dict = STRATEGIE_REGISTRY["Ende"]
                        ende_keys = list(ende_dict.keys())
                        ende_labels = list(ende_dict.values())
        
                        ende_default = alte_strategie.get("Ende", "standard")
                        ende_index = ende_keys.index(ende_default) if ende_default in ende_keys else 0
        
                        ende_neu_label = st.selectbox(
                            f"Endwert für {parameter}",
                            options=ende_labels,
                            index=ende_index,
                            key=f"{parameter}_ende"
                        )
                        ende_neu = ende_keys[ende_labels.index(ende_neu_label)]
        
                        neue_strategien[parameter] = {"Start": start_neu, "Ende": ende_neu}
        
                    # 💾 Speichern-Button
                    speichern = st.form_submit_button("💾 Speichern für dieses Schiff (2x bestätigen)")
        
                    if speichern:
                        neue_param = {
                            row["Spalte"]: {
                                "min": row["min"] if pd.notnull(row["min"]) else None,
                                "max": row["max"] if pd.notnull(row["max"]) else None
                            }
                            for _, row in edited_df.iterrows()
                        }
        
                        schiffsparameter[schiff] = {
                            **neue_param,
                            "Baggerseite": seite_auswahl,
                            "StartEndStrategie": neue_strategien
                        }
        
                        with open("schiffsparameter.json", "w", encoding="utf-8") as f:
                            json.dump(schiffsparameter, f, indent=2, ensure_ascii=False)
        
                        # 🔁 aktualisiere lokale Kopie für sofortige Anzeige (optional, aber nützlich)
                        aktuelle_param = schiffsparameter[schiff]
        
                        st.success("✅ Parameter gespeichert.")
            else:
                st.info("Bitte lade MoNa-Daten mit eindeutigem Schiffsname.")
  
            strategie = schiffsparameter.get(schiff, {}).get("StartEndStrategie", {})


#============================================================================================
# 🔵 Filterleiste und Grundeinstellungen
#============================================================================================
        
        
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
        umlauf_info_df = extrahiere_umlauf_startzeiten_cached(
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
        df = berechne_status_neu_cached(df, umlauf_info_df)



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
        
        # 💡 Session-Reset für Umlaufauswahl, wenn Tab "TDS-Tabellen" aktiv ist
        if (
            "tab_auswahl" in st.session_state and 
            st.session_state["tab_auswahl"] == "TDS-Tabellen" and 
            st.session_state.get("umlauf_auswahl") != "Alle"
        ):
            del st.session_state["umlauf_auswahl"]
        
        with col_umlauf:
            umlauf_options = ["Alle"]
            if not umlauf_info_df.empty and "Umlauf" in umlauf_info_df.columns:
                umlauf_options += [int(u) for u in umlauf_info_df["Umlauf"]]
        
            # ✅ Wenn Tab "Prozessdaten", "Tiefenprofil" oder "Debug" aktiv ist UND Auswahl auf "Alle" steht → auf ersten Umlauf setzen
            if (
                st.session_state.get("tab_auswahl") in ["Prozessdaten", "Tiefenprofil", "Debug"] and
                st.session_state.get("umlauf_auswahl") == "Alle" and
                len(umlauf_options) > 1
            ):
                st.session_state["umlauf_auswahl"] = umlauf_options[1]  # Index 1 = erster echter Umlauf (nach "Alle")
        
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


#============================================================================================
# 🔵 Globale Layersteuerung
#============================================================================================

        # Auswahl wurde zuvor gesetzt
        
        show_status1_b, show_status2_b, show_status3_b, show_status456_b, show_status1_v, show_status2_v, show_status3_v, show_status456_v, auto_modus_aktiv = zeige_layer_steuerung(umlauf_auswahl)
     
#============================================================================================
# 🔵 Baggerseite erkennen und auswählen
#============================================================================================

        # Auswahl der Baggerseite (Auto / BB / SB / BB+SB)

        seite_auswahl = locals().get("seite_auswahl", "Auto")
        erkannte_seite = locals().get("erkannte_seite", "BB")
        seite = erkannte_seite if seite_auswahl == "Auto" else seite_auswahl

#============================================================================================
# 🔵 Rechtswerte normalisieren (nur für UTM)
#============================================================================================

        def normalisiere_rechtswert(wert):
            if proj_system == "UTM" and auto_erkannt and wert > 30_000_000:
                return wert - int(epsg_code[-2:]) * 1_000_000
            return wert

        # Anwenden auf relevante Spalten
        for col in ["RW_Schiff", "RW_BB", "RW_SB"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].apply(normalisiere_rechtswert)

#============================================================================================
# 🔵 XML-Dateien (Baggerfelder) einlesen
#============================================================================================

        baggerfelder = []
        if uploaded_xml_files:
            try:
                for uploaded_xml in uploaded_xml_files:
                    try:
                        felder = parse_baggerfelder_cached(uploaded_xml, epsg_code)
                        baggerfelder.extend(felder)
                    except Exception as e:
                        st.sidebar.warning(f"{uploaded_xml.name} konnte nicht geladen werden: {e}")
                if baggerfelder:
                    xml_status.success(f"{len(baggerfelder)} Baggerfelder geladen")
                else:
                    xml_status.info("Keine Baggerfelder erkannt.")
            except Exception as e:
                xml_status.error(f"Fehler beim Verarbeiten der XML-Dateien: {e}")

#============================================================================================
# 🔵 Dichtepolygone – Zuweisung von Dichteparametern je Position innerhalb eines Umlaufs
#============================================================================================
        
        # 💾 EPSG-Code (Koordinatensystem) im Session-State speichern
        #     → wird später z. B. für Umrechnung der Koordinaten gebraucht
        st.session_state["epsg_code"] = epsg_code
        
        # ✅ Prüfen, ob Dichtepolygone bereits geladen wurden (aus ASCII-Datei o. ä.)
        if "dichte_polygone" in st.session_state:
            dichte_polygone = st.session_state["dichte_polygone"]
        
        # 🔁 Prüfen, ob df bereits mit Polygonwerten angereichert wurde
        #     → verhindert doppelte Berechnung bei erneutem Umlaufwechsel o. ä.
        aktueller_key = make_polygon_cache_key(
            df, baggerfelder, st.session_state.get("dichte_polygone"),
            epsg_code, seite, toleranz_oben, toleranz_unten, solltiefe_slider
        )
        
        if st.session_state.get("polygon_key") == aktueller_key and "df_mit_polygon" in st.session_state:
            df = st.session_state["df_mit_polygon"]
        else:
            # ➕ Neue Anreicherung nur wenn sich Parameter geändert haben
            df = initialisiere_polygon_werte(
                df,
                baggerfelder=baggerfelder,
                dichte_polygone=st.session_state.get("dichte_polygone"),
                epsg_code=epsg_code,
                seite=seite,
                toleranz_oben=toleranz_oben,
                toleranz_unten=toleranz_unten,
                solltiefe_slider=solltiefe_slider
            )
            st.session_state["df_mit_polygon"] = df
            st.session_state["polygon_key"] = aktueller_key
        

#============================================================================================
# 🔢 Berechnung von Kennzahlen und Zeitpunkten je Umlauf
#============================================================================================
        
        # 📊 Kennzahlen berechnen für jeden erkannten Umlauf
        #     → z. B. Volumen, Masse, Dichte, Strecke etc.
        auswertungen = [berechne_umlauf_kennzahlen(row, df) for _, row in umlauf_info_df.iterrows()]
        df_auswertung = pd.DataFrame(auswertungen)
        
        
        
        # 🔗 Umlaufnummern ergänzen (für spätere Tabellenverknüpfung)
        if not umlauf_info_df.empty and "Umlauf" in umlauf_info_df.columns:
            df_auswertung["Umlauf"] = umlauf_info_df["Umlauf"].values
        else:
            df_auswertung["Umlauf"] = pd.Series(dtype=int)  # Leere Spalte mit Typ
        
        # 🕓 Zeitstempel des ersten Baggerpunkts je Umlauf ermitteln
        if df_auswertung.empty:
            st.warning("⚠️ Datei enthält keine vollständigen Umläufe  – Visualisierung nicht möglich.")
            df_auswertung["timestamp_beginn_baggern"] = pd.NaT
        else:
            beginn_baggern_liste = []
        
            for umlauf_nummer in df_auswertung["Umlauf"]:
                # 🔍 Suche passende Zeile im Info-DataFrame
                zeile = umlauf_info_df[umlauf_info_df["Umlauf"] == umlauf_nummer]
        
                if not zeile.empty:
                    # ⏱️ Zeitfenster für „Baggern“ bestimmen
                    start = pd.to_datetime(zeile.iloc[0]["Start Baggern"])
                    ende = pd.to_datetime(zeile.iloc[0]["Start Vollfahrt"])
        
                    # 🌍 Zeitzonen korrekt setzen
                    if start.tzinfo is None:
                        start = start.tz_localize("UTC")
                    if ende.tzinfo is None:
                        ende = ende.tz_localize("UTC")
        
                    # 🔎 Filter auf Baggerpunkte innerhalb des Zeitfensters
                    df_baggern = df[
                        (df["timestamp"] >= start) &
                        (df["timestamp"] <= ende) &
                        (df["Status_neu"] == "Baggern")
                    ]
        
                    erster_timestamp = df_baggern["timestamp"].min() if not df_baggern.empty else pd.NaT
                else:
                    erster_timestamp = pd.NaT
        
                beginn_baggern_liste.append(erster_timestamp)
        
            # 🧾 Neue Spalte anhängen
            df_auswertung["timestamp_beginn_baggern"] = beginn_baggern_liste
              
#============================================================================================
# 🔵 Solltiefe auf Basis der Baggerfelder berechnen
#============================================================================================

        # 📦 Smarter Caching-Mechanismus für Polygonanreicherung
        #     → spart Rechenzeit, wenn sich Parameter nicht geändert haben
        aktueller_key = make_polygon_cache_key(
            df, baggerfelder, st.session_state.get("dichte_polygone"),
            epsg_code, seite, toleranz_oben, toleranz_unten, solltiefe_slider
        )
        
        if st.session_state.get("polygon_key") == aktueller_key and "df_mit_polygon" in st.session_state:
            df = st.session_state["df_mit_polygon"]
        else:
            # ➕ Neue Anreicherung, wenn sich Parameter geändert haben
            df = initialisiere_polygon_werte(
                df,
                baggerfelder=baggerfelder,
                dichte_polygone=st.session_state.get("dichte_polygone"),
                epsg_code=epsg_code,
                seite=seite,
                toleranz_oben=toleranz_oben,
                toleranz_unten=toleranz_unten,
                solltiefe_slider=solltiefe_slider
            )
            st.session_state["df_mit_polygon"] = df
            st.session_state["polygon_key"] = aktueller_key
        
        # 🧾 Namen der Bagger- und Verbringfelder extrahieren (nur wenn Spalten vorhanden)
        bagger_namen = []
        verbring_namen = []
        
        if "Polygon_Name" in df.columns and "Status_neu" in df.columns:
            df_bagger = df[df["Status_neu"] == "Baggern"]
            df_verbring = df[df["Status_neu"] == "Verbringen"]
        
            bagger_namen = sorted(df_bagger["Polygon_Name"].dropna().unique())
            verbring_namen = sorted(df_verbring["Polygon_Name"].dropna().unique())
        
        # 🔎 Aktuelle Solltiefe bestimmen und Herkunft analysieren
        if "Solltiefe_Aktuell" in df.columns and df["Solltiefe_Aktuell"].notnull().any():
            gueltige = df["Solltiefe_Aktuell"].dropna()
            if (gueltige == gueltige.iloc[0]).all():
                solltiefe_wert = gueltige.iloc[0]  # Einheitlicher Wert im gesamten df
            else:
                solltiefe_wert = "variabel"       # Unterschiedliche Werte → variabel
        else:
            solltiefe_wert = None                 # Keine Werte vorhanden
        
        # 🧠 Herkunftslogik: Bestimme, wie Solltiefe zustande kam
        if solltiefe_wert is None:
            solltiefe_herkunft = "nicht definiert"
        elif solltiefe_wert == solltiefe_slider:
            solltiefe_herkunft = "manuelle Eingabe"
        elif solltiefe_wert == "variabel":
            solltiefe_herkunft = "aus XML - mehrere Werte"
        else:
            solltiefe_herkunft = "aus XML-Datei übernommen"
        
        # 📤 Ausgabeformatierung der Solltiefe
        if isinstance(solltiefe_wert, (int, float)):
            anzeige_solltiefe = f"{solltiefe_wert:.2f}"
            anzeige_m = " m"
        elif solltiefe_wert == "variabel":
            anzeige_solltiefe = "variabel"
            anzeige_m = ""
        else:
            anzeige_solltiefe = " "
            anzeige_m = ""
#============================================================================================

        df_ungefiltert = df.copy()


#============================================================================================
# 🔵 FESTSTOFFDATEN – Manuelle Eingaben (CSV/Excel), Zusammenführung, Bearbeitung in Sidebar
#============================================================================================

        # ✅ Relevante Daten in Session speichern (für spätere Schritte / Module)
        st.session_state["umlauf_info_df_all"] = umlauf_info_df_all
        st.session_state["df_auswertung"] = df_auswertung

        # 📦 Sidebar: Datenimport und manuelle Bearbeitung
        with st.sidebar.expander("📥 Feststoffdaten laden und bearbeiten", expanded=False):
            st.markdown("Lade CSV oder Excel mit Feststoffdaten. Bearbeite sie anschließend direkt.")

            # 🔄 Eingabedaten vorbereiten
            df_import = None           # CSV-Import
            df_excel_import = None     # Excel-Import

            # 1️⃣ CSV-Datei hochladen (manuell gespeicherte Feststoffdaten)
            uploaded_csv = st.file_uploader("📄 CSV (frühere Eingaben)", type=["csv"], key="sidebar_csv")
            if uploaded_csv:
                try:
                    df_import = pd.read_csv(uploaded_csv)
                    df_import["timestamp_beginn_baggern"] = pd.to_datetime(df_import["timestamp_beginn_baggern"], utc=True)
                    st.success("✅ CSV erfolgreich geladen.")
                except Exception as e:
                    st.error(f"❌ Fehler beim Einlesen der CSV: {e}")

            # 2️⃣ Excel-Datei hochladen (z. B. Wochenbericht vom Schiff)
            uploaded_excel = st.file_uploader("📘 Excel: Wochenbericht vom Schiff", type=["xlsx"], key="sidebar_excel")
            if uploaded_excel:
                try:
                    df_excel_import = lade_excel_feststoffdaten_cached(uploaded_excel)
                    st.success("✅ Excel erfolgreich geladen.")
                except Exception as e:
                    st.error(f"❌ Fehler beim Einlesen der Excel-Datei: {e}")

            # 3️⃣ Weiter nur, wenn beide Basisdaten vorhanden sind
            umlauf_info_df_all = st.session_state.get("umlauf_info_df_all", pd.DataFrame())
            df_auswertung = st.session_state.get("df_auswertung", pd.DataFrame())

            if not umlauf_info_df_all.empty and not df_auswertung.empty:
                # 🔍 Typanpassung: Umlauf-Nummern müssen ganzzahlig sein
                df_auswertung["Umlauf"] = df_auswertung["Umlauf"].astype(int)
                umlauf_info_df_all["Umlauf"] = umlauf_info_df_all["Umlauf"].astype(int)

                # ✳️ Manuelle Datentabelle initialisieren (Basis: alle Umläufe)
                df_manuell = initialisiere_manuell_df(umlauf_info_df_all, df_auswertung)

                # 🔗 Daten aus CSV und Excel (sofern vorhanden) in die Tabelle einfügen
                df_manuell, fehlende_merge_zeilen = merge_manuelle_daten(
                    df_manuell, df_csv=df_import, df_excel=df_excel_import
                )

                # 🧠 Aktuelle Version in den Session State schreiben
                st.session_state["df_manuell"] = df_manuell
                st.session_state["fehlende_merge_zeilen"] = fehlende_merge_zeilen

                # ⚠️ Info bei fehlender Zuordnung (z. B. Zeitstempel nicht gefunden)
                if not fehlende_merge_zeilen.empty:
                    st.warning(f"⚠️ {len(fehlende_merge_zeilen)} Umläufe ohne passende CSV-/Excel-Zuordnung.")

                # ✏️ Eingabemaske: Manuelle Daten direkt editieren
                st.markdown("#### ✏️ Editor Feststoffwerte")
                df_editor = df_manuell.copy()

                df_editor_display = st.data_editor(
                    df_editor.loc[:, ["Umlauf", "timestamp_beginn_baggern", "feststoff", "proz_wert"]],
                    num_rows="dynamic",
                    use_container_width=True,
                    column_config={
                        "Umlauf": st.column_config.NumberColumn("Umlauf", disabled=True),
                        "timestamp_beginn_baggern": st.column_config.DatetimeColumn("Start Baggern", disabled=True),
                        "feststoff": st.column_config.NumberColumn("Ladung - Feststoff (m³)", format="%.0f"),
                        "proz_wert": st.column_config.NumberColumn("Zentrifuge (%)", format="%.1f")
                    },
                    hide_index=True
                )

                # 💾 Überarbeitete Werte wieder speichern
                st.session_state["df_manuell"] = df_editor_display.copy()

                # 📤 Exportbutton zum Speichern der überarbeiteten Tabelle
                now_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                csv_data = df_editor_display.to_csv(index=False).encode("utf-8")
                csv_filename = f"{now_str}_manuell_feststoff.csv"

                st.download_button(
                    label="📥 Manuelle Feststoffwerte als .csv speichern",
                    data=csv_data,
                    file_name=csv_filename,
                    mime="text/csv"
                )
            else:
                st.info("ℹ️ Noch keine Umlaufdaten oder Auswertung geladen.")

        df = mappe_umlaufnummer(df, umlauf_info_df)

#============================================================================================
# 🔵 # Zentralisierte Berechnung nur bei Auswahl eines einzelnen Umlauf
#============================================================================================
    
        # 🎯 Filtere die Daten für den ausgewählten Umlauf (sofern nicht "Alle" gewählt wurde)
        # 👉 Auswahlzeile vorbereiten, falls ein einzelner Umlauf gewählt ist
        zeile = umlauf_info_df[umlauf_info_df["Umlauf"] == umlauf_auswahl] if umlauf_auswahl != "Alle" else pd.DataFrame()
    
        if not zeile.empty:
            # 🧾 Einzelne Zeile (Umlauf) extrahieren
            row = zeile.iloc[0]
        
            # 🗺️ Zeige Karte und erhalte gefilterten DataFrame für diesen Umlauf
            df, _ = zeige_umlauf_info_karte(umlauf_auswahl, zeile, zeitzone, epsg_code, df)
        
            # 🧠 Erstelle Start-/Endstrategien pro Parameter (z. B. Verdrängung, Ladungsvolumen)
            if nutze_schiffstrategie:
                strategie = schiffsparameter.get(schiff, {}).get("StartEndStrategie", {})
            else:
                strategie = {
                    "Verdraengung": {"Start": None, "Ende": None},
                    "Ladungsvolumen": {"Start": None, "Ende": None}
                }
        
            # 📊 Führe zentrale Auswertung für den gewählten Umlauf durch
            berechnungen = berechne_umlauf_auswertung(
                df, row, schiffsparameter, strategie, pf, pw, pb, zeitformat, epsg_code,
                df_manuell=st.session_state.get("df_manuell"),
                nutze_schiffstrategie=nutze_schiffstrategie,
                nutze_gemischdichte=nutze_gemischdichte  # ⬅️ das ist neu!
            )

        
            # 📦 Ergebnisse der Auswertung entpacken
            (
                tds_werte, werte, kennzahlen, strecken, strecke_disp, dauer_disp,
                debug_info, bagger_namen, verbring_namen, amob_dauer, dichtewerte, abrechnung
            ) = berechnungen
        
        else:
            # ⚠️ Kein einzelner Umlauf ausgewählt – Leere Initialisierung
            row = None
            tds_werte = werte = kennzahlen = strecken = strecke_disp = dauer_disp = debug_info = []
            bagger_namen = verbring_namen = []
            amob_dauer = 0.0
            dichtewerte = abrechnung = {}


# ============================================================================================
# 🎨 HTML-Styling für KPI-Panel
#     ➤ Definiert eigene CSS-Klassen zur optischen Gestaltung von Kennzahlen-Panels
#     ➤ Wird später z. B. für die Darstellung von Volumen, Masse etc. genutzt
# ============================================================================================
        
        st.markdown("""
        <style>
            .big-num {
                font-size: 2.5rem;
                font-weight: bold;
            }
            .panel {
                background: #f4f8fc;
                border-radius: 16px;
                padding: 20px;
                margin-bottom: 1.5rem;
            }
            .caption {
                font-size: 1rem;
                color: #555;
            }
            .highlight {
                font-weight: bold;
                font-size: 1.2rem;
                color: #0353a4;
            }
        </style>
        """, unsafe_allow_html=True)
        
        
# ============================================================================================
# 🌐 Karten-Transformer vorbereiten (EPSG → WGS84)
#     ➤ Zur Umrechnung von UTM oder anderen lokalen Koordinaten in GPS-Formate
#     ➤ Voraussetzung für Mapbox-Darstellungen mit Längen-/Breitengraden
# ============================================================================================
        
        from pyproj import Transformer
        if epsg_code:
            transformer = Transformer.from_crs(epsg_code, "EPSG:4326", always_xy=True)
        else:
            transformer = None  # Optional: hier könnte man auch einen Fehler erzwingen bei fehlendem EPSG
        
        
# ============================================================================================
# 🧭 Tab-Auswahl per PILL-Navigation (option_menu)
#     ➤ Darstellung oben in der App, ersetzt klassische Tabs
#     ➤ Optisch moderne Navigation (runde "Pills" mit Icons)
# ============================================================================================
        
        # 🏷️ Klartext-Beschriftungen für Tabs (ohne Emojis)
        tab_labels = [
            "Karte",             # Interaktive Karte mit Fahrtspuren
            "Prozessdaten",      # Zeitverläufe & Sensorwerte
            "Tiefenprofil",      # Baggerkopftiefe
            "Umlauftabelle",     # Zeitliche Übersicht aller Umläufe
            "TDS-Tabellen",      # Abrechnungstabellen (Feststoffmengen etc.)
            "Debug",             # Entwicklermodus mit Detailinfos
            # "Export"           # Optionaler Tab, derzeit deaktiviert
        ]
        
        # 🖼️ Bootstrap-kompatible Icons für jede Tab-Kategorie
        tab_icons = [
            "geo",               # Karte
            "graph-up",          # Prozessdaten
            "activity",          # Tiefenprofil
            "journal-text",      # Umlauftabelle
            "journal-text",      # TDS (nochmals gleiches Icon)
            "tools"              # Debug-Modus
        ]
        
        # 💡 Session-Init: Wähle standardmäßig den ersten Tab aus, wenn kein Zustand gesetzt ist
        if "tab_auswahl" not in st.session_state:
            st.session_state["tab_auswahl"] = tab_labels[0]
        
        # 📌 Darstellung des horizontalen PILL-Menüs über `streamlit-option-menu`
        selected_tab = option_menu(
            menu_title=None,                    # Kein Titel oberhalb der Navigation
            options=tab_labels,                 # Auswahloptionen
            icons=tab_icons,                    # Zugehörige Icons
            orientation="horizontal",           # Horizontal angeordnet
            styles={                            # Anpassung des Designs
                "container": {
                    "padding": "0!important",
                    "background-color": "#FFFFFF"
                },
                "nav-link": {
                    "font-size": "14px",
                    "margin": "0 8px",
                    "border-radius": "999px",   # Runde "Pills"
                    "padding": "8px 18px",
                    "color": "#333"
                },
                "nav-link-selected": {
                    "background-color": "#EBF2FC",
                    "color": "#3C598C"
                }
            },
            default_index=tab_labels.index(st.session_state["tab_auswahl"]),
            key="tab_auswahl"                   # Streamlit-State-Schlüssel
        )
        
        # 🧠 Ausgewählten Tab für die nachfolgende Logik zugänglich machen
        selected_tab = st.session_state["tab_auswahl"]
        
        





# ============================================================================================
# Tab 1 - Übersichtskarten
# ============================================================================================
        
        if selected_tab == "Karte":
            
            # --------------------------------------------------------------------------------------------------------------------------
            # 🌐 Karten-Transformer vorbereiten (für Plotly/Mapbox)
            # --------------------------------------------------------------------------------------------------------------------------
            transformer = Transformer.from_crs(epsg_code, "EPSG:4326", always_xy=True)
            zeit_suffix = "UTC" if zeitzone == "UTC" else "Lokal"
        
            # --------------------------------------------------------------------------------------------------------------------------
            # 📌 Anzeige bei Auswahl eines einzelnen Umlaufs
            # --------------------------------------------------------------------------------------------------------------------------
            if umlauf_auswahl != "Alle" and row is not None:
                # 🔍 Karte vorbereiten mit Info
                df_karten, _ = zeige_umlauf_info_karte(umlauf_auswahl, zeile, zeitzone, epsg_code, df)
        
                # 🕓 Zeitbasierte Polygon-Auswertung
                bagger_df = berechne_punkte_und_zeit_cached(df, statuswert=2)
                bagger_zeiten = bagger_df["Zeit_Minuten"].to_dict()
        
                verbring_df = berechne_punkte_und_zeit_cached(df, statuswert=4)
                verbring_zeiten = verbring_df["Zeit_Minuten"].to_dict()
        
                # 🧩 Bagger-/Verbring-Felder anzeigen
                zeige_bagger_und_verbringfelder(
                    bagger_namen=bagger_namen,
                    verbring_namen=verbring_namen,
                    df=df,
                    baggerfelder=baggerfelder
                )
      
            # --------------------------------------------------------------------------------------------------------------------------
            # 📌 Anzeige bei "Alle" – einfache Übersicht ohne Detailauswertung
            # --------------------------------------------------------------------------------------------------------------------------
            else:
                bagger_namen = []
                verbring_namen = []
                if "Polygon_Name" in df.columns and "Status_neu" in df.columns:
                    bagger_namen = sorted(df.loc[df["Status_neu"] == "Baggern", "Polygon_Name"].dropna().unique())
                    verbring_namen = sorted(df.loc[df["Status_neu"] == "Verbringen", "Polygon_Name"].dropna().unique())

        
                zeige_bagger_und_verbringfelder(
                    bagger_namen=bagger_namen,
                    verbring_namen=verbring_namen,
                    df=df,
                    baggerfelder=baggerfelder
                )
        
            # --------------------------------------------------------------------------------------------------------------------------
            # 🗺️ Kartenansichten nebeneinander (links = Baggern, rechts = Verbringen)
            # --------------------------------------------------------------------------------------------------------------------------
            col1, col2 = st.columns(2)
        
            # --------------------------------------------------------------------------------------------------------------------------
            # 🟦 Linke Karte: Status 2 – Baggerstelle
            # --------------------------------------------------------------------------------------------------------------------------
            # 📌 Sicherstellen, dass Umlaufnummern vorhanden und korrekt sind


            with col1:
                fig, df_status2, df_456 = plot_karte(
                    df=df,
                    transformer=transformer,
                    seite=seite,
                    status2_label="Status 2 (Baggern)",
                    tiefe_spalte="Abs_Tiefe_Kopf_BB" if seite in ["BB", "BB+SB"] else "Abs_Tiefe_Kopf_SB",
                    mapbox_center={"lat": 53.5, "lon": 8.2},
                    zeitzone=zeitzone,
                    zeit_suffix=zeit_suffix,
                    baggerfelder=baggerfelder,
                    dichte_polygone=st.session_state.get("dichte_polygone"),
                    show_status1=show_status1_b,
                    show_status2=show_status2_b,
                    show_status3=show_status3_b,
                    show_status456=show_status456_b
                )
        
                if show_status2_b and not df_status2.empty:
                    map_center, zoom = berechne_map_center_zoom(df_status2, transformer)
                    fig.update_layout(mapbox_center=map_center, mapbox_zoom=zoom)
                elif show_status2_b:
                    st.info("Keine Daten mit Status 2 verfügbar.")
        
                st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True}, key="karte_baggerstelle")
        
            # --------------------------------------------------------------------------------------------------------------------------
            # 🟥 Rechte Karte: Status 4/5/6 – Verbringstelle
            # --------------------------------------------------------------------------------------------------------------------------
            with col2:
                fig, df_status2, df_456 = plot_karte(
                    df=df,
                    transformer=transformer,
                    seite=seite,
                    status2_label="Status 2 (Verbringen)",
                    tiefe_spalte="Abs_Tiefe_Kopf_BB" if seite in ["BB", "BB+SB"] else "Abs_Tiefe_Kopf_SB",
                    mapbox_center={"lat": 53.5, "lon": 8.2},
                    zeitzone=zeitzone,
                    zeit_suffix=zeit_suffix,
                    baggerfelder=baggerfelder,
                    show_status1=show_status1_v,
                    show_status2=show_status2_v,
                    show_status3=show_status3_v,
                    show_status456=show_status456_v
                )
        
                if show_status456_v and not df_456.empty:
                    map_center, zoom = berechne_map_center_zoom(df_456, transformer)
                    fig.update_layout(mapbox_center=map_center, mapbox_zoom=zoom)
                elif show_status456_v:
                    st.info("Keine Daten mit Status 4, 5 oder 6 verfügbar.")
        
                st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True}, key="karte_verbringstelle")
        
            # --------------------------------------------------------------------------------------------------------------------------
            # 📏 Streckenanzeige (sofern Kennzahlen vorhanden)
            # --------------------------------------------------------------------------------------------------------------------------
            if kennzahlen:
                st.markdown("#### Strecken im Umlauf")
                zeige_strecken_panels(
                    strecke_disp["leerfahrt"], strecke_disp["baggern"], strecke_disp["vollfahrt"],
                    strecke_disp["verbringen"], strecke_disp["gesamt"],
                    dauer_disp["leerfahrt"], dauer_disp["baggern"], dauer_disp["vollfahrt"],
                    dauer_disp["verbringen"], dauer_disp["umlauf"],
                    strecken_panel_template
                )

#============================================================================================
# Tab 2 - Diagramm Prozessdaten
#============================================================================================
        
        elif selected_tab == "Prozessdaten":
            st.markdown("#### Umlaufgrafik – Prozessdaten")
        
            if umlauf_auswahl != "Alle" and row is not None and tds_werte is not None:

                # ----------------------------------------------------------------------------------------------------------------------
                # 📦 Baggerdaten anzeigen: Masse, Volumen, Feststoffe, Bodenvolumen, Dichten
                # ----------------------------------------------------------------------------------------------------------------------
                    zeige_baggerwerte_panels(kennzahlen, tds_werte, zeitzone, pw, pf, pb, panel_template, dichte_panel_template)
                    
                # ----------------------------------------------------------------------------------------------------------------------
                # 📦 Baggerdaten als Diagramm
                # ----------------------------------------------------------------------------------------------------------------------                    
                    zeige_prozessgrafik_tab(df_context, zeitzone, row, schiffsparameter, schiff, werte, seite, plot_key="prozessgrafik_tab2")

                # ----------------------------------------------------------------------------------------------------------------------
                # 📦 Abrechnung pro Umlauf
                # ----------------------------------------------------------------------------------------------------------------------
                    zeige_bonus_abrechnung_panels(tds_werte, dichtewerte, abrechnung, pw, pf, panel_template)                
                
                # ----------------------------------------------------------------------------------------------------------------------
                # 📊 Zeitliche Phasen anzeigen (Leerfahrt, Baggern und Strecken)
                # ----------------------------------------------------------------------------------------------------------------------
                    zeige_statuszeiten_panels_mit_strecke(row, zeitzone, zeitformat, strecken=strecke_disp, panel_template=status_panel_template_mit_strecke)

            else:
                st.info("Bitte einen konkreten Umlauf auswählen.")

# ============================================================================================
# Tab 3 - Diagramm Tiefe Baggerkopf (Modularisiert)
# ============================================================================================
       
        elif selected_tab == "Tiefenprofil":
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
                
#============================================================================================
# Tab 4 - Umlauftabelle - gesamt 
#============================================================================================

        elif selected_tab == "Umlauftabelle":
            st.markdown("#### Auflistung aller Umläufe")
        
            if not umlauf_info_df.empty:
                # ✅ Extrahiere ALLE Umlauf-Startzeiten (unabhängig von Filtersicht)
        
                # 📅 Erzeuge Tabelle mit einzelnen Umläufen und ihren Zeitabschnitten
                df_umlaeufe, list_leer, list_bagg, list_voll, list_verk, list_umlauf = erzeuge_umlauftabelle_cached(
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
                # 🔢 Tabelle der Einzelumläufe
                st.dataframe(df_umlaeufe, use_container_width=True, hide_index=True)

                # ➕ Panels für Gesamtdauer statt langweilige Tabelle
                st.markdown("#### Aufsummierte Dauer")
                zeige_aufsummierte_dauer_panels(df_gesamt)
            else:
                st.info("⚠️ Es wurden keine vollständigen Umläufe erkannt.")
          
# ======================================================================================================================
# # Tab 5 – 💠 UMLAUFTABELLE: TDS-Berechnung pro Umlauf
# ======================================================================================================================
        
        # Dieser Tab dient der Anzeige, manuellen Ergänzung und Berechnung von TDS-Kennzahlen je Umlauf
        elif selected_tab == "TDS-Tabellen":

            st.markdown("#### TDS Berechnung pro Umlauf")
        
            # 🛑 Sicherheitsprüfung: Sind manuelle Feststoffdaten vorhanden?
            if "df_manuell" not in st.session_state or st.session_state["df_manuell"].empty:
                st.warning("⚠️ Keine Feststoffdaten vorhanden. Bitte CSV oder Excel über die Sidebar laden.")
                st.stop()
        
            # 🔀 Prüfung der Umlauf-Auswahl – nur "Alle" erlaubt für TDS-Gesamttabelle
            selected_umlauf = st.session_state.get("umlauf_auswahl", "Alle")
            if selected_umlauf != "Alle":
                st.info("🔁 Bitte 'Alle' im Umlauf-Auswahlmenü wählen, um TDS-Tabelle zu berechnen.")
            else:
                # 🔘 Button zur Berechnung aktivieren
                if st.button("📊 TDS-Tabelle berechnen"):
                    # 🚀 Starte zentrale Strategie-Definition (falls schiffspezifisch gewünscht)
                    strategie = (
                        schiffsparameter.get(schiffsnamen[0], {}).get("StartEndStrategie", {})
                        if nutze_schiffstrategie else
                        {"Verdraengung": {"Start": None, "Ende": None}, "Ladungsvolumen": {"Start": None, "Ende": None}}
                    )
        
                    # ⏳ Starte TDS-Berechnung für alle Umläufe
                    with st.spinner("🔄 Berechne TDS-Kennzahlen für alle Umläufe..."):
                        df_tabelle, df_tabelle_export = erzeuge_tds_tabelle(
                            df, umlauf_info_df_all, schiffsparameter, strategie, pf, pw, pb, zeitformat, epsg_code
                        )
        
                        # 📦 Ergebnisse in Session speichern
                        st.session_state["tds_df"] = df_tabelle
                        st.session_state["tds_df_export"] = df_tabelle_export
        
                        # 💾 Export als Excel vorbereiten (2 Tabellenblätter)
                        now_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        excel_buffer = io.BytesIO()
                        df_export_flat = df_tabelle_export.copy()
                        df_export_flat.columns = [
                            " - ".join(col).strip() if isinstance(col, tuple) else col
                            for col in df_export_flat.columns
                        ]
        
                        with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
                            # 📄 Export-Tabelle (roh)
                            df_export_flat.to_excel(writer, sheet_name="TDS-Werte", startrow=2, index=False, header=False)
                            worksheet = writer.sheets["TDS-Werte"]
                            for col_num, header in enumerate(df_export_flat.columns):
                                worksheet.write(0, col_num, header)
        
                            # 📊 Anzeige-Tabelle (formatiert)
                            df_anzeige = df_tabelle.copy()
                            df_anzeige.columns = [
                                " - ".join(col).strip() if isinstance(col, tuple) else col
                                for col in df_anzeige.columns
                            ]
                            df_anzeige.to_excel(writer, sheet_name="TDS-Anzeige", index=False)
        
                        # Speichern im Session-State
                        st.session_state["export_excel"] = excel_buffer.getvalue()
                        st.session_state["export_excel_filename"] = f"{now_str}_TDS_Tabelle.xlsx"
        
            # 📋 TDS-Tabelle anzeigen, wenn vorhanden
            if "tds_df" in st.session_state:
                st.dataframe(st.session_state["tds_df"], use_container_width=True, hide_index=True)
        
            # 📥 Export-Button für XLSX
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
            # 📍 Verbringstellen-Tabelle (WSA-konform)
            # ---------------------------------------------------------------------------------------------------------------------
            st.markdown("---")   
            st.markdown("#### Verbringstellen-Tabelle")
        
            if not df.empty:
                # 🧮 Berechnung der Verbringstellen (Zeitpunkt & Polygon)
                df_verbring_tab = erzeuge_verbring_tabelle(
                    df_ungefiltert,
                    umlauf_info_df_all,
                    transformer,
                    zeitzone=zeitzone,
                    status_col="Status_neu"
                )
        
                if df_verbring_tab.empty:
                    st.warning("⚠️ Keine Verbringstellen erkannt. Prüfe Polygone und Statuswerte (4/5/6).")
                else:
                    # 🖥️ Tabelle anzeigen
                    st.dataframe(df_verbring_tab, use_container_width=True, hide_index=True)
        
                    # 📁 Excel-Export ermöglichen
                    df_verbring_export = df_verbring_tab.copy()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    dateiname = f"Verbringstellen_WSA_{schiff}_{timestamp}.xlsx"
        
                    excel_buffer = io.BytesIO()
                    df_verbring_export.to_excel(excel_buffer, index=True)
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

        elif selected_tab == "Debug":
            if umlauf_auswahl != "Alle" and row is not None:

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
                # 📦 Abrechnung pro Umlauf
                # ----------------------------------------------------------------------------------------------------------------------
                    st.markdown("---")
                    st.markdown("#### Abrechnung pro Umlauf", unsafe_allow_html=True)
                    
                    zeige_bonus_abrechnung_panels(tds_werte, dichtewerte, abrechnung, pw, pf, panel_template)


               
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
                        st.dataframe(umlauf_info_df)
                     
                    # ----------------------------------------------------------------------------------------------------------------------
                    # 📊 Vorschau: Rohdaten
                    # ----------------------------------------------------------------------------------------------------------------------                        
                    with st.expander("🔍 Vorschau: Rohdaten (erste 20 Zeilen)", expanded=False):
                        if not df.empty:
                            st.caption(f"📄 Zeige die ersten 20 von insgesamt {len(df)} Zeilen")
                            st.dataframe(df.head(20), use_container_width=True)
                        else:
                            st.info("ℹ️ Noch keine Daten geladen.")
                     
                     
                        
                    # ----------------------------------------------------------------------------------------------------------------------
                    # 📊 Debug-Infos (ausklappbar) – Verweilzeiten pro Polygon
                    # ----------------------------------------------------------------------------------------------------------------------
                                        
                    with st.expander("📊 Verweilzeiten pro Polygon"):
                        df_bagger = berechne_punkte_und_zeit_cached(df, statuswert=2)
                        df_verbring = berechne_punkte_und_zeit_cached(df, statuswert=4)
            
                        st.write("**Baggerzeiten pro Feld (Status 2):**")
                        st.dataframe(df_bagger)
            
                        st.write("**Verbringzeiten pro Feld (Status 4):**")
                        st.dataframe(df_verbring) 
                        
                    # ----------------------------------------------------------------------------------------------------------------------
                    # 📊 Debug-Infos (ausklappbar) – Verweilzeiten pro Dichte Polygon
                    # ----------------------------------------------------------------------------------------------------------------------                    
                    with st.expander("📌 Häufigkeit Dichtepolygone"):
                        if "Dichte_Polygon_Name" in df.columns:
                            df_polygone = df["Dichte_Polygon_Name"].dropna()
                    
                            if not df_polygone.empty:
                                anzahl_gesamt = len(df_polygone)
                                haeufigkeit_df = (
                                    df_polygone.value_counts()
                                    .rename_axis("Polygon")
                                    .reset_index(name="Anzahl")
                                )
                                haeufigkeit_df["Anteil (%)"] = (haeufigkeit_df["Anzahl"] / anzahl_gesamt * 100).round(2)
                    
                                st.dataframe(haeufigkeit_df, use_container_width=True)
                            else:
                                st.info("Keine Polygon-Daten vorhanden in dieser Datei.")
                        else:
                            st.warning("Spalte 'Dichte_Polygon_Name' nicht gefunden.")                    
                    
                    # ----------------------------------------------------------------------------------------------------------------------
                    # 📊 Statuswerte im Umlauf
                    # ----------------------------------------------------------------------------------------------------------------------                     
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


                    # ----------------------------------------------------------------------------------------------------------------------
                    # 📊 AMOB im Umlauf (erweiterter Debug)
                    # ----------------------------------------------------------------------------------------------------------------------
                    with st.expander("🧪 AMOB-Dauer (Debug-Ausgabe)", expanded=False):
                        st.write("📦 Umlauf-Info vorhanden:", not umlauf_info_df.empty)
                        st.write("📦 Zeitreihe vorhanden:", not df.empty)
                    
                        if amob_dauer is not None:
                            st.success(f"✅ AMOB-Zeit für diesen Umlauf: **{amob_dauer:.1f} Sekunden**")
                    
                            # 🔍 Typen checken
                            st.code(f"Typ von row['Umlauf']: {type(row['Umlauf'])}")
                            st.code(f"Typ von df['Umlauf']: {df['Umlauf'].dtype}")
                    
                            # 🔍 Status-Werte prüfen
                            st.write("🧾 Eindeutige Werte in Status_neu:")
                            st.dataframe(pd.DataFrame(df["Status_neu"].dropna().unique(), columns=["value"]))
                    
                            # 🔁 Verfügbare Umläufe
                            st.write("🔁 Vorhandene Umläufe im DF:")
                            st.dataframe(pd.DataFrame(df["Umlauf"].dropna().unique(), columns=["value"]))
                    
                            # 📌 Aktueller Umlauf
                            st.write("📌 Aktuell untersuchter Umlauf:", row["Umlauf"])
                    
                            # 📏 Anzahl Status=Baggern insgesamt
                            df_bagger_status = df[df["Status_neu"] == "Baggern"]
                            st.write(f"🔍 Anzahl Punkte mit Status_neu = 'Baggern' (gesamt): {len(df_bagger_status)}")
                    
                            # ✅ Typen angleichen
                            umlauf_id = str(row["Umlauf"])
                            df["Umlauf"] = df["Umlauf"].astype(str)
                    
                            df_bagg = df[(df["Umlauf"] == umlauf_id) & (df["Status_neu"] == "Baggern")].copy()
                            st.write(f"🔍 ...davon im aktuellen Umlauf: {len(df_bagg)}")
                    
                            if not df_bagg.empty:
                                df_bagg = df_bagg.sort_values("timestamp")
                                df_bagg["delta_t"] = df_bagg["timestamp"].diff().dt.total_seconds().fillna(0)
                                df_bagg["delta_t"] = df_bagg["delta_t"].apply(lambda x: x if x <= 30 else 0)  # Gaps >30 s ignorieren
                                bagger_dauer_s = df_bagg["delta_t"].sum()
                    
                                anteil = (amob_dauer / bagger_dauer_s * 100) if bagger_dauer_s > 0 else 0
                                st.info(f"🔍 Baggerdauer: **{bagger_dauer_s:.1f} s**, AMOB-Anteil: **{anteil:.1f} %**")
                            else:
                                st.warning("⚠️ Keine Datenpunkte mit Status_neu = 'Baggern' im gewählten Umlauf gefunden.")
                    
                        else:
                            st.warning("⚠️ AMOB-Dauer wurde nicht berechnet oder ist `None`.")

                    # -----------------------------------------------------------------------------------------------------------------
                    # 📊 Dataframe
                    # -----------------------------------------------------------------------------------------------------------------            
                    with st.expander("🧪 Debug: Spalten im DataFrame"):
                        st.write("🧾 Spalten im DataFrame:", df.columns.tolist())
                         # Debug-Tabelle: Übersicht Dichtewerte je Umlauf

                    # ----------------------------------------------------------------------------------------------------------------------
                    # 📊 Abrechnungsfaktor
                    # ---------------------------------------------------------------------------------------------------------------------
                    with st.expander("📊 Debug: Abrechnungsfaktor", expanded=False):
                        st.write("🔢 Abrechnungsdaten:")
                        st.json(abrechnung)
        
  
            else:
                st.info("Bitte einen konkreten Umlauf auswählen.")
            

#=====================================================================================




elif not uploaded_files:
    st.info("Bitte lade mindestens eine Datei mit Baggerinformationen im Format MoNa- oder HPA hoch.")

