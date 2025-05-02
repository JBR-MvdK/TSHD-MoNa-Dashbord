import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from modul_hilfsfunktionen import convert_timestamp, plot_x
from modul_startend_strategie import berechne_start_endwerte

# ===================================================================================================
# 📉 Prozessgrafik: Darstellung aller wichtigen Zeitreihen über den Umlauf
# Zeigt Liniengrafiken inkl. Statusbereiche, strategischen Zeitpunkten und diversen Messgrößen
# ===================================================================================================

# ---------------------------------------------------------------------------------------------------
# 🔎 Hilfsfunktion: Start- und End-Indices von Statusblöcken ermitteln
# Wird verwendet, um z. B. Baggerphasen visuell hervorzuheben
# ---------------------------------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------------------------------
# 🔧 Hilfsfunktion: Dynamische Spaltenwahl je nach Schiffseite (z. B. "Gemischdichte_" + Seite)
# ---------------------------------------------------------------------------------------------------
def get_spaltenname(base, seite):
    if base.endswith("_") and seite in ["BB", "SB"]:
        return base + seite
    elif base.endswith("_") and seite == "BB+SB":
        return [base + "BB", base + "SB"]
    return base

# ---------------------------------------------------------------------------------------------------
# 🔄 Hauptfunktion: Generiert die Prozessgrafik für den gewählten Umlauf
# ---------------------------------------------------------------------------------------------------
def zeige_prozessgrafik_tab(df, zeitzone, row, schiffsparameter, schiff, seite="BB+SB", plot_key="prozessgrafik"):

    # 🧾 Sicherstellen, dass ein Umlauf geladen wurde
    if row is None:
        st.info("Kein Umlauf ausgewählt.")
        return

    # 📅 Zeitbereich des Umlaufs definieren (inkl. Zeitzonenprüfung)
    t_start = pd.to_datetime(row["Start Leerfahrt"]).tz_localize("UTC") if pd.to_datetime(row["Start Leerfahrt"]).tzinfo is None else row["Start Leerfahrt"]
    t_ende  = pd.to_datetime(row["Ende"]).tz_localize("UTC") if pd.to_datetime(row["Ende"]).tzinfo is None else row["Ende"]

    # ⏱ Zeitstempel im DataFrame auf UTC setzen, falls nötig
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")

    # 🔍 Daten des Umlaufs extrahieren
    df_umlauf = df[(df["timestamp"] >= t_start) & (df["timestamp"] <= t_ende)]
    strategie = schiffsparameter.get(schiff, {}).get("StartEndStrategie", {})

    # 🎯 Strategie-Auswertung ausführen (z. B. Verdrängung Start/Ende)
    werte, _ = berechne_start_endwerte(df_umlauf, strategie, df_gesamt=df) if "Verdraengung" in df_umlauf.columns else ({}, {})

    # ---------------------------------------------------------------------------------------------------
    # 📐 Konfiguriere die Kurven, die in der Grafik angezeigt werden sollen
    # ---------------------------------------------------------------------------------------------------

    # 🔹 Zusätzliche Füllstandskurven (pro Segment vorne/mittel/hinten + BB/SB)
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

    # 🔹 Hauptkurvenkonfiguration (sichtbar + optional gefiltert)
    kurven_haupt = [
        {"spaltenname": "Status", "label": "Status", "farbe": "#BDBDBD", "sichtbar": False},
        {"spaltenname": "Pegel", "label": "Pegel [m]", "farbe": "#3D5A80", "sichtbar": False},
        {"spaltenname": "Tiefgang_vorne", "label": "Tiefgang vorne [m]", "farbe": "#5B84B1", "sichtbar": False},
        {"spaltenname": "Tiefgang_hinten", "label": "Tiefgang hinten [m]", "farbe": "#5B84B1", "sichtbar": False},
        {"spaltenname": "Verdraengung", "label": "Verdrängung [t]", "farbe": "#A67C52", "sichtbar": True},
        {"spaltenname": "Gemischdichte_", "label": "Gemischdichte [t/m³]", "farbe": "#628395", "sichtbar": False, "nur_baggern": True},
        {"spaltenname": "Ladungsvolumen", "label": "Ladungsvolumen [m³]", "farbe": "#7D8CA3", "sichtbar": True},
        {"spaltenname": "Ladungsmasse", "label": "Ladungsmasse [t]", "farbe": "#8E735B", "sichtbar": False},
        {"spaltenname": "Ladungsdichte", "label": "Ladungsdichte [t/m³]", "farbe": "#6A7D8F", "sichtbar": False},
        {"spaltenname": "Feststoffkonzentration", "label": "Feststoffkonzentration [-]", "farbe": "#A9A9A9", "sichtbar": False},
        {"spaltenname": "Feststoffvolumen", "label": "Feststoffvolumen [m³]", "farbe": "#808B8D", "sichtbar": False},
        {"spaltenname": "Feststoffmasse", "label": "Feststoffmasse [t]", "farbe": "#4C6A6D", "sichtbar": False},
        {"spaltenname": "Geschwindigkeit", "label": "Geschwindigkeit", "farbe": "#9EADAF", "sichtbar": False},
        {"spaltenname": "Fuellstand_Mittel", "label": "Füllstand Mittel [m]", "farbe": "#4A6D8C", "sichtbar": False},
    ] + kurven_fuellstand

    # ---------------------------------------------------------------------------------------------------
    # 📈 Grafik erzeugen
    # ---------------------------------------------------------------------------------------------------
    fig = go.Figure()
    df_plot = df.sort_values("timestamp").reset_index(drop=True)

    # 🟦 Statusbereiche als farbige Rechtecke einfügen
    for status, farbe, name in [([2], "rgba(0,180,255,0.12)", "Baggern"), ([4, 5, 6], "rgba(0,255,80,0.11)", "Verbringen")]:
        for s, e in zip(*status_bereiche(df, status)):
            x0 = convert_timestamp(df.loc[s, "timestamp"], zeitzone)
            x1 = convert_timestamp(df.loc[e, "timestamp"], zeitzone)
            fig.add_vrect(x0=x0, x1=x1, fillcolor=farbe, layer="below", line_width=0,
                          annotation_text=name, annotation_position="top left")

    # 📉 Kurven zeichnen
    for k in kurven_haupt:
        spalten = get_spaltenname(k["spaltenname"], seite)
        farbe = k["farbe"]
        sicht = k["sichtbar"]
        label = k["label"]
        line_width = k.get("dicke", 2)

        if isinstance(spalten, list):  # z. B. Gemischdichte_BB und _SB
            for s in spalten:
                if s not in df.columns:
                    continue
                y = pd.to_numeric(df[s], errors="coerce")
                if y.empty or y.min() == y.max():
                    continue
                y_norm = (y - y.min()) / (y.max() - y.min())
                fig.add_trace(go.Scatter(
                    x=plot_x(df, df.index, zeitzone),
                    y=y_norm,
                    customdata=y,
                    hovertemplate=f"{label} ({s[-2:]}): %{{customdata:.2f}}<extra></extra>",
                    mode="lines", name=f"{label} ({s[-2:]})",
                    line=dict(color=farbe, width=line_width),
                    visible=True if sicht else "legendonly"
                ))
        else:
            if spalten not in df.columns:
                continue
            mask = (df["Status"] == 2) if k.get("nur_baggern") else pd.Series(True, index=df.index)
            y = pd.to_numeric(df.loc[mask, spalten], errors="coerce")
            x = plot_x(df, mask, zeitzone)
            if y.empty or y.min() == y.max():
                continue
            y_norm = (y - y.min()) / (y.max() - y.min())
            fig.add_trace(go.Scatter(
                x=x, y=y_norm, customdata=y,
                hovertemplate=f"{label}: %{{customdata:.2f}}<extra></extra>",
                mode="lines", name=label,
                line=dict(color=farbe, width=line_width),
                visible=True if sicht else "legendonly"
            ))

    # 🧭 Vertikale Linien für Start-/Endzeitpunkte aus der Strategieauswertung
    for key, color in [
        ("Verdraengung Start TS", "#A67C52"),
        ("Verdraengung Ende TS", "#A67C52"),
        ("Ladungsvolumen Start TS", "#8C8C8C"),
        ("Ladungsvolumen Ende TS", "#8C8C8C")
    ]:
        ts = werte.get(key)
        if ts is not None and pd.notnull(ts):
            ts = convert_timestamp(ts, zeitzone)
            fig.add_vline(x=ts, line=dict(color=color, width=2, dash="dot"), opacity=0.8)

    # ---------------------------------------------------------------------------------------------------
    # 🎨 Layout-Einstellungen der Grafik
    # ---------------------------------------------------------------------------------------------------
    fig.update_layout(
        height=600,
        yaxis=dict(showticklabels=False, gridcolor="lightgray"),
        xaxis=dict(title="Zeit", type="date", showgrid=True, gridcolor="lightgray"),
        hovermode="x unified",
        showlegend=True,
        legend=dict(orientation="v", x=1.02, y=1)
    )

    # 📤 Darstellung im Streamlit-Frontend
    st.plotly_chart(fig, use_container_width=True, key=plot_key)
