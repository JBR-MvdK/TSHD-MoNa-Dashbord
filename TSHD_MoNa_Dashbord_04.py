#==============================================================================================================================
# 🔵 Imports und Hilfsfunktionen
#==============================================================================================================================

# === 🔧 Basis-Module ===
import os              # Für Dateipfade, Dateioperationen, Existenzprüfungen etc.
import json            # Zum Lesen und Schreiben von JSON-Dateien (z. B. Konfiguration)
import pandas as pd    # Pandas ist essenziell für DataFrame-basierte Datenverarbeitung
import numpy as np     # Numpy für numerische Berechnungen und Masken
import pytz            # Zeitzonenmanagement (z. B. für Umrechnungen in UTC)
import traceback

# === 📊 Visualisierung & UI ===
import streamlit as st               # Streamlit steuert die gesamte Benutzeroberfläche
import plotly.graph_objects as go    # Für interaktive Diagramme (z. B. Zeitreihen oder Scatterplots)

# === 🌍 Geodaten & Geometrie ===
from shapely.geometry import Point   # Wird z. B. für Geo-Punkte zur Feldprüfung genutzt

# === 🧩 Eigene Module (Funktionsbausteine) ===
# Diese Module hast du selbst geschrieben und in separate .py-Dateien ausgelagert.

# Datenimport & TDS-Berechnung (z. B. Dichten, Konzentrationen)
from modul_tshd_mona_import import parse_mona, berechne_tds_parameter

# Umlauf-Erkennung (Zeitlogik, Segmentierung)
from modul_umlaeufe import nummeriere_umlaeufe, extrahiere_umlauf_startzeiten

# Baggerseite (Backbord / Steuerbord) automatisch erkennen
from modul_baggerseite import erkenne_baggerseite

# Koordinatensystem automatisch erkennen (z. B. UTM, Gauß-Krüger)
from modul_koordinatenerkennung import erkenne_koordinatensystem

# XML-Import für Baggerfelder
from modul_baggerfelder_xml_import import parse_baggerfelder

# Berechnung der Solltiefe anhand der Felder oder Eingabewerte
from modul_solltiefe_tshd import berechne_solltiefe_fuer_df

# Streckenberechnung je nach Status (Leerfahrt, Baggern usw.)
from modul_strecken import berechne_strecken

# Berechnung der Kennzahlen für jeden Umlauf (Verdraengung, Volumen usw.)
from modul_umlauf_kennzahl import berechne_umlauf_kennzahlen

from modul_startend_strategie import berechne_start_endwerte

#==============================================================================================================================
# 🔵 Hilfsfunktionen
#==============================================================================================================================

# === 📋 DataFrame-Hilfsfunktionen ===

def split_by_gap(df, max_gap_minutes=2):
    """
    Teilt einen DataFrame in Segmente auf, wenn Lücken zwischen Zeitstempeln größer als max_gap_minutes sind.
    """
    df = df.sort_values(by="timestamp")
    df["gap"] = df["timestamp"].diff().dt.total_seconds() > (max_gap_minutes * 60)
    df["segment"] = df["gap"].cumsum()
    return df

# === 🕒 Zeit- und Zeitzonenfunktionen ===

def convert_timestamp(ts, zeitzone):
    """
    Konvertiert einen Zeitstempel in die angegebene Zeitzone (UTC oder Europe/Berlin).
    """
    if ts is None or pd.isnull(ts):
        return None
    if zeitzone == "UTC":
        return ts.tz_localize("UTC") if ts.tzinfo is None else ts.astimezone(pytz.UTC)
    elif zeitzone == "Lokal (Europe/Berlin)":
        return ts.tz_localize("UTC").astimezone(pytz.timezone("Europe/Berlin")) if ts.tzinfo is None else ts.astimezone(pytz.timezone("Europe/Berlin"))
    return ts

def format_time(ts, zeitzone):
    """
    Formatiert einen Zeitstempel (je nach Zeitzone) als lesbaren String.
    """
    ts_conv = convert_timestamp(ts, zeitzone)
    return "-" if ts_conv is None or pd.isnull(ts_conv) else ts_conv.strftime("%d.%m.%Y %H:%M:%S")

def plot_x(df, mask, zeitzone):
    """
    Gibt Zeitstempel-Spalte (timestamp) mit korrekt angepasster Zeitzone zurück.
    """
    col = "timestamp"
    if zeitzone == "Lokal (Europe/Berlin)":
        return df.loc[mask, col].dt.tz_convert("Europe/Berlin")
    return df.loc[mask, col]



# === ⚙️ Schiffsspezifische Parameter laden und prüfen ===

def lade_schiffsparameter(pfad="schiffsparameter.json"):
    """
    Lädt schiffsspezifische Parameter (Grenzwerte) aus einer JSON-Datei.
    """
    if os.path.exists(pfad):
        try:
            with open(pfad, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            st.sidebar.error(f"❌ Fehler in JSON-Datei: {e}")
            return {}
    else:
        return {}

def pruefe_werte_gegen_schiffsparameter(df, schiff_name, parameter_dict):
    """
    Prüft Spaltenwerte im DataFrame gegen Grenzwerte aus den Schiffsparametern.
    Entfernt fehlerhafte Zeilen und gibt Info über entfernte Werte.
    """
    if schiff_name not in parameter_dict:
        return df, []

    fehlerhafte_werte = []
    limits = parameter_dict[schiff_name]

    for spalte, grenz in limits.items():
        if spalte in df.columns:
            mask = pd.Series([True] * len(df))

            if grenz.get("min") is not None:
                mask &= df[spalte] >= grenz["min"]

            if grenz.get("max") is not None:
                mask &= df[spalte] <= grenz["max"]

            entfernt = (~mask).sum()
            if entfernt > 0:
                fehlerhafte_werte.append((spalte, entfernt))
                df = df[mask]

    return df, fehlerhafte_werte

#==============================================================================================================================
# 🔵 Hilfsfunktionen für die Dauer-Formatierung
#==============================================================================================================================

# === ⏳ Dauer-Formatierungsfunktionen ===

def to_hhmmss(td):
    try:
        if pd.isnull(td) or td is None:
            return "-"
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    except:
        return "-"

def to_dezimalstunden(td):
    try:
        if pd.isnull(td) or td is None:
            return "-"
        value = td.total_seconds() / 3600
        stunden_formatiert = f"{value:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{stunden_formatiert} h"
    except:
        return "-"

def to_dezimalminuten(td):
    try:
        if pd.isnull(td) or td is None:
            return "-"
        return f"{int(td.total_seconds() // 60):,} min".replace(",", ".")
    except:
        return "-"

def format_dauer(td, zeitformat="dezimalminuten"):
    if td is None or pd.isnull(td):
        return "-"
    
    if zeitformat == "hh:mm:ss":
        return to_hhmmss(td)
    elif zeitformat == "dezimalstunden":
        return to_dezimalstunden(td)
    elif zeitformat == "dezimalminuten":
        return to_dezimalminuten(td)
    else:
        return "-"


# === 🧮 Sichere Berechnung von Zeitdauern ===
def sichere_dauer(start, ende, zeitformat):
    if pd.notnull(start) and pd.notnull(ende):
        return format_dauer(ende - start, zeitformat)
    return "-"
    
# -----------------------------------------------
# Hilfsfunktionen (global verwendbar)
# -----------------------------------------------

def sichere_zeit(ts):
    if ts is None or pd.isnull(ts):
        return "-"
    return format_time(ts, zeitzone)
    
    
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
        min_value=1.5, max_value=2.5,
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




        

#==============================================================================================================================
# 🔵 Tabs definieren
#==============================================================================================================================

# Tabs für die verschiedenen Visualisierungen
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🗺️ Karte",
            "📈 Prozess",
            "📉 Tiefe",
            "📋 Umläufe - gesamt",
            "📋 Umlauf - Auswertung"
        ])

    

