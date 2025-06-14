# ===============================================================================================================================
# 🗺️ MODUL_KARTEN – Visualisierung von Fahrtdaten auf interaktiven Karten (Plotly Mapbox)
# ===============================================================================================================================
import math
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from pyproj import Transformer

from modul_hilfsfunktionen import convert_timestamp, format_dauer, split_by_gap



# -------------------------------------------------------------------------------------------------------------------------------
# 📍 Zoom und Mittelpunkt bestimmen
# -------------------------------------------------------------------------------------------------------------------------------

def berechne_map_center_zoom(
    df, transformer, pixel_width=1000, pixel_height=600, min_zoom=7, max_zoom=16
):
    if df.empty:
        return {"lat": 53.5, "lon": 8.2}, min_zoom

    coords = df.apply(lambda row: transformer.transform(row["RW_Schiff"], row["HW_Schiff"]), axis=1)
    lons, lats = zip(*coords)

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    center = {"lat": (min_lat + max_lat) / 2, "lon": (min_lon + max_lon) / 2}
    lat_range = max_lat - min_lat
    lon_range = max_lon - min_lon
    max_range = max(lat_range, lon_range)

    # 🔧 Neue heuristische Zoom-Formel: sanft, realistisch
    if max_range < 0.0005:
        zoom = max_zoom
    elif max_range < 0.005:
        zoom = 14
    elif max_range < 0.01:
        zoom = 13.5
    elif max_range < 0.03:
        zoom = 13
    elif max_range < 0.05:
        zoom = 12.5
    elif max_range < 0.1:
        zoom = 12
    elif max_range < 0.3:
        zoom = 11
    elif max_range < 0.5:
        zoom = 10
    else:
        zoom = min_zoom

    zoom = round(zoom, 2)


    return center, zoom



