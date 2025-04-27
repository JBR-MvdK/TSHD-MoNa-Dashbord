import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import pytz
from shapely.geometry import Point
import numpy as np


#=== Einlesen und Parsen der MoNa-Dateien --> modul_mona_import.py ============================================================
from modul_tshd_mona_import import parse_mona, berechne_tds_parameter

#=== Umläufe berechnen --> modul_umlaeufe.py ==================================================================================
from modul_umlaeufe import nummeriere_umlaeufe, extrahiere_umlauf_startzeiten

#=== Baggerseite --> modul_baggerseite.py =====================================================================================
from modul_baggerseite import erkenne_baggerseite

#=== Koordinatensystem erkennen --> modul_koordinatenerkennung.py =============================================================
from modul_koordinatenerkennung import erkenne_koordinatensystem

#=== XML-Datei der Baggerfeldgrenzen (LandXML) parsen --> modul_baggerfelder_xml_import.py ====================================
from modul_baggerfelder_xml_import import parse_baggerfelder

#=== Solltiefen berechnen --> modul_solltiefe_tshd.py ====================================
from modul_solltiefe_tshd import berechne_solltiefe_fuer_df


#=== Zeitliche Lücken erkennen und segmentieren (für Linienunterbrechungen) ===================================================
def split_by_gap(df, max_gap_minutes=2):
    df = df.sort_values(by="timestamp")
    df["gap"] = df["timestamp"].diff().dt.total_seconds() > (max_gap_minutes * 60)
    df["segment"] = df["gap"].cumsum()
    return df
    
#=== Definition UTC oder Lokale Zeit  =========================================================================================
def convert_timestamp(ts, zeitzone):
    if ts is None or pd.isnull(ts):
        return None
    if zeitzone == "UTC":
        # Sicherstellen, dass Timestamp tz-aware ist (UTC)
        if ts.tzinfo is None:
            return ts.tz_localize("UTC")
        else:
            return ts.astimezone(pytz.UTC)
    elif zeitzone == "Lokal (Europe/Berlin)":
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        return ts.astimezone(pytz.timezone("Europe/Berlin"))
    return ts

def plot_x(df, mask, zeitzone):
    col = "timestamp"
    if zeitzone == "Lokal (Europe/Berlin)":
        return df.loc[mask, col].dt.tz_convert("Europe/Berlin")
    return df.loc[mask, col]


#=== START der Routine  =======================================================================================================

st.set_page_config(page_title="TSHD-MoNa Dashboard - MvdK", layout="wide")
st.title("📊 TSHD-MoNa Dashboard - MvdK")

# Sidebar für Datei-Upload
st.sidebar.header("📂 Datei-Upload")

with st.sidebar.expander("📂 Dateien hochladen / auswählen", expanded=True):  # expanded=False wenn zugeklappt starten soll
    # MoNa Daten auswählen
    uploaded_files = st.file_uploader(
        "MoNa-Dateien (.txt) auswählen", 
        type=["txt"], 
        accept_multiple_files=True,
        key="mona_upload"
    )
    upload_status = st.empty()  # Platz für Erfolgsmeldung

    # Polygone als XML-Datei auswählen
    uploaded_xml_files = st.file_uploader(
        "Baggerfeldgrenzen (XML)", 
        type=["xml"], 
        accept_multiple_files=True,
        key="xml_upload"
    )
    xml_status = st.empty()  # Platz für XML-Status


# Erfolgsmedlung ob Koordinatensysten erkannt wurde 
koordsys_status = st.sidebar.empty()  


#=== Parameter Dichte  =======================================================================================================
with st.sidebar.expander("🚢 Berechnungs-Setup"):
    #---- Eingabe - Feststoffdichte
    pf = st.number_input(
        "Feststoffdichte pf [t/m³]",
        min_value=2.0,
        max_value=3.0,
        value=2.643,
        step=0.001,
        format="%.3f"
    )
    #---- Eingabe - Wasserdichte
    pw = st.number_input(
        "Wasserdichte pw [t/m³]",
        min_value=1.0,
        max_value=1.1,
        value=1.025,
        step=0.001,
        format="%.3f"
    )
    #---- Eingabe - min. Geschwindigkeit Leerfahrt
    min_fahr_speed = st.number_input(
        "Mindestgeschwindigkeit für Leerfahrt (knt)",
        min_value=0.0,
        max_value=2.0,
        value=0.3,
        step=0.01,
        format="%.2f"
    )
    solltiefe_slider = st.number_input(
        "**Solltiefe (m)** \n_Nur falls keine XML mit gültiger Tiefe geladen wird_",  # \n für Zeilenumbruch
        min_value=-30.0,
        max_value=0.0,
        value=0.0,
        step=0.1,
        format="%.2f"
    )

    toleranz_oben = st.slider(
        "Obere Toleranz (m)", min_value=0.0, max_value=2.0, value=0.5, step=0.1
    )
    toleranz_unten = st.slider(
        "Untere Toleranz (m)", min_value=0.0, max_value=2.0, value=0.5, step=0.1
    )


    