#==============================================================================================================================
# Tab - Übersichtskarten 
#==============================================================================================================================

        with tab1:
        
            from pyproj import Transformer  # Importiere Koordinatentransformation
        
            # --- 1. Aufbau der Umlauf-Info-Tabelle über der Karte ---
            if umlauf_auswahl != "Alle":
                if zeile.empty:
                    # Falls der ausgewählte Umlauf unvollständig ist (z.B. fehlender Abschlussstatus)
                    st.warning("⚠️ Kein vollständiger Umlauf: Der ausgewählte Umlauf ist unvollständig (endet z. B. nicht mit Status 4, 5 oder 6). "
                               "Es werden trotzdem alle Rohdaten und Karten angezeigt.")
                else:
                    try:
                        # Zeile für den ausgewählten Umlauf laden
                        row = zeile.iloc[0]
        
                        # Start-/Endzeiten der verschiedenen Phasen (Leerfahrt, Baggern, Vollfahrt, Verbringen)
                        phase_keys = [
                            ("Start Leerfahrt", "anzeige_start_leerfahrt"),
                            ("Start Baggern", "anzeige_start_baggern"),
                            ("Start Vollfahrt", "anzeige_start_vollfahrt"),
                            ("Start Verklappen/Pump/Rainbow", "anzeige_start_verklapp"),
                            ("Ende", "anzeige_ende_umlauf")
                        ]
                        phase_times = {}
                        for key, out in phase_keys:
                            t = row.get(key, None)
                            phase_times[out] = convert_timestamp(pd.Timestamp(t) if t is not None else None, zeitzone) if t is not None else None
        
                        # Prüfen, ob überhaupt ein vollständiger Zeitbereich existiert
                        if phase_times["anzeige_start_leerfahrt"] is None or phase_times["anzeige_ende_umlauf"] is None:
                            st.warning("⚠️ Kein vollständiger Umlauf: Beginn oder Ende fehlt (kein Status 1 oder 4/5/6 erkannt).")
                        else:
                            # Filtere das DataFrame auf den gewählten Umlauf-Zeitraum
                            df = df[(df["timestamp"] >= phase_times["anzeige_start_leerfahrt"]) & 
                                    (df["timestamp"] <= phase_times["anzeige_ende_umlauf"])]
        
                            # Berechnung der Dauer für jede Phase
                            dauer_leerfahrt = (phase_times["anzeige_start_baggern"] - phase_times["anzeige_start_leerfahrt"]) if phase_times["anzeige_start_baggern"] else None
                            dauer_baggern = (phase_times["anzeige_start_vollfahrt"] - phase_times["anzeige_start_baggern"]) if phase_times["anzeige_start_baggern"] and phase_times["anzeige_start_vollfahrt"] else None
                            dauer_vollfahrt = (phase_times["anzeige_start_verklapp"] - phase_times["anzeige_start_vollfahrt"]) if phase_times["anzeige_start_vollfahrt"] and phase_times["anzeige_start_verklapp"] else None
                            dauer_verklapp = (phase_times["anzeige_ende_umlauf"] - phase_times["anzeige_start_verklapp"]) if phase_times["anzeige_start_verklapp"] and phase_times["anzeige_ende_umlauf"] else None
                            dauer_umlauf = (phase_times["anzeige_ende_umlauf"] - phase_times["anzeige_start_leerfahrt"]) if phase_times["anzeige_ende_umlauf"] else None
        
                            # Formatierte Anzeige der Dauern
                            dauer_leerfahrt_disp = format_dauer(dauer_leerfahrt)
                            dauer_baggern_disp = format_dauer(dauer_baggern)
                            dauer_vollfahrt_disp = format_dauer(dauer_vollfahrt)
                            dauer_verbringen_disp = format_dauer(dauer_verklapp)
                            dauer_umlauf_disp = format_dauer(dauer_umlauf)
        
                            # Erstellung der Tabellenstruktur (mit MultiIndex für saubere Spaltenüberschriften)
                            columns = pd.MultiIndex.from_tuples([
                                ("Umlauf", "Nr."),
                                ("Datum", ""),
                                ("Leerfahrt", "Beginn"), ("Leerfahrt", "Dauer"),
                                ("Baggern", "Beginn"), ("Baggern", "Dauer"),
                                ("Vollfahrt", "Beginn"), ("Vollfahrt", "Dauer"),
                                ("Verklappen", "Beginn"), ("Verklappen", "Dauer"),
                                ("Umlauf", "Ende"), ("Umlauf", "Dauer")
                            ])
        
                            # Einfügen der Werte in die Tabelle
                            data = [[
                                row.get("Umlauf", "-"),
                                phase_times["anzeige_start_leerfahrt"].strftime("%d.%m.%Y") if phase_times["anzeige_start_leerfahrt"] else "-",
                                phase_times["anzeige_start_leerfahrt"].strftime("%H:%M:%S") if phase_times["anzeige_start_leerfahrt"] else "-",
                                format_dauer(dauer_leerfahrt),
                                phase_times["anzeige_start_baggern"].strftime("%H:%M:%S") if phase_times["anzeige_start_baggern"] else "-",
                                format_dauer(dauer_baggern),
                                phase_times["anzeige_start_vollfahrt"].strftime("%H:%M:%S") if phase_times["anzeige_start_vollfahrt"] else "-",
                                format_dauer(dauer_vollfahrt),
                                phase_times["anzeige_start_verklapp"].strftime("%H:%M:%S") if phase_times["anzeige_start_verklapp"] else "-",
                                format_dauer(dauer_verklapp),
                                phase_times["anzeige_ende_umlauf"].strftime("%H:%M:%S") if phase_times["anzeige_ende_umlauf"] else "-",
                                format_dauer(dauer_umlauf)
                            ]]
                            df_summary = pd.DataFrame(data, columns=columns)
        
                            # Anzeige der Tabelle
                            st.dataframe(df_summary, use_container_width=True, hide_index=True)
        
                    except Exception as e:
                        # Fehlerbehandlung
                        st.warning("⚠️ Der gewählte Umlauf ist unvollständig oder fehlerhaft.")
                        st.info(f"(Details: {e})")
            
            # --- 2. Aufteilung der Kartenanzeige in zwei Spalten ---
            col1, col2 = st.columns(2)
        
            # Transformer: Koordinatensystem von UTM (o.ä.) nach WGS84 (EPSG:4326) vorbereiten
            transformer = Transformer.from_crs(epsg_code, "EPSG:4326", always_xy=True)





    # -------------------------------------------------------------------------------------------------------------------------
    # Definition der Kartenfunktion - linke und rechte Karte basieren auf gleicher Logik
    # -------------------------------------------------------------------------------------------------------------------------
            
            # Wähle Suffix für Zeitangaben je nach Zeitzone
            zeit_suffix = "UTC" if zeitzone == "UTC" else "Lokal"
            
            def plot_karte(
                df,                # Eingabe-DataFrame
                transformer,       # Koordinatentransformation (z.B. UTM -> WGS84)
                seite,             # Baggerseite (BB / SB / BB+SB)
                status2_label,     # Bezeichnung für Status 2 im Plot
                tiefe_spalte,      # Spaltenname für Tiefenanzeige
                mapbox_center,     # Start-Mittelpunkt der Karte
                focus_trace=None   # Optional: zusätzlichen Marker einfügen
            ):
                import plotly.graph_objects as go
                
                fig = go.Figure()  # Neues leeres Plotly-Mapbox-Objekt
                
                # --- Tooltip für Status 2 (zeigt Zeit + Tiefe) ---
                def tooltip_text(row):
                    ts = convert_timestamp(row["timestamp"], zeitzone)
                    zeit = ts.strftime("%d.%m.%Y %H:%M:%S") if ts else "-"
                    tiefe = row.get(tiefe_spalte)
                    tooltip = f"🕒 {zeit} ({zeit_suffix})"
                    if pd.notnull(tiefe):
                        tooltip += f"<br>📉 Tiefe: {tiefe:.2f} m"
                    return tooltip
            
                # --- Tooltip für Status 1, 3, 4, 5, 6 (zeigt Zeit + Geschwindigkeit) ---
                def tooltip_status1_3(row):
                    ts = convert_timestamp(row["timestamp"], zeitzone)
                    zeit = ts.strftime("%d.%m.%Y %H:%M:%S") if ts else "-"
                    tooltip = f"🕒 {zeit} ({zeit_suffix})"
                    geschw = row.get("Geschwindigkeit", None)
                    if pd.notnull(geschw):
                        tooltip += f"<br>🚤 Geschwindigkeit: {geschw:.1f} kn"
                    return tooltip
            
                # -------------------------------------------------------------------------------------------------------------------------
                # Darstellung der verschiedenen Statusbereiche:
                # -------------------------------------------------------------------------------------------------------------------------
            
                # --- Status 1: Leerfahrt (RW_Schiff / HW_Schiff) ---
                df_status1 = df[df["Status"] == 1].dropna(subset=["RW_Schiff", "HW_Schiff"])
                df_status1 = split_by_gap(df_status1)
                for seg_id, segment_df in df_status1.groupby("segment"):
                    coords = segment_df.apply(lambda row: transformer.transform(row["RW_Schiff"], row["HW_Schiff"]), axis=1)
                    lons, lats = zip(*coords)
                    tooltips = segment_df.apply(tooltip_status1_3, axis=1)
                    fig.add_trace(go.Scattermapbox(
                        lon=lons, lat=lats, mode='lines',
                        marker=dict(size=4, color='rgba(150, 150, 150, 0.7)'),
                        line=dict(width=1, color='rgba(150, 150, 150, 0.7)'),
                        text=tooltips, hoverinfo='text',
                        name='Status 1 (Leerfahrt)' if seg_id == 0 else None,
                        showlegend=(seg_id == 0), legendgroup="status1"
                    ))
            
                # --- Status 2: Baggern (RW_BB/HW_BB oder RW_SB/HW_SB je nach Seite) ---
                df_status2 = df[df["Status"] == 2]
                df_status2 = split_by_gap(df_status2)
            
                for seg_id, segment_df in df_status2.groupby("segment"):
                    # Backbord (BB)
                    if seite in ["BB", "BB+SB"]:
                        df_status2_bb = segment_df.dropna(subset=["RW_BB", "HW_BB"])
                        if not df_status2_bb.empty:
                            coords_bb = df_status2_bb.apply(lambda row: transformer.transform(row["RW_BB"], row["HW_BB"]), axis=1)
                            lons_bb, lats_bb = zip(*coords_bb)
                            tooltips_bb = df_status2_bb.apply(tooltip_text, axis=1)
                            fig.add_trace(go.Scattermapbox(
                                lon=lons_bb, lat=lats_bb, mode='lines+markers',
                                marker=dict(size=6, color='rgba(0, 102, 204, 0.8)'),
                                line=dict(width=2, color='rgba(0, 102, 204, 0.8)'),
                                text=tooltips_bb, hoverinfo='text',
                                name="Status 2 (Baggern, BB)" if seg_id == 0 else None,
                                showlegend=(seg_id == 0), legendgroup="status2bb"
                            ))
                    # Steuerbord (SB)
                    if seite in ["SB", "BB+SB"]:
                        df_status2_sb = segment_df.dropna(subset=["RW_SB", "HW_SB"])
                        if not df_status2_sb.empty:
                            coords_sb = df_status2_sb.apply(lambda row: transformer.transform(row["RW_SB"], row["HW_SB"]), axis=1)
                            lons_sb, lats_sb = zip(*coords_sb)
                            tooltips_sb = df_status2_sb.apply(tooltip_text, axis=1)
                            fig.add_trace(go.Scattermapbox(
                                lon=lons_sb, lat=lats_sb, mode='lines+markers',
                                marker=dict(size=6, color='rgba(0, 204, 102, 0.8)'),
                                line=dict(width=2, color='rgba(0, 204, 102, 0.8)'),
                                text=tooltips_sb, hoverinfo='text',
                                name="Status 2 (Baggern, SB)" if seg_id == 0 else None,
                                showlegend=(seg_id == 0), legendgroup="status2sb"
                            ))
            
                # --- Status 3: Vollfahrt (RW_Schiff / HW_Schiff) ---
                df_status3 = df[df["Status"] == 3].dropna(subset=["RW_Schiff", "HW_Schiff"])
                df_status3 = split_by_gap(df_status3)
                for seg_id, segment_df in df_status3.groupby("segment"):
                    coords = segment_df.apply(lambda row: transformer.transform(row["RW_Schiff"], row["HW_Schiff"]), axis=1)
                    lons, lats = zip(*coords)
                    tooltips = segment_df.apply(tooltip_status1_3, axis=1)
                    fig.add_trace(go.Scattermapbox(
                        lon=lons, lat=lats, mode='lines',
                        marker=dict(size=5, color='rgba(0, 153, 76, 0.8)'),
                        line=dict(width=1, color='rgba(0, 153, 76, 0.8)'),
                        text=tooltips, hoverinfo='text',
                        name='Status 3 (Vollfahrt)' if seg_id == 0 else None,
                        showlegend=(seg_id == 0), legendgroup="status3"
                    ))
            
                # --- Status 4/5/6: Verbringen (RW_Schiff / HW_Schiff) ---
                df_456 = df[df["Status"].isin([4, 5, 6])].dropna(subset=["RW_Schiff", "HW_Schiff"])
                df_456 = split_by_gap(df_456)
                for seg_id, segment_df in df_456.groupby("segment"):
                    coords = segment_df.apply(lambda row: transformer.transform(row["RW_Schiff"], row["HW_Schiff"]), axis=1)
                    lons, lats = zip(*coords)
                    tooltips = segment_df.apply(tooltip_status1_3, axis=1)
                    fig.add_trace(go.Scattermapbox(
                        lon=lons, lat=lats, mode='lines+markers',
                        marker=dict(size=6, color='rgba(255, 140, 0, 0.8)'),
                        line=dict(width=2, color='rgba(255, 140, 0, 0.8)'),
                        text=tooltips, hoverinfo='text',
                        name='Status 4/5/6 (Verbringen)' if seg_id == 0 else None,
                        showlegend=(seg_id == 0), legendgroup="status456"
                    ))
            
                # --- Baggerfelder (Polygone) darstellen ---
                if baggerfelder:
                    for idx, feld in enumerate(baggerfelder):
                        coords = list(feld["polygon"].exterior.coords)
                        lons, lats = zip(*coords)
                        tooltip = f"{feld['name']}<br>Solltiefe: {feld['solltiefe']} m"
                        
                        # Polygon-Umriss und Fläche
                        fig.add_trace(go.Scattermapbox(
                            lon=lons,
                            lat=lats,
                            mode="lines+markers",
                            fill="toself",
                            fillcolor="rgba(50, 90, 150, 0.2)",
                            line=dict(color="rgba(30, 60, 120, 0.8)", width=2),
                            marker=dict(size=3, color="rgba(30, 60, 120, 0.8)"),
                            name="Baggerfelder" if idx == 0 else None,
                            legendgroup="baggerfelder",
                            showlegend=(idx == 0),
                            visible=True,
                            text=[tooltip] * len(lons),
                            hoverinfo="text"
                        ))
                        
                        # Unsichtbarer Marker im Mittelpunkt für Tooltip
                        centroid = feld["polygon"].centroid
                        lon_c, lat_c = centroid.x, centroid.y
                        fig.add_trace(go.Scattermapbox(
                            lon=[lon_c],
                            lat=[lat_c],
                            mode="markers",
                            marker=dict(size=1, color="rgba(0,0,0,0)"),
                            text=[tooltip],
                            hoverinfo="text",
                            showlegend=False
                        ))
            
                # Optional: Zusätzlicher Fokus-Trace einfügen (z.B. Marker für aktuellen Punkt)
                if focus_trace:
                    fig.add_trace(focus_trace)
            
                # --- Layout der Karte anpassen ---
                fig.update_layout(
                    mapbox_style="open-street-map",
                    mapbox_zoom=12,
                    mapbox_center=mapbox_center,
                    height=700,
                    margin=dict(r=0, l=0, t=0, b=0),
                    legend=dict(
                        x=0.01, y=0.99,
                        bgcolor="rgba(255,255,255,0.8)",
                        bordercolor="gray",
                        borderwidth=1
                    )
                )
            
                return fig, df_status2, df_456



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
                    status2_label="Status 2 (Baggern)",                     # Bezeichnung im Legendeneintrag
                    tiefe_spalte="Abs_Tiefe_Kopf_BB" if seite in ["BB", "BB+SB"] else "Abs_Tiefe_Kopf_SB",  # Wahl der Tiefenspalte
                    mapbox_center={"lat": 53.5, "lon": 8.2}                  # Grobe Anfangszentrierung
                )
            
                # Wenn Status 2-Daten vorhanden sind → Zoome auf den ersten Punkt
                if not df_status2.empty:
                    first_latlon = transformer.transform(df_status2.iloc[0]["RW_Schiff"], df_status2.iloc[0]["HW_Schiff"])
                    fig.update_layout(
                        mapbox_center={"lat": first_latlon[1], "lon": first_latlon[0]},
                        mapbox_zoom=13
                    )
                else:
                    st.info("Keine Daten mit Status 2 verfügbar.")
            
                # Überschrift und Karte darstellen
                st.markdown("#### Baggerstelle")
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
                    status2_label="Status 2 (Verbringen)",                    # Bezeichnung hier auf Verbringen gesetzt
                    tiefe_spalte="Abs_Tiefe_Verbring",                        # Spalte für Verbringtiefe
                    mapbox_center={"lat": 53.6, "lon": 8.3}                   # Grobe Anfangszentrierung
                )
            
                # Wenn Status 4/5/6-Daten vorhanden sind → Zoome auf den ersten Punkt
                if not df_456.empty:
                    first_latlon = transformer.transform(df_456.iloc[0]["RW_Schiff"], df_456.iloc[0]["HW_Schiff"])
                    fig.update_layout(
                        mapbox_center={"lat": first_latlon[1], "lon": first_latlon[0]},
                        mapbox_zoom=13
                    )
                else:
                    st.info("Keine Daten mit Status 4, 5 oder 6 verfügbar.")
            
                # Überschrift und Karte darstellen
                st.markdown("#### Verbringstelle")
                st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})


