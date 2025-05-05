# ===============================================================================================================================
# 📈 MODUL_PROZESSGRAFIK – Interaktive Zeitreihendiagramme zu Pegel, Dichte, Tiefe, etc.
# Zeigt Messgrößen entlang des Umlaufs inkl. Statusfarben, Strategiezeitpunkten, Solltiefe etc.
# ===============================================================================================================================

import plotly.graph_objects as go
import pandas as pd
import numpy as np
import streamlit as st

# 📦 Eigene Hilfsfunktionen
from modul_hilfsfunktionen import convert_timestamp, plot_x, split_by_gap, get_spaltenname
from modul_startend_strategie import berechne_start_endwerte


# -------------------------------------------------------------------------------------------------------------------------------
# 🔎 status_bereiche – Start- und Endpunkte für Statusbereiche (z. B. Status 2) im Verlauf finden
# Wird genutzt, um farbige Rechtecke in der Grafik zu setzen (z. B. Baggerphase hervorheben)
# -------------------------------------------------------------------------------------------------------------------------------
def status_bereiche(df, status_liste):
    mask = df["Status"].isin(status_liste)
    indices = mask.astype(int).diff().fillna(0)
    starts = df.index[(indices == 1)].tolist()
    ends = df.index[(indices == -1)].tolist()
    if mask.iloc[0]:
        starts = [df.index[0]] + starts
    if mask.iloc[-1]:
        ends += [df.index[-1]]
    return starts, ends