# === MoNa Daten einlesen =====================================================================================================
if uploaded_files:
    try:
    # Daten einlesen
        df, rw_max, hw_max = parse_mona(uploaded_files)
        
    # Ausgabe wie viele Datensätz eingelesen wurden
        upload_status.success(f"{len(df)} Zeilen aus {len(uploaded_files)} Datei(en) geladen")
        
        df = berechne_tds_parameter(df, pf, pw)
    # Automatische Erkennung des Koordinatensystems (UTM, GK, RD) aus modul_koordinatenerkennung.py
        if 'df' in locals() and not df.empty:      # oder: if uploaded_mona_files:
            proj_system, epsg_code, auto_erkannt = erkenne_koordinatensystem(
                df, st=koordsys_status, sidebar=st.sidebar
            )
        
     
        # ... (Datei-Upload, Parsen, df einlesen usw.)
        
        schiffe = df["Schiffsname"].dropna().unique()
        if len(schiffe) == 1:
            schiffsname_text = f"**Schiff:** **{schiffe[0]}**"
        elif len(schiffe) > 1:
            schiffsname_text = f"**Schiffe im Datensatz:** {', '.join(schiffe)}"
        else:
            schiffsname_text = "Keine bekannten Schiffsnamen gefunden."
        
        meta_info = st.empty() 
        
        # Nach Upload
        meta_info.markdown(f"""
        {schiffsname_text}  
        **Zeitraum:** {df["timestamp"].min().strftime('%d.%m.%Y %H:%M:%S')} – {df["timestamp"].max().strftime('%d.%m.%Y %H:%M:%S')} UTC  
        **Baggerseite:** *(wird noch erkannt...)*
        """)
        
# === Auswahlzeile platzieren – direkt VOR Tabelle und Filter! ================================================================
# Umlaufauswahl und Zeitauswahl
       
        st.markdown("---")
        col_startwert, col_umlauf, col_zeitformat, col_zeitzone = st.columns([1, 1, 1, 1])
        
    # Startwert Umlaufzählung setzen
        with col_startwert:
            startwert = st.number_input("🔢 Startwert Umlaufzählung", min_value=1, step=1, value=1)

        
        # ---- Jetzt die Umlaufnummerierung und Info extrahieren! ----
        df = nummeriere_umlaeufe(df, startwert=startwert)
        
        umlauf_info_df = extrahiere_umlauf_startzeiten(df, startwert=startwert)
        if not umlauf_info_df.empty:
            if "Start Leerfahrt" in umlauf_info_df.columns:
                umlauf_info_df["start"] = umlauf_info_df["Start Leerfahrt"]
            if "Ende" in umlauf_info_df.columns:
                umlauf_info_df["ende"] = umlauf_info_df["Ende"]
                
    # Umlauf auswählen      
        with col_umlauf:
            # Prüfe robust, ob die Umlauf-Spalte existiert und das DF nicht leer ist
            umlauf_options = ["Alle"]
            if not umlauf_info_df.empty and "Umlauf" in umlauf_info_df.columns:
                umlauf_options += [int(u) for u in umlauf_info_df["Umlauf"]]
        
            umlauf_auswahl = st.selectbox(
                "🔁 Umlauf auswählen",
                options=umlauf_options
            )
            
    # Zeitformat auswählen
        with col_zeitformat:
            zeitformat = st.selectbox(
                "Zeitformat für Summenanzeige",
                options=["hh:mm:ss", "dezimalminuten", "dezimalstunden"],
                index=1,
                format_func=lambda x: {
                    "hh:mm:ss": "hh:mm:ss",
                    "dezimalminuten": "Dezimalminuten",
                    "dezimalstunden": "Dezimalstunden"
                }[x]
            )
    
    # Zeitzone setzen
        with col_zeitzone:
            zeitzone = st.selectbox(
                "🌍 Zeitzone anzeigen",
                ["UTC", "Lokal (Europe/Berlin)"],
                index=0

            )
    
    # Zeitkonvertierung vorbereiten
        if df["timestamp"].dt.tz is None:
            df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")

           
    # Umlaufliste vorbereiten
        verfuegbare_umlaeufe = df["Umlauf"].dropna().unique()
        verfuegbare_umlaeufe.sort()
        

    # Umlauf-Zeile vorbereiten
        if umlauf_auswahl != "Alle":
            zeile = umlauf_info_df[umlauf_info_df["Umlauf"] == umlauf_auswahl]
        else:
            zeile = pd.DataFrame()
            
# === Seitenwahl (Auto / BB / SB / BB+SB) =====================================================================================
# Manuelle Auswahl per Dropdown
        seite_auswahl = st.sidebar.selectbox(
            "🧭 Baggerseite wählen",
            options=["Auto", "BB", "SB", "BB+SB"],
            index=1  # Standard auf "Auto"
        )
        
    # Automatische Erkennung
        erkannte_seite = erkenne_baggerseite(df)
        
    # Auswahl anwenden
        seite = erkannte_seite if seite_auswahl == "Auto" else seite_auswahl
        
    # Anzeigen in der Sidebar
        # ... Dann später nach Auswahl/Erkennung:
        meta_info.markdown(f"""
        {schiffsname_text}  
        **Zeitraum:** {df["timestamp"].min().strftime('%d.%m.%Y %H:%M:%S')} – {df["timestamp"].max().strftime('%d.%m.%Y %H:%M:%S')} UTC  
        **Baggerseite:** {seite}
        """)
        

#=== Normalisierung der Rechtswerte (z. B. Entfernen der Zonenkennung bei UTM) ================================================
# ⤷ Wird auf alle relevanten Spalten angewendet (RW_Schiff, RW_BB, RW_SB)
    
        def normalisiere_rechtswert(wert):
            if proj_system == "UTM" and auto_erkannt and wert > 30_000_000:
                return wert - int(epsg_code[-2:]) * 1_000_000
            return wert
    
    # anwenden auf relevante Spalten
        for col in ["RW_Schiff", "RW_BB", "RW_SB"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].apply(normalisiere_rechtswert)
            