#==============================================================================================================================
# Tab 2 - Diagramm Prozessdaten
#==============================================================================================================================
        
        
        # --- Hilfsfunktion: Bereiche mit bestimmtem Status finden (z.B. Baggern, Verbringen) ---
        def status_bereiche(df, status_liste):
            mask = df["Status"].isin(status_liste)
            indices = mask.astype(int).diff().fillna(0)
            starts = df.index[(indices == 1)].tolist()
            ends = df.index[(indices == -1)].tolist()
            if mask.iloc[0]:
                starts = [df.index[0]] + starts
            if mask.iloc[-1]:
                ends = ends + [df.index[-1]]
            return starts, ends
        


        with tab2:
        
            # --- Strategie-Zeitmarken vorbereiten für vertikale Linien ---
            if umlauf_auswahl != "Alle" and row is not None:
                # Start- und Endzeit prüfen
                t_start = pd.to_datetime(row["Start Leerfahrt"])
                t_ende = pd.to_datetime(row["Ende"])
                if t_start.tzinfo is None:
                    t_start = t_start.tz_localize("UTC")
                if t_ende.tzinfo is None:
                    t_ende = t_ende.tz_localize("UTC")
                if df["timestamp"].dt.tz is None:
                    df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
        
                # Umlauf-Daten extrahieren
                df_umlauf = df[(df["timestamp"] >= t_start) & (df["timestamp"] <= t_ende)]
        
                # Strategie anwenden (nur wenn Spalten in df_umlauf vorhanden sind!)
                strategie = schiffsparameter.get(schiff, {}).get("StartEndStrategie", {})
                if "Verdraengung" in df_umlauf.columns and "Ladungsvolumen" in df_umlauf.columns:
                    werte, debug_info = berechne_start_endwerte(df_umlauf, strategie, df_gesamt=df)
                else:
                    werte = {}
            else:
                werte = {}

        
            # --- Hilfsfunktion für spaltenabhängige Beschriftung (BB/SB) ---
            def get_spaltenname(base, seite):
                if base.endswith("_") and seite in ["BB", "SB"]:
                    return base + seite
                elif base.endswith("_") and seite == "BB+SB":
                    return [base + "BB", base + "SB"]
                return base

        
            # --- Kurvenübersicht: Füllstandsdaten und Prozessgrößen definieren ---
            fuell_cols = [
                'Fuellstand_BB_vorne', 'Fuellstand_SB_vorne',
                'Fuellstand_BB_mitte', 'Fuellstand_SB_mitte',
                'Fuellstand_BB_hinten', 'Fuellstand_SB_hinten'
            ]
            fuellstand_farbe = "#AAB7B8"
        
            # Kurven für Füllstände
            kurven_fuellstand = [
                {"spaltenname": col, "label": f"{col.replace('_', ' ')} [m]", "farbe": fuellstand_farbe, "sichtbar": False, "dicke": 1}
                for col in fuell_cols if col in df.columns and df[col].notnull().any()
            ]
        
            # Hauptkurven (Prozessdaten)
            kurven_haupt = [
                {"spaltenname": "Status", "label": "Status", "farbe": "#BDB76B", "sichtbar": False},
                {"spaltenname": "Pegel", "label": "Pegel [m]", "farbe": "#6699CC", "sichtbar": False},
                {"spaltenname": "Gemischdichte_", "label": "Gemischdichte [t/m³]", "farbe": "#82A07A", "sichtbar": False, "nur_baggern": True},
                {"spaltenname": "Ladungsvolumen", "label": "Ladungsvolumen [m³]", "farbe": "#8C8C8C", "sichtbar": True},
                {"spaltenname": "Verdraengung", "label": "Verdraengung [t]", "farbe": "#A67C52", "sichtbar": True},
                {"spaltenname": "Ladungsmasse", "label": "Ladungsmasse [t]", "farbe": "#A1584F", "sichtbar": False},
                {"spaltenname": "Ladungsdichte", "label": "Ladungsdichte [t/m³]", "farbe": "#627D98", "sichtbar": False},
                {"spaltenname": "Feststoffkonzentration", "label": "Feststoffkonzentration [-]", "farbe": "#BCA898", "sichtbar": False},
                {"spaltenname": "Feststoffvolumen", "label": "Feststoffvolumen [m³]", "farbe": "#7F8C8D", "sichtbar": False},
                {"spaltenname": "Feststoffmasse", "label": "Feststoffmasse [t]", "farbe": "#52796F", "sichtbar": False},
                {"spaltenname": "Fuellstand_Mittel", "label": "Füllstand Mittel [m]", "farbe": "#50789C", "sichtbar": True},
                {"spaltenname": "Geschwindigkeit", "label": "Geschwindigkeit", "farbe": "#82A07A", "sichtbar": False, "sichtbar": True},
            ] + kurven_fuellstand
        
            # --- Start Diagrammaufbau ---
            df_plot = df.copy()
            fig = go.Figure()
        
            # --- Bereiche Status==2 (Baggern) optisch hervorheben ---
            df_plot = df_plot.sort_values("timestamp").reset_index(drop=True)
            starts2, ends2 = status_bereiche(df, [2])
            for start, end in zip(starts2, ends2):
                x0 = df.loc[start, "timestamp"]
                x1 = df.loc[end, "timestamp"]
                if zeitzone != "UTC":
                    x0 = convert_timestamp(x0, zeitzone)
                    x1 = convert_timestamp(x1, zeitzone)
                fig.add_vrect(
                    x0=x0, x1=x1,
                    fillcolor="rgba(0,180,255,0.12)",  # blasses Türkis
                    layer="below", line_width=0,
                    annotation_text="Baggern", annotation_position="top left"
                )
        
            # --- Bereiche Status 4/5/6 (Verbringen) optisch hervorheben ---
            starts4, ends4 = status_bereiche(df, [4, 5, 6])
            for start, end in zip(starts4, ends4):
                x0 = df.loc[start, "timestamp"]
                x1 = df.loc[end, "timestamp"]
                if zeitzone != "UTC":
                    x0 = convert_timestamp(x0, zeitzone)
                    x1 = convert_timestamp(x1, zeitzone)
                fig.add_vrect(
                    x0=x0, x1=x1,
                    fillcolor="rgba(0,255,80,0.11)",  # blasses Grün
                    layer="below", line_width=0,
                    annotation_text="Verbringen", annotation_position="top left"
                )
        
            # --- Prozesskurven einzeichnen ---
            for k in kurven_haupt:
                spalten = get_spaltenname(k["spaltenname"], seite)
                farbe = k["farbe"]
                sicht = k["sichtbar"]
                label = k["label"]
                line_width = k.get("dicke", 2)
        
                if spalten is None:
                    continue
        
                # --- Falls BB+SB getrennte Spalten vorhanden ---
                if isinstance(spalten, list):
                    for s in spalten:
                        if s not in df.columns:
                            continue
                        y = pd.to_numeric(df[s], errors="coerce")
                        x = plot_x(df, df.index, zeitzone)
                        if y.empty or y.min() == y.max():
                            continue
                        y_min, y_max = y.min(), y.max()
                        padding = (y_max - y_min) * 0.1 if y_max != y_min else 1
                        y_min -= padding
                        y_max += padding
                        y_norm = (y - y_min) / (y_max - y_min)  # Normalisierung auf 0-1
        
                        fig.add_trace(go.Scatter(
                            x=x,
                            y=y_norm,
                            mode="lines",
                            name=f"{label} ({s[-2:]})",
                            customdata=y,
                            hovertemplate=f"{label} ({s[-2:]}): %{{customdata:.2f}}<extra></extra>",
                            line=dict(color=farbe, width=line_width),
                            visible=True if sicht else "legendonly"
                        ))
                # --- Normale Einzelsäule ---
                else:
                    if spalten not in df.columns:
                        continue
                    if k.get("nur_baggern"):
                        mask = df["Status"] == 2
                    else:
                        mask = pd.Series([True] * len(df), index=df.index)
        
                    y = pd.to_numeric(df.loc[mask, spalten], errors="coerce")
                    x = plot_x(df, mask, zeitzone)
        
                    if y.empty or y.min() == y.max():
                        continue
                    y_min, y_max = y.min(), y.max()
                    padding = (y_max - y_min) * 0.1 if y_max != y_min else 1
                    y_min -= padding
                    y_max += padding
                    y_norm = (y - y_min) / (y_max - y_min)
        
                    fig.add_trace(go.Scatter(
                        x=x,
                        y=y_norm,
                        mode="lines",
                        name=label,
                        customdata=y,
                        hovertemplate=f"{label}: %{{customdata:.2f}}<extra></extra>",
                        line=dict(color=farbe, width=line_width),
                        visible=True if sicht else "legendonly"
                    ))

        
            # --- Diagrammlayout fertigstellen ---
            st.markdown("#### Umlaufgrafik - Prozessdaten")
            fig.update_layout(
                height=600,
                yaxis=dict(
                    showticklabels=False,
                    showgrid=True,
                    tickvals=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
                    gridcolor="lightgray"
                ),
                xaxis=dict(
                    title="Zeit",
                    showticklabels=True,
                    showgrid=True,
                    gridcolor="lightgray",
                    type="date"
                ),
                hovermode="x unified",
                showlegend=True,
                legend=dict(orientation="v", x=1.02, y=1)
            )
            
 
            # 🔵 Vertikale Linien für Start-/Endzeitpunkte von Verdraengung und Volumen

            # Vertikale Linien für strategische Zeitstempel
            for key, color, label in [
                ("Verdraengung Start TS", "#A67C52", "Verdraengung Start"),
                ("Verdraengung Ende TS", "#A67C52", "Verdraengung Ende"),
                ("Ladungsvolumen Start TS", "#8C8C8C", "Volumen Start"),
                ("Ladungsvolumen Ende TS", "#8C8C8C", "Volumen Ende"),
            ]:
                ts = werte.get(key)
                if ts is not None and pd.notnull(ts):

                    ts = pd.to_datetime(ts)
                    if zeitzone != "UTC":
                        ts = convert_timestamp(ts, zeitzone)
                    if hasattr(ts, "to_pydatetime"):
                        ts = ts.to_pydatetime()

            
                    fig.add_vline(
                        x=ts,
                        line=dict(color=color, width=2, dash="dot"),
                        annotation=None,
                        opacity=0.8
                    )
            
            # Plot anzeigen
            st.plotly_chart(fig, use_container_width=True)
        
            