# -------------------------------------------------------------------------------------------------------------------------------
# 📊 zeige_prozessgrafik_tab – Hauptdiagramm mit Verlauf aller Messgrößen für gewählten Umlauf
# -------------------------------------------------------------------------------------------------------------------------------
def zeige_prozessgrafik_tab(df, zeitzone, row, schiffsparameter, schiff, seite="BB+SB", plot_key="prozessgrafik"):
    """
    Zeichnet interaktive Zeitreihen zu Dichte, Tiefe, Pegel, Verdrängung etc. für einen Umlauf.
    Die Kurven werden normalisiert (0–1) für übersichtliche Darstellung und Statusphasen farbig hinterlegt.
    """

    if row is None:
        st.info("Kein Umlauf ausgewählt.")
        return

    # 🕒 Zeitrahmen bestimmen
    t_start = pd.to_datetime(row["Start Leerfahrt"]).tz_localize("UTC") if pd.to_datetime(row["Start Leerfahrt"]).tzinfo is None else row["Start Leerfahrt"]
    t_ende  = pd.to_datetime(row["Ende"]).tz_localize("UTC") if pd.to_datetime(row["Ende"]).tzinfo is None else row["Ende"]

    # 🔄 UTC-Angabe sicherstellen
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")

    df_umlauf = df[(df["timestamp"] >= t_start) & (df["timestamp"] <= t_ende)]
    strategie = schiffsparameter.get(schiff, {}).get("StartEndStrategie", {})
    werte, _ = berechne_start_endwerte(df_umlauf, strategie, df_gesamt=df) if "Verdraengung" in df_umlauf.columns else ({}, {})

    # 🎨 Kurven-Konfiguration (sichtbare + unsichtbare Messgrößen)
    # Dynamisch je nach Datenverfügbarkeit
    kurven_fuellstand = [
        {"spaltenname": col, "label": f"{col.replace('_', ' ')} [m]", "farbe": "#AAB7B8", "sichtbar": False, "dicke": 1}
        for col in [
            'Fuellstand_BB_vorne', 'Fuellstand_SB_vorne',
            'Fuellstand_BB_mitte', 'Fuellstand_SB_mitte',
            'Fuellstand_BB_hinten', 'Fuellstand_SB_hinten'
        ]
        if col in df.columns and df[col].notnull().any()
    ]

    kurven_haupt = [
        {"spaltenname": "Status", "label": "Status", "farbe": "#BDBDBD", "sichtbar": False},
        {"spaltenname": "Pegel", "label": "Pegel [m]", "farbe": "#3D5A80", "sichtbar": False},
        {"spaltenname": "Tiefgang_vorne", "label": "Tiefgang vorne [m]", "farbe": "#5B84B1", "sichtbar": False},
        {"spaltenname": "Tiefgang_hinten", "label": "Tiefgang hinten [m]", "farbe": "#5B84B1", "sichtbar": False},
        {"spaltenname": "Verdraengung", "label": "Verdrängung [t]", "farbe": "#A67C52", "sichtbar": True},
        {"spaltenname": "Gemischdichte_", "label": "Gemischdichte [t/m³]", "farbe": "#628395", "sichtbar": False, "nur_baggern": True},
        {"spaltenname": "Ladungsvolumen", "label": "Ladungsvolumen [m³]", "farbe": "#7D8CA3", "sichtbar": True},
        {"spaltenname": "Ladungsmasse", "label": "Ladungsmasse [t]", "farbe": "#8E735B", "sichtbar": False},
        # ... weitere Felder ...
    ] + kurven_fuellstand

    fig = go.Figure()
    df_plot = df.sort_values("timestamp").reset_index(drop=True)

    # 🟡 Statushinterlegung (z. B. Baggern = blau)
    for status, farbe, name in [([2], "rgba(0,180,255,0.12)", "Baggern"), ([4, 5, 6], "rgba(0,255,80,0.11)", "Verbringen")]:
        for s, e in zip(*status_bereiche(df, status)):
            fig.add_vrect(
                x0=convert_timestamp(df.loc[s, "timestamp"], zeitzone),
                x1=convert_timestamp(df.loc[e, "timestamp"], zeitzone),
                fillcolor=farbe, layer="below", line_width=0,
                annotation_text=name, annotation_position="top left"
            )

    # 📈 Kurven hinzufügen
    for k in kurven_haupt:
        spalten = get_spaltenname(k["spaltenname"], seite)
        if isinstance(spalten, list):
            spalten = [s for s in spalten if s in df.columns]
        else:
            spalten = [spalten] if spalten in df.columns else []

        for s in spalten:
            mask = (df["Status"] == 2) if k.get("nur_baggern") else pd.Series(True, index=df.index)
            y = pd.to_numeric(df.loc[mask, s], errors="coerce")
            x = plot_x(df, mask, zeitzone)
            if y.empty or y.min() == y.max():
                continue
            y_norm = (y - y.min()) / (y.max() - y.min())
            fig.add_trace(go.Scatter(
                x=x, y=y_norm, customdata=y,
                hovertemplate=f"{k['label']} ({s[-2:]}): %{{customdata:.2f}}<extra></extra>",
                mode="lines", name=k["label"] if len(spalten) == 1 else f"{k['label']} ({s[-2:]})",
                line=dict(color=k["farbe"], width=k.get("dicke", 2)),
                visible=True if k["sichtbar"] else "legendonly"
            ))

    # 📍 Strategiepunkte als vertikale Linien
    for key, color in [
        ("Verdraengung Start TS", "#A67C52"),
        ("Verdraengung Ende TS", "#A67C52"),
        ("Ladungsvolumen Start TS", "#8C8C8C"),
        ("Ladungsvolumen Ende TS", "#8C8C8C")
    ]:
        ts = werte.get(key)
        if ts is not None and pd.notnull(ts):
            fig.add_vline(
                x=convert_timestamp(ts, zeitzone),
                line=dict(color=color, width=2, dash="dot"),
                opacity=0.8
            )

    # 📋 Layout
    fig.update_layout(
        height=600,
        yaxis=dict(showticklabels=False, gridcolor="lightgray"),
        xaxis=dict(title="Zeit", type="date", showgrid=True, gridcolor="lightgray"),
        hovermode="x unified",
        showlegend=True,
        legend=dict(orientation="v", x=1.02, y=1)
    )

    st.plotly_chart(fig, use_container_width=True, key=plot_key)