#=== XML-Datei der Baggerfeldgrenzen (LandXML) parsen =========================================================================
# ⤷ baggerfelder_parser.py ---> Extrahiert Polygon-Koordinaten für jedes Baggerfeld – inkl. Namenszuweisung

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
        
        df = berechne_solltiefe_fuer_df(
            df, baggerfelder, seite, epsg_code, toleranz_oben, toleranz_unten, solltiefe_slider
        )

        # Nach df = berechne_solltiefe_fuer_df(...)
        if "Solltiefe_Aktuell" in df.columns and df["Solltiefe_Aktuell"].notnull().any():
            # Alle gültigen Werte extrahieren (ohne NaN)
            gueltige = df["Solltiefe_Aktuell"].dropna()
            # Schauen, ob sie alle gleich sind (dann war's vermutlich Slider oder XML mit konstantem Wert)
            if (gueltige == gueltige.iloc[0]).all():
                solltiefe_wert = gueltige.iloc[0]
            else:
                solltiefe_wert = "variabel"
        else:
            solltiefe_wert = None
        
        # Bestimme Quelle der Solltiefe
        if solltiefe_wert is None:
            solltiefe_herkunft = "nicht definiert"
        elif solltiefe_wert == solltiefe_slider:
            solltiefe_herkunft = "manuelle Eingabe"
        elif solltiefe_wert == "variabel":
            solltiefe_herkunft = "aus XML - mehrere Werte"
        else:
            solltiefe_herkunft = "aus XML-Datei übernommen"
        
        # Anzeige Solltiefe hübsch machen (nur Zahl formatieren, sonst einfach weitergeben)
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



#=== Umlaufinformationen ======================================================================================================
        
        # Definition hh:mm:sss
        def to_hhmmss(td):
            try:
                if pd.isnull(td) or td is None:
                    return "-"
                total_seconds = int(td.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                return f"{hours:02}:{minutes:02}:{seconds:02}"
            except Exception:
                return "-"
        
        # Definition hh.hhh
        def to_dezimalstunden(td):
            try:
                if pd.isnull(td) or td is None:
                    return "-"
                value = td.total_seconds() / 3600
                # Komma für Dezimal, Punkt für Tausender
                stunden_formatiert = f"{value:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")
                return f"{stunden_formatiert} h"
            except:
                return "-"
   
        # Definition mm.mmm
        def to_dezimalminuten(td):
            try:
                if pd.isnull(td) or td is None:
                    return "-"
                # Mit Tausenderpunkt
                return f"{int(td.total_seconds() // 60):,} min".replace(",", ".")
            except:
                return "-"

                
        
        def format_dauer(td):
            if zeitformat == "hh:mm:ss":
                return to_hhmmss(td)
            elif zeitformat == "dezimalstunden":
                return to_dezimalstunden(td)
            elif zeitformat == "dezimalminuten":
                return to_dezimalminuten(td)
            else:
                return "-"

        
    # --- Umlauf-Info-Tabelle bauen --------------------------------------
        if umlauf_auswahl != "Alle":
            if zeile.empty:
                st.warning("⚠️ Kein vollständiger Umlauf: Der ausgewählte Umlauf ist unvollständig (endet z. B. nicht mit Status 4, 5 oder 6). "
                           "Es werden trotzdem alle Rohdaten und Karten angezeigt.")
            else:
                try:
                    row = zeile.iloc[0]
                    # Alle Start-/Endzeiten sicher auslesen (auch None möglich)
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
        
                    # Robust prüfen ob Umlauf "existiert"
                    if phase_times["anzeige_start_leerfahrt"] is None or phase_times["anzeige_ende_umlauf"] is None:
                        st.warning("⚠️ Kein vollständiger Umlauf: Beginn oder Ende fehlt (kein Status 1 oder kein Status 4/5/6 erkannt).")
                    else:
                        # DataFrame auf Zeitbereich des Umlaufs filtern
                        df = df[(df["timestamp"] >= phase_times["anzeige_start_leerfahrt"]) & (df["timestamp"] <= phase_times["anzeige_ende_umlauf"])]
        
                        # Dauerabschnitte berechnen
                        dauer_leerfahrt = (phase_times["anzeige_start_baggern"] - phase_times["anzeige_start_leerfahrt"]) if phase_times["anzeige_start_baggern"] else None
                        dauer_baggern = (phase_times["anzeige_start_vollfahrt"] - phase_times["anzeige_start_baggern"]) if phase_times["anzeige_start_baggern"] and phase_times["anzeige_start_vollfahrt"] else None
                        dauer_vollfahrt = (phase_times["anzeige_start_verklapp"] - phase_times["anzeige_start_vollfahrt"]) if phase_times["anzeige_start_vollfahrt"] and phase_times["anzeige_start_verklapp"] else None
                        dauer_verklapp = (phase_times["anzeige_ende_umlauf"] - phase_times["anzeige_start_verklapp"]) if phase_times["anzeige_start_verklapp"] and phase_times["anzeige_ende_umlauf"] else None
                        dauer_umlauf = (phase_times["anzeige_ende_umlauf"] - phase_times["anzeige_start_leerfahrt"]) if phase_times["anzeige_ende_umlauf"] else None
        
                        columns = pd.MultiIndex.from_tuples([
                            ("Umlauf", "Nr."),
                            ("Datum", ""),
                            ("Leerfahrt", "Beginn"), ("Leerfahrt", "Dauer"),
                            ("Baggern", "Beginn"), ("Baggern", "Dauer"),
                            ("Vollfahrt", "Beginn"), ("Vollfahrt", "Dauer"),
                            ("Verklappen", "Beginn"), ("Verklappen", "Dauer"),
                            ("Umlauf", "Ende"), ("Umlauf", "Dauer")
                        ])
        
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
                        st.dataframe(df_summary, use_container_width=True, hide_index=True)
        
                except Exception as e:
                    st.warning("⚠️ Der gewählte Umlauf ist unvollständig oder fehlerhaft.")
                    st.info(f"(Details: {e})")
        #else:
            #st.info("**Bitte wähle einen Umlauf aus.**")
        

        # === Tabs definieren ===
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🗺️ Karte",
            "📈 Prozess",
            "📉 Tiefe",
            "📋 Umläufe",
            "📋 Auswertung"
        ])