#==============================================================================================================================
# Tab 3 - Diagramm Tiefe Baggerkopf 
#==============================================================================================================================
            
       
        with tab3:
        
            # --- Spezialdiagramm: Tiefe des Baggerkopfs (nur Status == 2) ----------------------------------------------------------
        
            kurven_abs_tiefe = [
                {"spaltenname": "Abs_Tiefe_Kopf_", "label": "Abs. Tiefe Kopf [m]", "farbe": "#186A3B", "sichtbar": True, "dicke": 2, "dash": None},  # Dunkelgrün
                {"spaltenname": "Solltiefe_Aktuell", "label": "Solltiefe [m]", "farbe": "#B22222", "sichtbar": True, "dicke": 2, "dash": "dash"},   # Rot, gestrichelt
            ]
        
            fig2 = go.Figure()  # Neues leeres Plotly-Diagramm erstellen
        
            # Schleife über alle zu plottenden Kurven
            for k in kurven_abs_tiefe:
                spalten = get_spaltenname(k["spaltenname"], seite)  # Spaltenname abhängig von der gewählten Baggerseite
                farbe = k["farbe"]
                label = k["label"]
        
                if spalten is None:
                    continue  # Spalte existiert nicht → überspringen
        
                # --- Falls mehrere Spalten vorhanden sind (z.B. BB + SB getrennt) ---
                if isinstance(spalten, list):
                    for s in spalten:
                        if s not in df_plot.columns:
                            continue
        
                        status_mask = df_plot["Status"] == 2
                        df_filtered = df_plot.loc[status_mask, ["timestamp", s]].copy()
                        df_filtered["timestamp"] = pd.to_datetime(df_filtered["timestamp"])
                        df_filtered = df_filtered.sort_values("timestamp").reset_index(drop=True)
                        df_filtered = split_by_gap(df_filtered, max_gap_minutes=2)
        
                        for seg_id, seg in df_filtered.groupby("segment"):
                            y = pd.to_numeric(seg[s], errors="coerce")
                            x = seg["timestamp"]
        
                            if y.empty or pd.isna(y.max()):
                                continue
        
                            y_min = y.min()
                            y_max = y.max() + 4  # 4 Meter Puffer nach oben
                            padding = abs(y_min) * 0.1 if abs(y_min) > 0 else 1
                            y_min -= padding
        
                            fig2.add_trace(go.Scatter(
                                x=x,
                                y=y,
                                mode="lines",
                                name=f"{label} ({s[-2:]})" if seg_id == 0 else None,
                                customdata=pd.DataFrame({"original": y}),
                                hovertemplate=f"{label} ({s[-2:]}): %{{customdata[0]:.2f}}<extra></extra>",
                                line=dict(color=farbe, width=k.get("dicke", 2), dash=k.get("dash", None)),
                                visible=True,
                                connectgaps=False,
                                showlegend=(seg_id == 0),
                            ))
        
                # --- Falls nur eine einzelne Spalte vorhanden ist ---
                else:
                    if spalten not in df_plot.columns:
                        continue
        
                    status_mask = df_plot["Status"] == 2
                    df_filtered = df_plot.loc[status_mask, ["timestamp", spalten]].copy()
                    df_filtered["timestamp"] = pd.to_datetime(df_filtered["timestamp"])
                    df_filtered = df_filtered.sort_values("timestamp").reset_index(drop=True)
                    df_filtered = split_by_gap(df_filtered, max_gap_minutes=2)
        
                    for seg_id, seg in df_filtered.groupby("segment"):
                        y = pd.to_numeric(seg[spalten], errors="coerce")
                        x = plot_x(seg, [True] * len(seg), zeitzone)
        
                        if y.empty or pd.isna(y.max()):
                            continue
        
                        y_min = y.min()
                        y_max = y.max() + 4
                        padding = abs(y_min) * 0.1 if abs(y_min) > 0 else 1
                        y_min -= padding
        
                        fig2.add_trace(go.Scatter(
                            x=x,
                            y=y,
                            mode="lines",
                            name=label if seg_id == 0 else None,
                            customdata=pd.DataFrame({"original": y}),
                            hovertemplate=f"{label}: %{{customdata[0]:.2f}}<extra></extra>",
                            line=dict(color=farbe, width=k.get("dicke", 2), dash=k.get("dash", None)),
                            visible=True,
                            connectgaps=False,
                            showlegend=(seg_id == 0),
                        ))
        
            # --- Dynamische Achsenskalierung je nach vorhandener Tiefe -----------------------------------------------
        
            tiefe_col = get_spaltenname("Abs_Tiefe_Kopf_", seite)
            if isinstance(tiefe_col, list):
                vorhandene = [col for col in tiefe_col if col in df_plot.columns]
                if vorhandene:
                    df_plot["_tmp_tiefe_mittel"] = df_plot[vorhandene].mean(axis=1)
                    tiefe_col = "_tmp_tiefe_mittel"
                else:
                    tiefe_col = tiefe_col[0]
        
            mask_tiefe = (df_plot["Status"] == 2) & df_plot[tiefe_col].notnull()
            if mask_tiefe.sum() > 0:
                tiefen = df_plot.loc[mask_tiefe, tiefe_col]
                y_min = tiefen.min() - 2
                y_max = tiefen.max() + 2
            else:
                y_min = -20
                y_max = 0
        
            # --- Solltiefenkorridor (Toleranzbereich) als gefüllte Fläche ------------------------------------------------
        
            if {"Solltiefe_Aktuell", "Solltiefe_Oben", "Solltiefe_Unten"}.issubset(df_plot.columns):
                status_mask = df_plot["Status"] == 2
                x_corridor = plot_x(df_plot, status_mask, zeitzone)
                y_oben = df_plot.loc[status_mask, "Solltiefe_Oben"]
                y_unten = df_plot.loc[status_mask, "Solltiefe_Unten"]
        
                fig2.add_trace(go.Scatter(
                    x=np.concatenate([x_corridor, x_corridor[::-1]]),
                    y=np.concatenate([y_oben, y_unten[::-1]]),
                    fill='toself',
                    fillcolor='rgba(255,0,0,0.13)',
                    line=dict(color='rgba(255,0,0,0)'),
                    hoverinfo='skip',
                    name='Toleranzbereich',
                    showlegend=True,
                ))
        
            # --- Diagramm Layout finalisieren ---------------------------------------------------------------------------
        
            st.markdown("#### Baggerkopftiefe")
            fig2.update_layout(
                height=500,
                yaxis=dict(
                    title="Tiefe [m]",
                    range=[y_min, y_max],
                    showgrid=True,
                    gridcolor="lightgray"
                ),
                xaxis=dict(
                    title="Zeit",
                    showticklabels=True,
                    showgrid=True,
                    gridcolor="lightgray",
                    type="date"
                ),
                hovermode="x unified",
                showlegend=True,
                legend=dict(orientation="v", x=1.02, y=1),
            )
        
            # --- Diagramm anzeigen ---
            st.plotly_chart(fig2, use_container_width=True)

   
        