# -------------------------------------------------------------------------------------------------------------------------------
# 📍 plot_karte – Hauptfunktion zur Darstellung der Fahrtphasen (Status 1–6) auf einer Mapbox-Karte
# -------------------------------------------------------------------------------------------------------------------------------
def plot_karte(df, transformer, seite, status2_label, tiefe_spalte, mapbox_center, zeitzone, zeit_suffix="UTC", focus_trace=None, baggerfelder=None, dichte_polygone=None, show_status1=True, show_status2=True, show_status3=True, show_status456=True, return_fig=False):

    """
    Visualisiert den Fahrtverlauf anhand des Status-Feldes auf einer interaktiven Karte.
    Unterstützt farblich unterscheidbare Statusphasen (1–6), Tooltip-Darstellung sowie optionale Polygone (Baggerfelder).

    Parameter:
        - df: Pandas DataFrame mit MoNa-Fahrtdaten
        - transformer: PyProj-Transformer zur Koordinatenumwandlung (z. B. UTM ➝ WGS84)
        - seite: "BB", "SB" oder "BB+SB" – beeinflusst welche Spalten für Status 2 verwendet werden
        - status2_label: Bezeichnung für Status 2 (für Legende)
        - tiefe_spalte: Spaltenname für die Tiefenanzeige (z. B. 'Abs_Tiefe_Kopf_BB')
        - mapbox_center: Dictionary mit 'lat' und 'lon' für die initiale Kartenmitte
        - zeitzone: Zeitzone für Zeitdarstellung im Tooltip
        - zeit_suffix: Text wie "UTC" oder "Lokal", zur Anzeige im Tooltip
        - focus_trace: Optionaler Marker für Highlighting
        - baggerfelder: Optional, Liste von Polygonobjekten mit Namen und Solltiefe
    """

    fig = go.Figure()
    df_status2 = pd.DataFrame()
    df_456 = pd.DataFrame()
    
    # Tooltip bei Status 2: Tiefenanzeige
    # in modul_karten.py – innerhalb von plot_karte(...)

    def tooltip_text(row):
        ts = convert_timestamp(row["timestamp"], zeitzone)
        zeit = ts.strftime("%d.%m.%Y %H:%M:%S") if ts else "-"
        tiefe = row.get(tiefe_spalte)
        solltiefe = row.get("Solltiefe_Aktuell")
        umlauf = row.get("Umlauf_korrekt", "–")
        
        tooltip = f"🔁 Umlauf: {umlauf}"  # NEU    
        tooltip += f"<br>🕒 {zeit} ({zeit_suffix})"

        if pd.notnull(tiefe):
            tooltip += f"<br>📉 Baggerkopftiefe: {tiefe:.2f} m"
        if pd.notnull(solltiefe):
            tooltip += f"<br>🎯 Solltiefe: {solltiefe:.2f} m"

        return tooltip


    # Tooltip bei allen anderen Status: Geschwindigkeit
    def tooltip_status1_3(row):
        umlauf = row.get("Umlauf_korrekt", "–")
        ts = convert_timestamp(row["timestamp"], zeitzone)
        zeit = ts.strftime("%d.%m.%Y %H:%M:%S") if ts else "-"
        geschw = row.get("Geschwindigkeit", None)
        tooltip = f"🔁 Umlauf: {umlauf}"  # NEU            
        tooltip += f"<br>🕒 {zeit} ({zeit_suffix})"
        if pd.notnull(geschw):
            tooltip += f"<br>🚤 Geschwindigkeit: {geschw:.1f} kn"

        return tooltip


    # -------- Status 1 – Leerfahrt (grau) --------
    if show_status1:
        df_status1 = df[df["Status_neu"] == "Leerfahrt"].dropna(subset=["RW_Schiff", "HW_Schiff"])
        df_status1 = split_by_gap(df_status1)
        for seg_id, segment_df in df_status1.groupby("segment"):
            coords = segment_df.apply(lambda row: transformer.transform(row["RW_Schiff"], row["HW_Schiff"]), axis=1)
            lons, lats = zip(*coords)
            tooltips = segment_df.apply(tooltip_status1_3, axis=1)
            fig.add_trace(go.Scattermapbox(
                lon=lons, lat=lats, mode='lines',
                line=dict(width=1, color='rgba(150, 150, 150, 0.7)'),
                text=tooltips, hoverinfo='text',
                name='Status 1 (Leerfahrt)' if seg_id == 0 else None,
                showlegend=(seg_id == 0), legendgroup="status1"
                #visible="legendonly"
            ))

    # -------- Status 2 – Baggern (blau/grün, je nach Seite) --------
    if show_status2:
        df_status2 = df[df["Status_neu"] == "Baggern"]
        df_status2 = split_by_gap(df_status2)
        for seg_id, segment_df in df_status2.groupby("segment"):
            if seite in ["BB", "BB+SB"]:
                df_bb = segment_df.dropna(subset=["RW_BB", "HW_BB"])
                if not df_bb.empty:
                    lons, lats = zip(*df_bb.apply(lambda r: transformer.transform(r["RW_BB"], r["HW_BB"]), axis=1))
                    tooltips = df_bb.apply(tooltip_text, axis=1)
                    fig.add_trace(go.Scattermapbox(
                        lon=lons, lat=lats, mode='lines+markers',
                        marker=dict(size=6, color='rgba(0, 102, 204, 0.8)'),
                        line=dict(width=1, color='rgba(0, 102, 204, 0.8)'),
                        text=tooltips, hoverinfo='text',
                        name="Status 2 (Baggern, BB)" if seg_id == 0 else None,
                        showlegend=(seg_id == 0), legendgroup="status2bb"
                    ))
            if seite in ["SB", "BB+SB"]:
                df_sb = segment_df.dropna(subset=["RW_SB", "HW_SB"])
                if not df_sb.empty:
                    lons, lats = zip(*df_sb.apply(lambda r: transformer.transform(r["RW_SB"], r["HW_SB"]), axis=1))
                    tooltips = df_sb.apply(tooltip_text, axis=1)
                    fig.add_trace(go.Scattermapbox(
                        lon=lons, lat=lats, mode='lines+markers',
                        marker=dict(size=6, color='rgba(0, 204, 102, 0.8)'),
                        line=dict(width=2, color='rgba(0, 204, 102, 0.8)'),
                        text=tooltips, hoverinfo='text',
                        name="Status 2 (Baggern, SB)" if seg_id == 0 else None,
                        showlegend=(seg_id == 0), legendgroup="status2sb"
                    ))

    # -------- Status 3 – Vollfahrt (grün) --------
    if show_status3:
        df_status3 = df[df["Status_neu"] == "Vollfahrt"].dropna(subset=["RW_Schiff", "HW_Schiff"])
        df_status3 = split_by_gap(df_status3)
    
        for seg_id, segment_df in df_status3.groupby("segment"):
            coords = segment_df.apply(lambda row: transformer.transform(row["RW_Schiff"], row["HW_Schiff"]), axis=1)
            lons, lats = zip(*coords)
            tooltips = segment_df.apply(tooltip_status1_3, axis=1)
            fig.add_trace(go.Scattermapbox(
                lon=lons, lat=lats, mode='lines',
                line=dict(width=1, color='rgba(0, 153, 76, 0.8)'),
                text=tooltips, hoverinfo='text',
                name='Status 3 (Vollfahrt)' if seg_id == 0 else None,
                showlegend=(seg_id == 0), legendgroup="status3"
                #visible="legendonly"
            ))

    # -------- Status 4/5/6 – Verbringen (orange) --------
    if show_status456:
        df_456 = df[df["Status_neu"] == "Verbringen"].dropna(subset=["RW_Schiff", "HW_Schiff"])
        df_456 = split_by_gap(df_456)
    
        
        for seg_id, segment_df in df_456.groupby("segment"):
            lons, lats = zip(*segment_df.apply(lambda r: transformer.transform(r["RW_Schiff"], r["HW_Schiff"]), axis=1))
            tooltips = segment_df.apply(tooltip_status1_3, axis=1)
            fig.add_trace(go.Scattermapbox(
                lon=lons, lat=lats, mode='lines+markers',
                marker=dict(size=6, color='rgba(255, 140, 0, 0.8)'),
                line=dict(width=1, color='rgba(255, 140, 0, 0.8)'),
                text=tooltips, hoverinfo='text',
                name="Status 4/5/6 (Verbringen)" if seg_id == 0 else None,
                showlegend=(seg_id == 0), legendgroup="status456"
            ))

    # -------- Optional: Baggerfelder (Polygon-Umrisse) --------
    if baggerfelder:
        for idx, feld in enumerate(baggerfelder):
            coords = list(feld["polygon"].exterior.coords)
            lons, lats = zip(*coords)
            solltiefe = feld.get("solltiefe", 0.0)
            tooltip = feld["name"]
            if solltiefe and solltiefe != 0.0:
                tooltip += f"<br>Solltiefe: {solltiefe:.2f} m"
 
            fig.add_trace(go.Scattermapbox(
                lon=lons, lat=lats, mode="lines+markers",
                fill="toself", fillcolor="rgba(50, 90, 150, 0.2)",
                line=dict(color="rgba(30, 60, 120, 0.8)", width=2),
                marker=dict(size=3, color="rgba(30, 60, 120, 0.8)"),
                name="Baggerfelder" if idx == 0 else None,
                legendgroup="baggerfelder", showlegend=(idx == 0),
                text=[tooltip] * len(lons), hoverinfo="text"
            ))
            
    # -------- Optional: Dichtepolygone (transparente Flächen) --------
    if dichte_polygone:
        for idx, p in enumerate(dichte_polygone):
            if "polygon" not in p:
                continue  # ➤ z. B. manuelle Werte ohne Geometrie
            if not p["polygon"].is_valid:
                continue  # ➤ Ungültige Geometrie überspringen
    
            coords = list(p["polygon"].exterior.coords)
            lons, lats = zip(*coords)
            tooltip = (
                f"{p['name']}<br>"
                f"Ortsdichte: {p['ortsdichte']} t/m³<br>"
            )
            fig.add_trace(go.Scattermapbox(
                lon=lons, lat=lats,
                mode="lines+markers",
                fill="toself", fillcolor="rgba(200, 50, 50, 0.15)",
                line=dict(color="rgba(180, 40, 40, 0.9)", width=2),
                marker=dict(size=3, color="rgba(180, 40, 40, 0.9)"),
                name="Dichtepolygone" if idx == 0 else None,
                legendgroup="dichtepolygon", showlegend=(idx == 0),
                text=[tooltip] * len(lons), hoverinfo="text",
                visible="legendonly"
            ))


            


    # -------- Optionaler Marker (z. B. aktuell gewählter Punkt) --------
    if focus_trace:
        fig.add_trace(focus_trace)

    # -------- Kartenlayout (Mapbox & Legende) --------
    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox_zoom=12,
        mapbox_center=mapbox_center,
        height=600,
        margin=dict(r=0, l=0, t=0, b=0),
        legend=dict(
            x=0.01, y=0.99,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="gray",
            borderwidth=1
        )
    )

    if return_fig:
        return fig, df_status2, df_456
    else:
        st.plotly_chart(fig, use_container_width=True)
        return None, df_status2, df_456