#==============================================================================================================================
# Tab - Übersichtskarten 
#==============================================================================================================================

        with tab1:
            from pyproj import Transformer
            
            # Zwei Spalten
            col1, col2 = st.columns(2)
            transformer = Transformer.from_crs(epsg_code, "EPSG:4326", always_xy=True)


    # -------------------------------------------------------------------------------------------------------------------------
    # Definition der Karten - linke und rechte Karte sind inhaltlich gleich.
            zeit_suffix = "UTC" if zeitzone == "UTC" else "Lokal"
            def plot_karte(
                df, 
                transformer, 
                seite, 
                status2_label, 
                tiefe_spalte, 
                mapbox_center, 
                focus_trace=None
            ):
                import plotly.graph_objects as go
            
                fig = go.Figure()
            
                def tooltip_text(row):
                    ts = convert_timestamp(row["timestamp"], zeitzone)
                    zeit = ts.strftime("%d.%m.%Y %H:%M:%S") if ts else "-"
                    tiefe = row.get(tiefe_spalte)  # Nur noch eine Zeile!
                    tooltip = f"🕒 {zeit} ({zeit_suffix})"
                    if pd.notnull(tiefe):
                        tooltip += f"<br>📉 Tiefe: {tiefe:.2f} m"
                    return tooltip                    
                                
                
                def tooltip_status1_3(row):
                    ts = convert_timestamp(row["timestamp"], zeitzone)
                    zeit = ts.strftime("%d.%m.%Y %H:%M:%S") if ts else "-"
                    tooltip = f"🕒 {zeit} ({zeit_suffix})"
                    geschw = row.get("Geschwindigkeit", None)
                    if pd.notnull(geschw):
                        tooltip += f"<br>🚤 Geschwindigkeit: {geschw:.1f} kn"
                    return tooltip

            
            # Status 1 (Leerfahrt)
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
            
            # Status 2 (Baggern)
                df_status2 = df[df["Status"] == 2].dropna(subset=["RW_Schiff", "HW_Schiff"])
                df_status2 = split_by_gap(df_status2)
                for seg_id, segment_df in df_status2.groupby("segment"):
                    coords = segment_df.apply(lambda row: transformer.transform(row["RW_Schiff"], row["HW_Schiff"]), axis=1)
                    lons, lats = zip(*coords)
                    tooltips = segment_df.apply(tooltip_text, axis=1)
                    fig.add_trace(go.Scattermapbox(
                        lon=lons, lat=lats, mode='lines+markers',
                        marker=dict(size=6, color='rgba(0, 102, 204, 0.8)'),
                        line=dict(width=2, color='rgba(0, 102, 204, 0.8)'),
                        text=tooltips, hoverinfo='text',
                        name=status2_label if seg_id == 0 else None,
                        showlegend=(seg_id == 0), legendgroup="status2"
                    ))
            
            # Status 3 (Vollfahrt)
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
            
            # Status 4/5/6 (Verbringen)
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

            # Polygone / Baggerfelder darstellen 4/5/6
                if baggerfelder:
                    for idx, feld in enumerate(baggerfelder):
                        coords = list(feld["polygon"].exterior.coords)
                        lons, lats = zip(*coords)
                        tooltip = f"{feld['name']}<br>Solltiefe: {feld['solltiefe']} m"
            
                    # Polygon-Umriss + Marker
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
            
                    # Unsichtbarer Tooltip-Punkt in der Mitte der Fläche
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
             # ----
                if focus_trace:
                    fig.add_trace(focus_trace)
            
                fig.update_layout(
                    mapbox_style="open-street-map",
                    mapbox_zoom=12,
                    mapbox_center=mapbox_center,
                    height=700,
                    margin=dict(r=0, l=0, t=0, b=0),
                    legend=dict(
                        x=0.01,
                        y=0.99,
                        bgcolor="rgba(255,255,255,0.8)",
                        bordercolor="gray",
                        borderwidth=1
                    )
                )
           
                return fig, df_status2, df_456

    # -------------------------------------------------------------------------------------------------------------------------
    # linke Karte - alles darstellen - Zoom auf Status 2 - Baggern

            with col1:
                fig, df_status2, df_456 = plot_karte(
                    df=df,
                    transformer=transformer,
                    seite=seite,
                    status2_label="Status 2 (Baggern)",
                    tiefe_spalte="Abs_Tiefe_Kopf_BB" if seite in ["BB", "BB+SB"] else "Abs_Tiefe_Kopf_SB",
                    mapbox_center={"lat": 53.5, "lon": 8.2}  # Passe ggf. an!
                )
            
                # Zentrierung auf ersten Status-2-Punkt
                if not df_status2.empty:
                    first_latlon = transformer.transform(df_status2.iloc[0]["RW_Schiff"], df_status2.iloc[0]["HW_Schiff"])
                    fig.update_layout(
                        mapbox_center={"lat": first_latlon[1], "lon": first_latlon[0]},
                        mapbox_zoom=13
                    )
                else:
                    st.info("Keine Daten mit Status 2 verfügbar.")
                    
                st.markdown("#### Baggerstelle")
                st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})
          
    
    # rechte Karte - alles darstellen - Zoom auf Status 4 5 6 - Verbringen

            with col2:
                fig, df_status2, df_456 = plot_karte(
                    df=df,
                    transformer=transformer,
                    seite=seite,
                    status2_label="Status 2 (Verbringen)",
                    tiefe_spalte="Abs_Tiefe_Verbring",
                    mapbox_center={"lat": 53.6, "lon": 8.3}  # Passe ggf. an!
                )
            
                # Zentrierung auf ersten Status 4/5/6-Punkt
                if not df_456.empty:
                    first_latlon = transformer.transform(df_456.iloc[0]["RW_Schiff"], df_456.iloc[0]["HW_Schiff"])
                    fig.update_layout(
                        mapbox_center={"lat": first_latlon[1], "lon": first_latlon[0]},
                        mapbox_zoom=13
                    )
                else:
                    st.info("Keine Daten mit Status 4, 5 oder 6 verfügbar.")
            
                st.markdown("#### Verbringstelle")
                st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})