#==============================================================================================================================
# Tab - Umlauftabelle - gesamt 
#==============================================================================================================================
            
        with tab4:

            def show_gesamtzeiten_dynamisch(
                summe_leerfahrt, summe_baggern, summe_vollfahrt, summe_verklapp, summe_umlauf, 
                zeitformat="hh:mm:ss", title="Gesamtzeiten"
            ):
                """
                Zeigt die Gesamtzeiten-Tabelle: 
                - Erste Zeile im gewählten Zeitformat 
                - Zweite Zeile immer in Dezimalstunden
                """
                # Mapping für das Zeitformat zur Funktion
                format_mapper = {
                    "hh:mm:ss": to_hhmmss,
                    "dezimalminuten": to_dezimalminuten,
                    "dezimalstunden": to_dezimalstunden,  # falls das gewählt werden kann
                    # weitere Formate kannst Du ergänzen
                }
                
                # Hole die passende Formatierungsfunktion (Fallback: to_hhmmss)
                formatter = format_mapper.get(zeitformat, to_hhmmss)
                
                # Erste Zeile: Im gewählten Zeitformat
                summen_format1 = [
                    formatter(summe_leerfahrt),
                    formatter(summe_baggern),
                    formatter(summe_vollfahrt),
                    formatter(summe_verklapp),
                    formatter(summe_umlauf)
                ]
                # Zweite Zeile: immer in Dezimalstunden
                summen_stunden = [
                    to_dezimalstunden(summe_leerfahrt),
                    to_dezimalstunden(summe_baggern),
                    to_dezimalstunden(summe_vollfahrt),
                    to_dezimalstunden(summe_verklapp),
                    to_dezimalstunden(summe_umlauf)
                ]
                columns = ["Leerfahrt", "Baggern", "Vollfahrt", "Verklappen", "Umlauf"]
                
                gesamtzeiten_df = pd.DataFrame([summen_format1, summen_stunden], columns=columns)
                
                gesamtzeiten_df.index = ["", ""]
                return gesamtzeiten_df
       
          # -------------------------         

            # ---- Zusammenfassung für ALLE vollständigen Umläufe ----
            st.markdown("#### Auflistung aller Umläufe")
            if not umlauf_info_df.empty:
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
                # Summen-Listen anlegen
                dauer_leerfahrt_list = []
                dauer_baggern_list = []
                dauer_vollfahrt_list = []
                dauer_verklapp_list = []
                dauer_umlauf_list = []
            
                for idx, row in umlauf_info_df.iterrows():
                    def safe_ts(key):
                        t = row.get(key, None)
                        return convert_timestamp(pd.Timestamp(t) if pd.notnull(t) and t is not None else None, zeitzone) if t is not None else None
            
                    anzeige_start_leerfahrt = safe_ts("Start Leerfahrt")
                    anzeige_start_baggern = safe_ts("Start Baggern")
                    anzeige_start_vollfahrt = safe_ts("Start Vollfahrt")
                    anzeige_start_verklapp = safe_ts("Start Verklappen/Pump/Rainbow")
                    anzeige_ende_umlauf = safe_ts("Ende")
            
                    # Dauern berechnen (tz-aware!)
                    dauer_leerfahrt = (anzeige_start_baggern - anzeige_start_leerfahrt) if anzeige_start_baggern and anzeige_start_leerfahrt else None
                    dauer_baggern = (anzeige_start_vollfahrt - anzeige_start_baggern) if anzeige_start_vollfahrt and anzeige_start_baggern else None
                    dauer_vollfahrt = (anzeige_start_verklapp - anzeige_start_vollfahrt) if anzeige_start_verklapp and anzeige_start_vollfahrt else None
                    dauer_verklapp = (anzeige_ende_umlauf - anzeige_start_verklapp) if anzeige_ende_umlauf and anzeige_start_verklapp else None
                    dauer_umlauf = (anzeige_ende_umlauf - anzeige_start_leerfahrt) if anzeige_ende_umlauf and anzeige_start_leerfahrt else None
            
                    # Summenlisten füllen
                    if dauer_leerfahrt is not None:
                        dauer_leerfahrt_list.append(dauer_leerfahrt)
                    if dauer_baggern is not None:
                        dauer_baggern_list.append(dauer_baggern)
                    if dauer_vollfahrt is not None:
                        dauer_vollfahrt_list.append(dauer_vollfahrt)
                    if dauer_verklapp is not None:
                        dauer_verklapp_list.append(dauer_verklapp)
                    if dauer_umlauf is not None:
                        dauer_umlauf_list.append(dauer_umlauf)
            
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
            
                # Nach der Schleife: DataFrames erzeugen
                df_alle_umlaeufe = pd.DataFrame(rows, columns=columns)
            

                # Nach der Schleife: DataFrames erzeugen
                df_alle_umlaeufe = pd.DataFrame(rows, columns=columns)
                
                # Summen berechnen
                summe_leerfahrt = sum(dauer_leerfahrt_list, pd.Timedelta(0))
                summe_baggern = sum(dauer_baggern_list, pd.Timedelta(0))
                summe_vollfahrt = sum(dauer_vollfahrt_list, pd.Timedelta(0))
                summe_verklapp = sum(dauer_verklapp_list, pd.Timedelta(0))
                summe_umlauf = sum(dauer_umlauf_list, pd.Timedelta(0))
                
                # *** HIER kommt der Funktionsaufruf für die Gesamtzeiten-Tabelle ***
                # Hier wird der DataFrame erzeugt UND in der Variablen gespeichert!
                gesamtzeiten_df = show_gesamtzeiten_dynamisch(
                    summe_leerfahrt,
                    summe_baggern,
                    summe_vollfahrt,
                    summe_verklapp,
                    summe_umlauf,
                    zeitformat=zeitformat,  # das ist die User-Auswahl!
                    title="Gesamtzeiten"
                )

                
                # Danach wie gehabt:
                st.dataframe(df_alle_umlaeufe, use_container_width=True, hide_index=True)

            
                # Anzeige
                st.markdown("#### Aufsummierte Dauer")
                st.dataframe(gesamtzeiten_df, use_container_width=True, hide_index=True)


            else:
                st.info("⚠️ Es wurden keine vollständigen Umläufe erkannt.")

            