# -------------------------------------------------------------------------------------------------------------------------------
# 📏 zeige_baggerkopftiefe_grafik – Separate Grafik zur Darstellung der Baggertiefe (nur Status 2)
# -------------------------------------------------------------------------------------------------------------------------------
def zeige_baggerkopftiefe_grafik(df, zeitzone, seite="BB+SB"):
    """
    Zeigt die absolute Tiefe des Baggerkopfs im Vergleich zur Solltiefe über die Zeit.
    
    ✔ Nur Daten mit Status = 2 (Baggern) werden berücksichtigt.
    ✔ Darstellung erfolgt getrennt für BB, SB oder beide Seiten (BB+SB).
    ✔ Optionales Toleranzband zeigt die Solltiefe ± definierte Ober-/Untergrenzen als roten Korridor.
    """

    # 🧹 Vorverarbeitung: sortiere nach Zeit und setze Index zurück
    df_plot = df.copy().sort_values("timestamp").reset_index(drop=True)

    # 🔧 Kurvenkonfiguration: welche Linien sollen geplottet werden?
    kurven_abs_tiefe = [
        {"spaltenname": "Abs_Tiefe_Kopf_", "label": "Abs. Tiefe Kopf [m]", "farbe": "#186A3B", "sichtbar": True, "dicke": 2, "dash": None},
        {"spaltenname": "Solltiefe_Aktuell", "label": "Solltiefe [m]", "farbe": "#B22222", "sichtbar": True, "dicke": 2, "dash": "dash"},
    ]

    fig2 = go.Figure()

    # 📈 Schleife durch alle zu zeichnenden Linien (z. B. Kopf BB, Kopf SB, Solltiefe)
    for k in kurven_abs_tiefe:
        spalten = get_spaltenname(k["spaltenname"], seite)
        farbe = k["farbe"]
        label = k["label"]

        # 💡 Skip, wenn Spalte nicht vorhanden
        if spalten is None:
            continue

        # Falls mehrere Spalten (BB+SB): filtere gültige
        if isinstance(spalten, list):
            spalten = [s for s in spalten if s in df_plot.columns]
        else:
            spalten = [spalten] if spalten in df_plot.columns else []

        # 🔄 Zeichne Kurven pro Spalte
        for s in spalten:
            status_mask = df_plot["Status"] == 2
            df_filtered = df_plot.loc[status_mask, ["timestamp", s]].copy()
            df_filtered = df_filtered.sort_values("timestamp").reset_index(drop=True)

            # Unterteilung in Segmente bei größeren Zeitlücken
            df_filtered = split_by_gap(df_filtered, max_gap_minutes=2)

            # 📉 Segmentweise Zeichnung
            for seg_id, seg in df_filtered.groupby("segment"):
                y = pd.to_numeric(seg[s], errors="coerce")
                x = plot_x(seg, [True] * len(seg), zeitzone)
                if y.empty or pd.isna(y.max()):
                    continue
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

    # 📏 Y-Achsenbereich automatisch skalieren basierend auf Messdaten
    tiefe_col = get_spaltenname("Abs_Tiefe_Kopf_", seite)
    if isinstance(tiefe_col, list):
        vorhandene = [col for col in tiefe_col if col in df_plot.columns]
        if vorhandene:
            df_plot["_tmp_tiefe_mittel"] = df_plot[vorhandene].mean(axis=1)
            tiefe_col = "_tmp_tiefe_mittel"
        elif tiefe_col:
            tiefe_col = tiefe_col[0]

    # Tiefenbereich für Y-Achse berechnen
    mask_tiefe = (df_plot["Status"] == 2) & df_plot[tiefe_col].notnull()
    if mask_tiefe.sum() > 0:
        tiefen = df_plot.loc[mask_tiefe, tiefe_col]
        y_min = tiefen.min() - 2
        y_max = tiefen.max() + 2
    else:
        y_min = -20
        y_max = 0

    # 🔴 Toleranzbereich (Solltiefe ± Abweichung) zeichnen
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

    # 🎨 Layout & Darstellung
    fig2.update_layout(
        height=600,
        yaxis=dict(title="Tiefe [m]", range=[y_min, y_max], showgrid=True, gridcolor="lightgray"),
        xaxis=dict(title="Zeit", type="date", showgrid=True, gridcolor="lightgray"),
        hovermode="x unified",
        showlegend=True,
        legend=dict(orientation="v", x=1.02, y=1),
    )

    # ⬆ Anzeige im Streamlit-Frontend
    st.plotly_chart(fig2, use_container_width=True)