#==============================================================================================================================
# Tab 2 - Diagramm Prozessdaten
#==============================================================================================================================
        
        
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
            # Hilfsfunktion für Kurvennamen
            def get_spaltenname(base, seite):
                if base.endswith("_") and seite in ["BB", "SB"]:
                    return base + seite
                elif base.endswith("_") and seite == "BB+SB":
                    return [base + "BB", base + "SB"]
                return base
        
            fuell_cols = [
                'Fuellstand_BB_vorne', 'Fuellstand_SB_vorne',
                'Fuellstand_BB_mitte', 'Fuellstand_SB_mitte',
                'Fuellstand_BB_hinten', 'Fuellstand_SB_hinten'
            ]
            fuellstand_farbe = "#AAB7B8"
        
            kurven_fuellstand = [
                {"spaltenname": col, "label": f"{col.replace('_', ' ')} [m]", "farbe": fuellstand_farbe, "sichtbar": False, "dicke": 1}
                for col in fuell_cols if col in df.columns and df[col].notnull().any()
            ]
        
            kurven_haupt = [
                {"spaltenname": "Status", "label": "Status", "farbe": "#BDB76B", "sichtbar": False},
                {"spaltenname": "Pegel", "label": "Pegel [m]", "farbe": "#6699CC", "sichtbar": False},
                #{"spaltenname": "Gemischdichte_", "label": "Gemischdichte [t/m³]", "farbe": "#82A07A", "sichtbar": False},
                {"spaltenname": "Gemischdichte_", "label": "Gemischdichte [t/m³]", "farbe": "#82A07A", "sichtbar": False, "nur_baggern": True},
                {"spaltenname": "Ladungsvolumen", "label": "Ladungsvolumen [m³]", "farbe": "#8C8C8C", "sichtbar": True},
                {"spaltenname": "Verdraengung", "label": "Verdrängung [t]", "farbe": "#A67C52", "sichtbar": True},
                {"spaltenname": "Ladungsmasse", "label": "Ladungsmasse [t]", "farbe": "#A1584F", "sichtbar": False},
                {"spaltenname": "Ladungsdichte", "label": "Ladungsdichte [t/m³]", "farbe": "#627D98", "sichtbar": False},
                {"spaltenname": "Feststoffkonzentration", "label": "Feststoffkonzentration [-]", "farbe": "#BCA898", "sichtbar": False},
                {"spaltenname": "Feststoffvolumen", "label": "Feststoffvolumen [m³]", "farbe": "#7F8C8D", "sichtbar": False},
                {"spaltenname": "Feststoffmasse", "label": "Feststoffmasse [t]", "farbe": "#52796F", "sichtbar": False},
                {"spaltenname": "Fuellstand_Mittel", "label": "Füllstand Mittel [m]", "farbe": "#50789C", "sichtbar": True},
            ] + kurven_fuellstand
        
            df_plot = df.copy()
            fig = go.Figure()


        # Bereich mit Status==2 (Baggern) optisch hervorheben
            df_plot = df_plot.sort_values("timestamp").reset_index(drop=True)
            status2 = df_plot["Status"] == 2
            wechsel = status2.astype(int).diff().fillna(0)
            starts = df_plot.index[(wechsel == 1)].tolist()
            ends = df_plot.index[(wechsel == -1)].tolist()
            
            if status2.iloc[0]:
                starts = [0] + starts
            if status2.iloc[-1]:
                ends = ends + [len(df_plot) - 1]
            
            # ---- Farbige Bereiche für Status == 2 (Baggern)
            starts2, ends2 = status_bereiche(df, [2])
            for start, end in zip(starts2, ends2):
                x0 = df.loc[start, "timestamp"]
                x1 = df.loc[end, "timestamp"]
                if zeitzone != "UTC":
                    x0 = convert_timestamp(x0, zeitzone)
                    x1 = convert_timestamp(x1, zeitzone)
                fig.add_vrect(
                    x0=x0, x1=x1,
                    fillcolor="rgba(0,180,255,0.12)",  # blass türkis
                    layer="below", line_width=0,
                    annotation_text="Baggern", annotation_position="top left"
                )
            
            # ---- Farbige Bereiche für Status 4/5/6 (Verbringen)
            starts4, ends4 = status_bereiche(df, [4, 5, 6])
            for start, end in zip(starts4, ends4):
                x0 = df.loc[start, "timestamp"]
                x1 = df.loc[end, "timestamp"]
                if zeitzone != "UTC":
                    x0 = convert_timestamp(x0, zeitzone)
                    x1 = convert_timestamp(x1, zeitzone)
                fig.add_vrect(
                    x0=x0, x1=x1,
                    fillcolor="rgba(0,255,80,0.11)",  # blass grün
                    layer="below", line_width=0,
                    annotation_text="Verbringen", annotation_position="top left"
                )
            
            
            for k in kurven_haupt:
                spalten = get_spaltenname(k["spaltenname"], seite)
                farbe = k["farbe"]
                sicht = k["sichtbar"]
                label = k["label"]
                line_width = k.get("dicke", 2)
        
                if spalten is None:
                    continue
        
                # Falls BB+SB-List
                if isinstance(spalten, list):
                    for s in spalten:
                        if s not in df.columns:
                            continue
                        y = pd.to_numeric(df[s], errors="coerce")
                        x = plot_x(df, df.index, zeitzone)
                        y_min, y_max = y.min(), y.max()
                        if pd.isna(y_min) or pd.isna(y_max) or y_max == y_min:
                            continue
                        padding = (y_max - y_min) * 0.1 if y_max != y_min else 1
                        y_min -= padding
                        y_max += padding
                        y_norm = (y - y_min) / (y_max - y_min)
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
                else:
                    if spalten not in df.columns:
                        continue
                    #y = pd.to_numeric(df[spalten], errors="coerce")
                    #x = plot_x(df, df.index, zeitzone)
                    
                    if k.get("nur_baggern"):
                        mask = df["Status"] == 2
                    else:
                        mask = pd.Series([True]*len(df), index=df.index)
                    y = pd.to_numeric(df.loc[mask, spalten], errors="coerce")
                    x = plot_x(df, mask, zeitzone)                    
                    
                    
                    y_min, y_max = y.min(), y.max()
                    if pd.isna(y_min) or pd.isna(y_max) or y_max == y_min:
                        continue
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
        
            st.markdown("#### Umlaufgrafik - Prozeßdaten")
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
            st.plotly_chart(fig, use_container_width=True)

        
            