#==============================================================================================================================
# Tab 5 - Numerische Auswertung Umlaufdaten
#==============================================================================================================================
        
        # --- HTML-Templates für die Anzeige der Panels ---
        
        # Template für allgemeine KPIs (Dauer, Mengen etc.)
        panel_template = """
        <div style="
            background:#f4f8fc;
            border-radius: 16px;
            padding: 14px 16px 10px 16px;
            margin-bottom: 1.2rem;
            min-width: 210px;
            min-height: 85px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        ">
            <div style="font-size:1rem; color:#555; margin-bottom:3px;">{caption}</div>
            <div style="font-size:2.1rem; font-weight:800; color:#222; line-height:1;">
                {value}
            </div>
            <div style="font-size:0.95rem; color:#4e6980; margin-top:3px;">
                <span style="font-weight:600;">{change_label1}</span> {change_value1}<br>
                <span style="font-weight:600;">{change_label2}</span> {change_value2}
            </div>
        </div>
        """

        
        # Template für Streckenanzeige inkl. kleiner Daueranzeige
        strecken_panel_template = """
        <div style="
            background:#f4f8fc;
            border-radius: 16px;
            padding: 14px 16px 10px 16px;
            margin-bottom: 1.2rem;
            min-width: 140px;
            min-height: 65px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        ">
            <div style="font-size:1rem; color:#555; margin-bottom:3px;">{caption}</div>
            <div style="font-size:2.1rem; font-weight:800; color:#222; line-height:1;">
                {value}
            </div>
            <div style="font-size:0.95rem; color:#4e6980; margin-top:3px;">
                <span style="font-weight:500;">Dauer:</span> {dauer}
            </div>
        </div>
        """

        dichte_panel_template = """
        <div style="
            background:#f4f8fc;
            border-radius: 16px;
            padding: 14px 16px;
            margin-bottom: 1.2rem;
            min-width: 200px;
            min-height: 100px;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
        ">
            <div style="font-size:1rem; color:#555; margin-bottom:6px;">{caption}</div>
            <div style="font-size:0.95rem; color:#333;">
                <strong>Wasser:</strong> {pw} t/m³<br>
                <strong>Feststoff:</strong> {pf} t/m³<br>
                <strong>Ladung:</strong> {pl} t/m³
            </div>
        </div>
        """
        


        with tab5:
            if umlauf_auswahl == "Alle":
                st.info("Bitte einen konkreten Umlauf auswählen, um die Detailauswertung anzuzeigen.")
                st.stop()
        
            # Bei konkretem Umlauf: Zeile finden
            zeile = umlauf_info_df[umlauf_info_df["Umlauf"] == umlauf_auswahl]
            if zeile.empty:
                st.warning("Ausgewählter Umlauf konnte nicht gefunden werden.")
                st.stop()
        
            row = zeile.iloc[0]
        
            if row is not None:
                # === Zeiten & Filter ===
                t_start = pd.to_datetime(row["Start Leerfahrt"])
                t_ende = pd.to_datetime(row["Ende"])
                if t_start.tzinfo is None:
                    t_start = t_start.tz_localize("UTC")
                if t_ende.tzinfo is None:
                    t_ende = t_ende.tz_localize("UTC")
                if df["timestamp"].dt.tz is None:
                    df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
        
                # Filter auf aktuellen Umlauf
                df_umlauf = df[(df["timestamp"] >= t_start) & (df["timestamp"] <= t_ende)]
        
                # === Strategie anwenden ===
                strategie = schiffsparameter.get(schiff, {}).get("StartEndStrategie", {})
                
                def berechne_tds_aus_werte(verd_leer, verd_voll, vol_leer, vol_voll, pf, pw, pb):
                    """
                    Berechnet TDS-Parameter auf Basis von Strategiewerten und Dichteangaben.
                
                    Parameter:
                    - verd_leer : Verdrängung leer (t)
                    - verd_voll : Verdrängung voll (t)
                    - vol_leer  : Volumen leer (m³)
                    - vol_voll  : Volumen voll (m³)
                    - pf : Feststoffdichte (t/m³)
                    - pw : Wasserdichte (t/m³)
                
                    Rückgabe:
                    - dict mit:
                        - ladungsmasse
                        - ladungsvolumen
                        - ladungsdichte
                        - feststoffkonzentration
                        - feststoffvolumen
                        - feststoffmasse
                    """
                
                    result = {}
                
                    if None in [verd_leer, verd_voll, vol_leer, vol_voll]:
                        return {
                            "ladungsmasse": None,
                            "ladungsvolumen": None,
                            "ladungsdichte": None,
                            "feststoffkonzentration": None,
                            "feststoffvolumen": None,
                            "feststoffmasse": None
                        }
                
                    # Berechnungen
                    ladungsmasse = verd_voll - verd_leer
                    ladungsvolumen = vol_voll - vol_leer
                    ladungsdichte = ladungsmasse / ladungsvolumen if ladungsvolumen != 0 else None
                    feststoffkonzentration = (ladungsdichte - pw) / (pf - pw) if ladungsdichte is not None else None
                    feststoffvolumen = feststoffkonzentration * ladungsvolumen if feststoffkonzentration is not None else None
                    feststoffmasse = feststoffvolumen * pf if feststoffvolumen is not None else None
                    if feststoffmasse is not None and pb is not None:
                        bodenvolumen = ((pf - pw) / (pf * (pb - pw))) * feststoffmasse
                    else:
                        bodenvolumen = None
                    
                    # Rückgabe inkl. Bodenvolumen
                    return {
                        "ladungsmasse": ladungsmasse,
                        "ladungsvolumen": ladungsvolumen,
                        "ladungsdichte": ladungsdichte,
                        "feststoffkonzentration": feststoffkonzentration,
                        "feststoffvolumen": feststoffvolumen,
                        "feststoffmasse": feststoffmasse,
                        "bodenvolumen": bodenvolumen   # 🆕 hinzugefügt
                    }                


                                
                
            
                if "Verdraengung" in df_umlauf.columns and "Ladungsvolumen" in df_umlauf.columns:
                    werte, debug_info = berechne_start_endwerte(df_umlauf, strategie, df_gesamt=df)
                    # ➕ TDS-Parameter basierend auf Strategie-Werten berechnen
                    tds_werte = berechne_tds_aus_werte(
                        werte.get("Verdraengung Start"),
                        werte.get("Verdraengung Ende"),
                        werte.get("Ladungsvolumen Start"),
                        werte.get("Ladungsvolumen Ende"),
                        pf, pw, pb
                    )

             
                
                else:
                    werte = {
                        "Verdraengung Start": None,
                        "Verdraengung Ende": None,
                        "Ladungsvolumen Start": None,
                        "Ladungsvolumen Ende": None
                    }
                    debug_info = ["⚠️ Spalten Verdraengung oder Ladungsvolumen fehlen – keine Strategieauswertung möglich."]
                

                    
                # Strategie-Werte (für Panel-Anzeige) in Kennzahlen übertragen
                kennzahlen["verdraengung_leer"] = werte.get("Verdraengung Start")
                kennzahlen["verdraengung_voll"] = werte.get("Verdraengung Ende")
                kennzahlen["volumen_leer"] = werte.get("Ladungsvolumen Start")
                kennzahlen["volumen_voll"] = werte.get("Ladungsvolumen Ende")
                
                # Anzeigen vorbereiten
                kennzahlen["verdraengung_leer_disp"] = f"{werte.get('Verdraengung Start'):.0f}" if werte.get("Verdraengung Start") is not None else "-"
                kennzahlen["verdraengung_voll_disp"] = f"{werte.get('Verdraengung Ende'):.0f}" if werte.get("Verdraengung Ende") is not None else "-"
                kennzahlen["volumen_leer_disp"] = f"{werte.get('Ladungsvolumen Start'):.0f}" if werte.get("Ladungsvolumen Start") is not None else "-"
                kennzahlen["volumen_voll_disp"] = f"{werte.get('Ladungsvolumen Ende'):.0f}" if werte.get("Ladungsvolumen Ende") is not None else "-"
                kennzahlen["delta_verdraengung_disp"] = (
                    f"{werte.get('Verdraengung Ende') - werte.get('Verdraengung Start'):.0f}"
                    if werte.get("Verdraengung Ende") is not None and werte.get("Verdraengung Start") is not None else "-"
                )
                kennzahlen["ladungsvolumen_disp"] = (
                    f"{werte.get('Ladungsvolumen Ende') - werte.get('Ladungsvolumen Start'):.0f}"
                    if werte.get("Ladungsvolumen Ende") is not None and werte.get("Ladungsvolumen Start") is not None else "-"
                )


                # Start- und Endzeit des Umlaufs auslesen und Zeitzone prüfen
                t_start = pd.to_datetime(row["Start Leerfahrt"])
                t_ende = pd.to_datetime(row["Ende"])
                if t_start.tzinfo is None:
                    t_start = t_start.tz_localize("UTC")
                if t_ende.tzinfo is None:
                    t_ende = t_ende.tz_localize("UTC")
                if df["timestamp"].dt.tz is None:
                    df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
        
                # --- Daten auf den aktuellen Umlauf filtern ---
                # Statt:
                # df_umlauf = df[(df["timestamp"] >= t_start) & (df["timestamp"] <= t_ende)]
                
                # Extra: Pufferzeit zurück für Startzeitstrategien
                zeitpuffer_vorher = pd.Timedelta("15min")  # ggf. auch 30min oder 60min
                
                df_umlauf = df[(df["timestamp"] >= (t_start - zeitpuffer_vorher)) & (df["timestamp"] <= t_ende)]

                     
                # --- Streckenlängen für alle Phasen berechnen ---
                strecken = berechne_strecken(df_umlauf, rw_col="RW_Schiff", hw_col="HW_Schiff", status_col="Status", epsg_code=epsg_code)
                gesamt = sum([v for v in [strecken["leerfahrt"], strecken["baggern"], strecken["vollfahrt"], strecken["verbringen"]] if v is not None])
        
                # Formatierte Strings für die Strecken
                strecke_leer_disp = f"{strecken['leerfahrt']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                strecke_baggern_disp = f"{strecken['baggern']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                strecke_vollfahrt_disp = f"{strecken['vollfahrt']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                strecke_verbringen_disp = f"{strecken['verbringen']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                strecke_gesamt_disp = f"{gesamt:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        

        
                # --- Styling für die Panels laden ---
                st.markdown("""
                <style>
                    .big-num {font-size: 2.5rem; font-weight: bold;}
                    .panel {background: #f4f8fc; border-radius: 16px; padding: 20px; margin-bottom: 1.5rem;}
                    .caption {font-size: 1rem; color: #555;}
                    .highlight {font-weight: bold; font-size: 1.2rem; color: #0353a4;}
                </style>
                """, unsafe_allow_html=True)
        
                # --- Headline-Kennzahlen (Dauer, Baggerzeit, Verdraengungsänderung, Volumen) anzeigen ---
                umlaufdauer = kennzahlen.get('Umlaufdauer')
                baggerzeit = kennzahlen.get('Baggerzeit')
                delta_verdraengung = kennzahlen.get('Delta Verdraengung')  # <- neue saubere Kennzahl
                
                umlauf_start = row.get('Start Leerfahrt', '-')
                umlauf_ende = row.get('Ende', '-')
                bagger_start = row.get('Start Baggern', '-')
                bagger_ende = row.get('Start Vollfahrt', '-')
                
                # Beispiel: Änderung der Verdraengung während des Umlaufs
                df_umlauf = df[(df["timestamp"] >= pd.to_datetime(row["Start Leerfahrt"]).tz_localize("UTC")) &
                               (df["timestamp"] <= pd.to_datetime(row["Ende"]).tz_localize("UTC"))]
                
                delta_verdraengung_start = df_umlauf["Verdraengung"].iloc[0] if not df_umlauf.empty else None
                delta_verdraengung_end = df_umlauf["Verdraengung"].iloc[-1] if not df_umlauf.empty else None

                # Zeitdauern je Phase (für Panels)
                dauer_leerfahrt_disp = sichere_dauer(row.get("Start Leerfahrt"), row.get("Start Baggern"), zeitformat)
                dauer_baggern_disp = sichere_dauer(row.get("Start Baggern"), row.get("Start Vollfahrt"), zeitformat)
                dauer_vollfahrt_disp = sichere_dauer(row.get("Start Vollfahrt"), row.get("Start Verklappen/Pump/Rainbow"), zeitformat)
                dauer_verbringen_disp = sichere_dauer(row.get("Start Verklappen/Pump/Rainbow"), row.get("Ende"), zeitformat)
                dauer_umlauf_disp = sichere_dauer(row.get("Start Leerfahrt"), row.get("Ende"), zeitformat)

                       
                # --- Anordnung der Hauptkennzahlen in vier Spalten ---
                st.markdown("#### Statuszeiten im Umlauf", unsafe_allow_html=True)
                if kennzahlen:
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    col1.markdown(panel_template.format(
                        caption="Leerfahrt",
                        value=f"{dauer_leerfahrt_disp}" if dauer_leerfahrt_disp is not None else "-",
                        unit="min",
                        change_label1="Startzeit:",
                        change_value1=format_time(row.get("Start Leerfahrt"), zeitzone),
                        change_label2="Endzeit:",
                        change_value2=format_time(row.get("Start Baggern"), zeitzone)
                    ), unsafe_allow_html=True)
                    
                    col2.markdown(panel_template.format(
                        caption="Baggern",
                        value=f"{dauer_baggern_disp}" if dauer_baggern_disp is not None else "-",
                        unit="min",
                        change_label1="Startzeit:",
                        change_value1=format_time(row.get("Start Baggern"), zeitzone),
                        change_label2="Endzeit:",
                        change_value2=format_time(row.get("Start Vollfahrt"), zeitzone)
                    ), unsafe_allow_html=True)
                    
                    col3.markdown(panel_template.format(
                        caption="Vollfahrt",
                        value=f"{dauer_vollfahrt_disp}" if dauer_vollfahrt_disp is not None else "-",
                        unit="min",
                        change_label1="Startzeit:",
                        change_value1=format_time(row.get("Start Vollfahrt"), zeitzone),
                        change_label2="Endzeit:",
                        change_value2=format_time(row.get("Start Verklappen/Pump/Rainbow"), zeitzone)
                    ), unsafe_allow_html=True)
                    
                    col4.markdown(panel_template.format(
                        caption="Verbringen",
                        value=f"{dauer_verbringen_disp}" if dauer_verbringen_disp is not None else "-",
                        unit="min",
                        change_label1="Startzeit:",
                        change_value1=format_time(row.get("Start Verklappen/Pump/Rainbow"), zeitzone),
                        change_label2="Endzeit:",
                        change_value2=format_time(row.get("Ende"), zeitzone)
                    ), unsafe_allow_html=True)
                    
                    col5.markdown(panel_template.format(
                        caption="Umlaufdauer",
                        value=f"{dauer_umlauf_disp}" if dauer_umlauf_disp is not None else "-",
                        unit="min",
                        change_label1="Startzeit:",
                        change_value1=format_time(row.get("Start Leerfahrt"), zeitzone),
                        change_label2="Endzeit:",
                        change_value2=format_time(row.get("Ende"), zeitzone)
                    ), unsafe_allow_html=True)

                # --- Trenner ---
                st.markdown("---")
                st.markdown("#### Baggerwerte im Umlauf", unsafe_allow_html=True)
                if kennzahlen:    
                    col6, col7, col8, col9, col10 = st.columns(5)
                    
                    col6.markdown(panel_template.format(
                        caption="Verdrängung",
                        value=kennzahlen.get("delta_verdraengung_disp", "-") + " t",
                        unit="",
                        change_label1="leer:",
                        change_value1=kennzahlen.get("verdraengung_leer_disp", "-") + " t",
                        change_label2="voll:",
                        change_value2=kennzahlen.get("verdraengung_voll_disp", "-") + " t"
                    ), unsafe_allow_html=True)
                    
                    col7.markdown(panel_template.format(
                        caption="Ladungsvolumen",
                        value=kennzahlen.get("ladungsvolumen_disp", "-") + " m³",
                        unit="",
                        change_label1="leer:",
                        change_value1=kennzahlen.get("volumen_leer_disp", "-") + " m³",
                        change_label2="voll:",
                        change_value2=kennzahlen.get("volumen_voll_disp", "-") + " m³"
                    ), unsafe_allow_html=True)
                    
                    
                    
                    col8.markdown(panel_template.format(
                        caption="Feststoffmasse",
                        value=f"{tds_werte.get('feststoffmasse', '-'):,.0f} t" if tds_werte.get("feststoffmasse") is not None else "-",
                        change_label1="Volumen:",
                        change_value1=f"{tds_werte.get('feststoffvolumen', '-'):,.0f} m³" if tds_werte.get("feststoffvolumen") is not None else "-",
                        change_label2="Konzentration:",
                        change_value2=f"{tds_werte.get('feststoffkonzentration', '-'):,.1%}" if tds_werte.get("feststoffkonzentration") is not None else "-"
                    ), unsafe_allow_html=True)

                    
                    col9.markdown(panel_template.format(
                        caption="Bodenvolumen",
                        value=f"{tds_werte.get('bodenvolumen', '-'):,.0f} m³" if tds_werte.get("bodenvolumen") is not None else "-",
                        unit="",
                        change_label1="Bodendichte:",
                        change_value1=f"{pb:.3f} t/m³",
                        change_label2="",
                        change_value2=""
                    ), unsafe_allow_html=True)

                    # 🧮 TDS-Ergebnis prüfen
                    if 'tds_result' in locals():
                        ladungsdichte_disp = f"{tds_result.get('ladungsdichte', '-'):,.2f}".replace(",", ".") if tds_result.get("ladungsdichte") is not None else "-"
                    else:
                        ladungsdichte_disp = "-"
                    
                    # 📦 Panel Dichte anzeigen
                    col10.markdown(dichte_panel_template.format(
                        caption="Dichte",
                        pw=f"{pw:.3f}",
                        pf=f"{pf:.3f}",
                        pl=ladungsdichte_disp
                    ), unsafe_allow_html=True)

        
                # --- Trenner ---
                st.markdown("---")
                
                
 
                # --- Streckenanzeige pro Phase inkl. Dauer ---
                st.markdown("#### Strecken im Umlauf")
                
                # Sicherstellen, dass alle Strecken-Werte vorhanden sind
                def format_km(value):
                    if value is None:
                        return "-"
                    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                
                strecke_leer_disp = format_km(strecken.get("leerfahrt"))
                strecke_baggern_disp = format_km(strecken.get("baggern"))
                strecke_vollfahrt_disp = format_km(strecken.get("vollfahrt"))
                strecke_verbringen_disp = format_km(strecken.get("verbringen"))
                strecke_gesamt_disp = format_km(gesamt)
                
                # Zeitdauern anzeigen – bereits abgesichert mit sichere_dauer()
                dauer_leerfahrt_disp = sichere_dauer(row.get("Start Leerfahrt"), row.get("Start Baggern"), zeitformat)
                dauer_baggern_disp = sichere_dauer(row.get("Start Baggern"), row.get("Start Vollfahrt"), zeitformat)
                dauer_vollfahrt_disp = sichere_dauer(row.get("Start Vollfahrt"), row.get("Start Verklappen/Pump/Rainbow"), zeitformat)
                dauer_verbringen_disp = sichere_dauer(row.get("Start Verklappen/Pump/Rainbow"), row.get("Ende"), zeitformat)
                dauer_umlauf_disp = sichere_dauer(row.get("Start Leerfahrt"), row.get("Ende"), zeitformat)
                
                # Darstellung in 5 Panels
                col_st1, col_st2, col_st3, col_st4, col_st5 = st.columns(5)
                
                col_st1.markdown(strecken_panel_template.format(
                    caption="Leerfahrt",
                    value=f"{strecke_leer_disp} km",
                    dauer=dauer_leerfahrt_disp
                ), unsafe_allow_html=True)
                
                col_st2.markdown(strecken_panel_template.format(
                    caption="Baggern",
                    value=f"{strecke_baggern_disp} km",
                    dauer=dauer_baggern_disp
                ), unsafe_allow_html=True)
                
                col_st3.markdown(strecken_panel_template.format(
                    caption="Vollfahrt",
                    value=f"{strecke_vollfahrt_disp} km",
                    dauer=dauer_vollfahrt_disp
                ), unsafe_allow_html=True)
                
                col_st4.markdown(strecken_panel_template.format(
                    caption="Verbringen",
                    value=f"{strecke_verbringen_disp} km",
                    dauer=dauer_verbringen_disp
                ), unsafe_allow_html=True)
                
                col_st5.markdown(strecken_panel_template.format(
                    caption="Gesamt",
                    value=f"{strecke_gesamt_disp} km",
                    dauer=dauer_umlauf_disp
                ), unsafe_allow_html=True)



#------ DEBUG Strategien
            
            st.markdown("---")

            # --- Debug-Tabelle basierend auf den Strategie-Werten (aus `werte`) ---
            with st.expander("🛠️ Debug-Infos & Strategieergebnisse", expanded=False):
            
                # Strategien anzeigen
                st.markdown(f"🔍 **Strategie Verdraengung**: `{strategie.get('Verdraengung', {})}`")
                st.markdown(f"🔍 **Strategie Ladungsvolumen**: `{strategie.get('Ladungsvolumen', {})}`")
            
                # Zeilenweises Debugging anzeigen
                for zeile in debug_info:
                    st.markdown(zeile)
            
                # Tabelle: Übersicht Start-/Endwerte laut Strategie
                st.markdown("### 📋 Übersicht Start-/Endwerte laut Strategie")
            
                werte_tabelle = pd.DataFrame([
                    {
                        "Parameter": "Verdraengung Start",
                        "Wert": f"{werte['Verdraengung Start']:.2f}" if werte.get("Verdraengung Start") is not None else "-",
                        "Zeitstempel": sichere_zeit(werte.get("Verdraengung Start TS"))
                    },
                    {
                        "Parameter": "Verdraengung Ende",
                        "Wert": f"{werte['Verdraengung Ende']:.2f}" if werte.get("Verdraengung Ende") is not None else "-",
                        "Zeitstempel": sichere_zeit(werte.get("Verdraengung Ende TS"))
                    },
                    {
                        "Parameter": "Ladungsvolumen Start",
                        "Wert": f"{werte['Ladungsvolumen Start']:.2f}" if werte.get("Ladungsvolumen Start") is not None else "-",
                        "Zeitstempel": sichere_zeit(werte.get("Ladungsvolumen Start TS"))
                    },
                    {
                        "Parameter": "Ladungsvolumen Ende",
                        "Wert": f"{werte['Ladungsvolumen Ende']:.2f}" if werte.get("Ladungsvolumen Ende") is not None else "-",
                        "Zeitstempel": sichere_zeit(werte.get("Ladungsvolumen Ende TS"))
                    }
                ])
            
                st.dataframe(werte_tabelle, use_container_width=True, hide_index=True)




#=====================================================================================
    except Exception as e:
        st.error(f"Fehler: {e}")
        st.text(traceback.format_exc())       
        
else:
    st.info("Bitte lade mindestens eine MoNa-Datei hoch.")