# -------------------------------------------------------------------------------------------------------------------------------
# 📋 zeige_umlauf_info_karte – Zeigt zusammenfassende Informationen zum gewählten Umlauf (inkl. Phasenstart/-dauer)
# -------------------------------------------------------------------------------------------------------------------------------
def zeige_umlauf_info_karte(umlauf_auswahl, zeile, zeitzone, epsg_code, df):
    """
    Zeigt eine Übersichtstabelle mit Zeitpunkten und Dauern eines ausgewählten Umlaufs.
    Rückgabe:
        - gefiltertes df (nur Umlaufzeitraum)
        - Transformer für EPSG ➝ WGS84 (oder None bei Fehler)
    """
    if umlauf_auswahl != "Alle":
        if zeile.empty:
            st.warning("⚠️ Kein vollständiger Umlauf: (fehlende Statusdaten)")
        else:
            try:
                row = zeile.iloc[0]

                # Zeitmarken sammeln
                phase_keys = [
                    ("Start Leerfahrt", "anzeige_start_leerfahrt"),
                    ("Start Baggern", "anzeige_start_baggern"),
                    ("Start Vollfahrt", "anzeige_start_vollfahrt"),
                    ("Start Verklappen/Pump/Rainbow", "anzeige_start_verklapp"),
                    ("Ende", "anzeige_ende_umlauf")
                ]
                phase_times = {}
                for key, out in phase_keys:
                    t = row.get(key)
                    phase_times[out] = convert_timestamp(pd.Timestamp(t) if t is not None else None, zeitzone) if t else None

                if not phase_times["anzeige_start_leerfahrt"] or not phase_times["anzeige_ende_umlauf"]:
                    st.warning("⚠️ Beginn oder Ende des Umlaufs fehlen.")
                    return df, None

                # DataFrame auf Zeitraum des Umlaufs beschränken
                df = df[(df["timestamp"] >= phase_times["anzeige_start_leerfahrt"]) &
                        (df["timestamp"] <= phase_times["anzeige_ende_umlauf"])]

                # Dauerberechnung je Phase
                dauer_leerfahrt = phase_times["anzeige_start_baggern"] - phase_times["anzeige_start_leerfahrt"] if phase_times["anzeige_start_baggern"] else None
                dauer_baggern = phase_times["anzeige_start_vollfahrt"] - phase_times["anzeige_start_baggern"] if phase_times["anzeige_start_vollfahrt"] else None
                dauer_vollfahrt = phase_times["anzeige_start_verklapp"] - phase_times["anzeige_start_vollfahrt"] if phase_times["anzeige_start_verklapp"] else None
                dauer_verklapp = phase_times["anzeige_ende_umlauf"] - phase_times["anzeige_start_verklapp"] if phase_times["anzeige_start_verklapp"] else None
                dauer_umlauf = phase_times["anzeige_ende_umlauf"] - phase_times["anzeige_start_leerfahrt"]

                # Tabellenanzeige vorbereiten
                columns = pd.MultiIndex.from_tuples([
                    ("Umlauf", "Nr."), ("Datum", ""),
                    ("Leerfahrt", "Beginn"), ("Leerfahrt", "Dauer"),
                    ("Baggern", "Beginn"), ("Baggern", "Dauer"),
                    ("Vollfahrt", "Beginn"), ("Vollfahrt", "Dauer"),
                    ("Verklappen", "Beginn"), ("Verklappen", "Dauer"),
                    ("Umlauf", "Ende"), ("Umlauf", "Dauer")
                ])

                data = [[
                    row.get("Umlauf", "-"),
                    phase_times["anzeige_start_leerfahrt"].strftime("%d.%m.%Y"),
                    phase_times["anzeige_start_leerfahrt"].strftime("%H:%M:%S"),
                    format_dauer(dauer_leerfahrt),
                    phase_times["anzeige_start_baggern"].strftime("%H:%M:%S") if phase_times["anzeige_start_baggern"] else "-",
                    format_dauer(dauer_baggern),
                    phase_times["anzeige_start_vollfahrt"].strftime("%H:%M:%S") if phase_times["anzeige_start_vollfahrt"] else "-",
                    format_dauer(dauer_vollfahrt),
                    phase_times["anzeige_start_verklapp"].strftime("%H:%M:%S") if phase_times["anzeige_start_verklapp"] else "-",
                    format_dauer(dauer_verklapp),
                    phase_times["anzeige_ende_umlauf"].strftime("%H:%M:%S"),
                    format_dauer(dauer_umlauf)
                ]]

                df_summary = pd.DataFrame(data, columns=columns)
                
                #Umlauftabelle - durch Panels ersetzt - kann aber der zeit wieder eingefügt werden
                #st.dataframe(df_summary, use_container_width=True, hide_index=True)

                transformer = Transformer.from_crs(epsg_code, "EPSG:4326", always_xy=True)
                return df, transformer

            except Exception as e:
                st.warning("⚠️ Der gewählte Umlauf ist unvollständig oder fehlerhaft.")
                st.info(f"(Details: {e})")
                return df, None

    # Wenn "Alle" ausgewählt wurde, keine Filterung, aber Transformer vorbereiten
    return df, Transformer.from_crs(epsg_code, "EPSG:4326", always_xy=True)