#==============================================================================================================================
# Tab 3 - Diagramm Tiefe Baggerkopf 
#==============================================================================================================================
            

        with tab3:
        
        # --- 2. Spezialdiagramm: NUR Abs_Tiefe_Kopf_ (Status==2, split by gap) ----------------------------------------------------------------

            kurven_abs_tiefe = [
                {"spaltenname": "Abs_Tiefe_Kopf_", "label": "Abs. Tiefe Kopf [m]", "farbe": "#186A3B", "sichtbar": True, "dicke": 2, "dash": None},   # Dunkelgrün
                {"spaltenname": "Solltiefe_Aktuell", "label": "Solltiefe [m]", "farbe": "#B22222", "sichtbar": True, "dicke": 2, "dash": "dash"},    # Rot, gestrichelt
            ]
            
           
            fig2 = go.Figure()  # Erstelle ein neues leeres Plotly-Diagramm
            
            # Schleife durch alle Kurven, die im Spezialdiagramm angezeigt werden sollen
            for k in kurven_abs_tiefe:
                spalten = get_spaltenname(k["spaltenname"], seite)  # Hole die Spaltennamen für die aktuelle Kurve (abhängig von der Seite)
                farbe = k["farbe"]  # Definiere die Farbe der Linie
                label = k["label"]  # Label für die Legende der Kurve
            
                if spalten is None:  # Wenn keine Spalte existiert, überspringe diese Kurve
                    continue
            
                # Wenn es sich um eine Liste von Spalten handelt (z.B. für BB oder SB)
                if isinstance(spalten, list):
                    for s in spalten:
                        if s not in df_plot.columns:  # Überprüfe, ob die Spalte überhaupt existiert
                            continue
            
                        # Filtere nur Daten, bei denen Status == 2
                        status_mask = df_plot["Status"] == 2
                        df_filtered = df_plot.loc[status_mask, ["timestamp", s]].copy()  # Kopiere nur die relevanten Daten
            
                        # Konvertiere die Zeitstempel zu Datetime und sortiere die Daten
                        df_filtered["timestamp"] = pd.to_datetime(df_filtered["timestamp"])
                        df_filtered = df_filtered.sort_values("timestamp").reset_index(drop=True)
            
                        # Splitte die Daten basierend auf Zeitlücken (maximal 2 Minuten)
                        df_filtered = split_by_gap(df_filtered, max_gap_minutes=2)
            
                        # Schleife durch die verschiedenen Segmente, die nach Zeitlücken getrennt wurden
                        for seg_id, seg in df_filtered.groupby("segment"):
                            y = pd.to_numeric(seg[s], errors="coerce")  # Konvertiere die Y-Werte in numerische Werte
                            x = seg["timestamp"]  # Die X-Werte (Zeitstempel)
            
                            # Wenn keine gültigen Y-Werte vorhanden sind, überspringe dieses Segment
                            if y.empty or pd.isna(y.max()):
                                continue
            
                            # Bestimme das Minimum und Maximum der Y-Werte für das Segment
                            y_min = y.min()
                            #y_max = -2.0  # Der Maximalwert für das Diagramm soll immer 0 (Wasseroberfläche) sein
                            y_max = y.max() + 4 
                                        
                            # Padding berechnen (Puffer) für das Minimum
                            padding = abs(y_min) * 0.1 if abs(y_min) > 0 else 1
                            y_min -= padding  # Füge Puffer zum Minimum hinzu
            
                            # Füge das Segment als Kurve in das Diagramm hinzu
                            fig2.add_trace(go.Scatter(
                                x=x,  # X-Werte (Zeitstempel)
                                y=y,  # Y-Werte (Tiefe)
                                mode="lines",  # Die Kurve als Linie darstellen
                                name=f"{label} ({s[-2:]})" if seg_id == 0 else None,  # Name der Kurve (für die Legende)
                                customdata=pd.DataFrame({"original": y}),  # Speichere die originalen Y-Werte für den Hover-Text
                                hovertemplate=f"{label} ({s[-2:]}): %{{customdata[0]:.2f}}<extra></extra>",  # Tooltip für den Hover-Effekt
                                line=dict(
                                    color=farbe,
                                    width=k.get("dicke", 2),
                                    dash=k.get("dash", None)
                                ),  # Farbe der Linie
                                visible=True,  # Die Kurve soll sichtbar sein
                                connectgaps=False,  # Keine Lücken zwischen den Punkten, falls Daten fehlen
                                showlegend=(seg_id == 0),  # Zeige die Legende nur für das erste Segment
                            ))
            
                # Wenn es sich nur um eine einzelne Spalte handelt (keine Liste)
                else:
                    if spalten not in df_plot.columns:  # Wenn die Spalte nicht existiert, überspringe sie
                        continue
            
                    # Filtere Daten, bei denen Status == 2
                    status_mask = df_plot["Status"] == 2
                    df_filtered = df_plot.loc[status_mask, ["timestamp", spalten]].copy()
            
                    # Konvertiere die Zeitstempel zu Datetime und sortiere die Daten
                    df_filtered["timestamp"] = pd.to_datetime(df_filtered["timestamp"])
                    df_filtered = df_filtered.sort_values("timestamp").reset_index(drop=True)
            
                    # Splitte die Daten basierend auf Zeitlücken (maximal 2 Minuten)
                    df_filtered = split_by_gap(df_filtered, max_gap_minutes=2)
            
                    # Schleife durch die verschiedenen Segmente, die nach Zeitlücken getrennt wurden
                    for seg_id, seg in df_filtered.groupby("segment"):
                        y = pd.to_numeric(seg[spalten], errors="coerce")
                        x = plot_x(seg, [True]*len(seg), zeitzone)

            
                        if y.empty or pd.isna(y.max()):
                            continue
            
                        y_min = y.min()
                        #y_max = 0.0
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
                            line=dict(
                                color=farbe,
                                width=k.get("dicke", 2),
                                dash=k.get("dash", None)
                            ),
                            visible=True,
                            connectgaps=False,
                            showlegend=(seg_id == 0),
                        ))
            

       # --- Dynamische Skalierung der Y-Achse auf Basis der Baggertiefe
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
                y_min = tiefen.min() - 2    # 1 Meter tiefer als Minimum
                y_max = tiefen.max() + 2    # 4 Meter flacher als Maximum
            else:
                y_min = -20
                y_max = 0
                    

            
            # Stelle sicher, dass die Spalten existieren und Daten da sind!
            if (
                "Solltiefe_Aktuell" in df_plot.columns
                and "Solltiefe_Oben" in df_plot.columns
                and "Solltiefe_Unten" in df_plot.columns
            ):
                # Nur Status==2 Daten (wie beim Tiefen-Plot)
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
            
            # --- ab hier wie gehabt update_layout etc. ---

 
            
            # --- Layout aktualisieren ---
            st.markdown("#### Baggerkopftiefe")
            fig2.update_layout(
                height=500,  # Höhe des Diagramms
                yaxis=dict(
                    title="Tiefe [m]",  # Y-Achse bezeichnen
                    range=[y_min, y_max],         # Die Tiefe beginnt bei y_min und geht bis 0 (Oberfläche)
                    showgrid=True,  # Gitterlinien anzeigen
                    gridcolor="lightgray"  # Farbe der Gitterlinien
                ),
                xaxis=dict(
                    title="Zeit",  # X-Achse bezeichnen
                    showticklabels=True,  # Zeitstempel auf der X-Achse anzeigen
                    showgrid=True,  # Gitterlinien auf der X-Achse anzeigen
                    gridcolor="lightgray",  # Farbe der Gitterlinien
                    type="date"  # X-Achse als Datum darstellen
                ),
                hovermode="x unified",  # Hover-Effekte für alle Kurven gleichzeitig anzeigen
                showlegend=True,  # Legende anzeigen
                legend=dict(orientation="v", x=1.02, y=1)  # Position der Legende einstellen
            )
            
            # Das Diagramm in der Streamlit-App anzeigen
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
            st.markdown("<h3 style='font-size: 24px'>Auflistung aller Umläufe</h3>", unsafe_allow_html=True)
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
                        format_dauer(dauer_leerfahrt),
                        anzeige_start_baggern.strftime("%H:%M:%S") if anzeige_start_baggern else "-",
                        format_dauer(dauer_baggern),
                        anzeige_start_vollfahrt.strftime("%H:%M:%S") if anzeige_start_vollfahrt else "-",
                        format_dauer(dauer_vollfahrt),
                        anzeige_start_verklapp.strftime("%H:%M:%S") if anzeige_start_verklapp else "-",
                        format_dauer(dauer_verklapp),
                        anzeige_ende_umlauf.strftime("%H:%M:%S") if anzeige_ende_umlauf else "-",
                        format_dauer(dauer_umlauf)
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
                st.markdown("<h3 style='font-size: 24px'>Aufsummierte Dauer</h3>", unsafe_allow_html=True)
                st.dataframe(gesamtzeiten_df, use_container_width=True, hide_index=True)


            else:
                st.info("⚠️ Es wurden keine vollständigen Umläufe erkannt.")

            
#==============================================================================================================================
# Tab 5 - Numerische Auswertung Umlaufdaten
#==============================================================================================================================


        with tab5:
            st.markdown("## ✨ Numerische Umlauf-Auswertung")
            st.markdown(
                """
                <style>
                .big-val { font-size: 2rem; font-weight: bold; }
                .main-col { background: #f7fafc; border-radius: 12px; padding: 1rem 2rem; margin-bottom: 2rem; }
                .highlight { background: #eef6ff; border-radius: 10px; padding: 0.5rem 1rem; }
                .section-head { font-size: 1.25rem; margin-top: 2rem; margin-bottom: 0.75rem; color: #186A3B; font-weight: bold;}
                </style>
                """,
                unsafe_allow_html=True,
            )
        
            if umlauf_auswahl != "Alle" and not umlauf_info_df.empty:
                row = umlauf_info_df[umlauf_info_df["Umlauf"] == umlauf_auswahl].iloc[0]
        
                def fmt(v, nachkomma=2, einheit=None):
                    if pd.isnull(v) or v in ["-", None, ""]:
                        return "-"
                    try:
                        val = float(v)
                        num = f"{val:,.{nachkomma}f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        return f"{num}{(' ' + einheit) if einheit else ''}"
                    except Exception:
                        return str(v)
        
                # Hauptzeiten als große Werte (in 3 Spalten)
                col1, col2, col3 = st.columns(3)
                col1.markdown(f"<div class='main-col'><div class='big-val'>{fmt(row.get('Umlaufdauer', '-'), 1)} min</div><div>Umlaufdauer</div></div>", unsafe_allow_html=True)
                col2.markdown(f"<div class='main-col'><div class='big-val'>{fmt(row.get('Baggerzeit', '-'), 1)} min</div><div>Baggerzeit</div></div>", unsafe_allow_html=True)
                col3.markdown(f"<div class='main-col'><div class='big-val'>{fmt(row.get('Ladungsmasse', '-'), 2, 't')}</div><div>Ladungsmasse</div></div>", unsafe_allow_html=True)
        
                # Zeiten: Start, Ende, Phasen
                st.markdown("<div class='section-head'>Zeiten</div>", unsafe_allow_html=True)
                zeit_col1, zeit_col2 = st.columns(2)
                zeit_col1.markdown(f"<div class='highlight'>🟢 Beginn: <b>{row.get('Start Leerfahrt', '-')}</b></div>", unsafe_allow_html=True)
                zeit_col1.markdown(f"<div class='highlight'>⛏️ Baggerstart: <b>{row.get('Start Baggern', '-')}</b></div>", unsafe_allow_html=True)
                zeit_col1.markdown(f"<div class='highlight'>🚢 Entladestart: <b>{row.get('Start Entladen', '-')}</b></div>", unsafe_allow_html=True)
                zeit_col2.markdown(f"<div class='highlight'>🔴 Ende: <b>{row.get('Ende', '-')}</b></div>", unsafe_allow_html=True)
                zeit_col2.markdown(f"<div class='highlight'>⛏️ Baggerende: <b>{row.get('Ende Baggern', '-')}</b></div>", unsafe_allow_html=True)
                zeit_col2.markdown(f"<div class='highlight'>🚢 Entladeende: <b>{row.get('Ende Entladen', '-')}</b></div>", unsafe_allow_html=True)
        
                # Mengen & Volumina
                st.markdown("<div class='section-head'>Mengen & Volumina</div>", unsafe_allow_html=True)
                menge_col1, menge_col2, menge_col3 = st.columns(3)
                menge_col1.metric("Ladungsvolumen [m³]", fmt(row.get("Ladungsvolumen", "-"), 0))
                menge_col2.metric("Ladungsdichte [t/m³]", fmt(row.get("Ladungsdichte", "-"), 3))
                menge_col3.metric("Abrechnungsvolumen", fmt(row.get("Abrechnungsvolumen", "-"), 0, "m³"))
        
                # Strecken
                st.markdown("<div class='section-head'>Strecken</div>", unsafe_allow_html=True)
                strecke_col1, strecke_col2 = st.columns(2)
                strecke_col1.metric("Leerfahrt [km]", fmt(row.get("Strecke Leerfahrt", "-"), 2))
                strecke_col1.metric("Baggern [km]", fmt(row.get("Strecke Baggern", "-"), 2))
                strecke_col2.metric("Vollfahrt [km]", fmt(row.get("Strecke Vollfahrt", "-"), 2))
                strecke_col2.metric("Entladung [km]", fmt(row.get("Strecke Entladen", "-"), 2))
        
                # Bonus & Zusatzinfos
                st.markdown("<div class='section-head'>Weitere Kennzahlen</div>", unsafe_allow_html=True)
                col_bonus, col_abrechnung = st.columns(2)
                col_bonus.metric("Bonusfaktor", fmt(row.get("Bonusfaktor", "-"), 2))
                col_abrechnung.metric("Verbleib", fmt(row.get("Verbleib", "-"), 2, "t"))
            else:
                st.info("Bitte einen Umlauf auswählen!")







#=====================================================================================
    except Exception as e:
        st.error(f"Fehler beim Verarbeiten der Dateien: {e}")
else:
    st.info("Bitte lade mindestens eine MoNa-Datei hoch.")
