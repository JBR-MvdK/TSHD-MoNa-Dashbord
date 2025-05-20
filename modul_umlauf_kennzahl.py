import pandas as pd
import streamlit as st

# ------------------------------------------------------------
# 🕓 Hilfsfunktion zur sicheren Zeitzonenanpassung
# ------------------------------------------------------------
def ensure_utc(timestamp, reference_series):
    # Falls Referenz-Zeitreihe timezone-aware ist und Timestamp nicht: Lokalisiere als UTC
    if hasattr(reference_series.iloc[0], "tzinfo") and reference_series.dt.tz is not None:
        if timestamp.tzinfo is None:
            return timestamp.tz_localize("UTC")
    return timestamp

# ------------------------------------------------------------
# 🔢 Zahlenformatierung für die Anzeige
# ------------------------------------------------------------
def format_number(value):
    return f"{value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".") if value is not None else "-"

# ------------------------------------------------------------
# 🔍 Ermittle Anfangs- und Endwert inkl. Zeitstempel für eine Spalte
# ------------------------------------------------------------
def berechne_delta_werte(df, spalte):
    if not df.empty:
        leer = df[spalte].iloc[0]
        leer_ts = df["timestamp"].iloc[0]
        voll = df[spalte].iloc[-1]
        voll_ts = df["timestamp"].iloc[-1]
        return leer, leer_ts, voll, voll_ts
    return None, None, None, None

# ------------------------------------------------------------
# 📊 Hauptfunktion zur Berechnung der Umlaufkennzahlen
# ------------------------------------------------------------
def berechne_umlauf_kennzahlen(row, df):
    # 📆 Start- und Endzeit des Umlaufs inkl. Zeitzonenprüfung
    t_start = ensure_utc(pd.to_datetime(row["Start Leerfahrt"]), df["timestamp"])
    t_ende = ensure_utc(pd.to_datetime(row["Ende"]), df["timestamp"])

    # 📦 Eingrenzen des Datensatzes auf aktuellen Umlaufzeitraum
    df_umlauf = df[(df["timestamp"] >= t_start) & (df["timestamp"] <= t_ende)]

    # ⛏️ Filter: nur Status_neu == "Baggern"
    df_baggern = df_umlauf[df_umlauf["Status_neu"] == "Baggern"]

    # 📌 Initialisiere Dichteinformationen
    dichte_info = {}

    # 🔧 Variante 1: Manuelle Dichtewerte (MoNa-Modus aktiv)
    if st.session_state.get("bonus_methode") == "mona":
        manuelle_werte = st.session_state.get("bonus_mona_werte", {})
        dichte_info.update({
            "Dichte_Polygon_Name": "manuell",
            "Ortsdichte": manuelle_werte.get("ortsdichte"),
            "Ortsspezifisch": manuelle_werte.get("ortspezifisch"),
            "Mindichte": manuelle_werte.get("mindichte"),
            "Maxdichte": manuelle_werte.get("maxdichte"),
        })

    # 🧠 Variante 2: Automatische Ableitung der häufigsten Werte in den Polygonfeldern
    if st.session_state.get("bonus_methode") != "mona":
        for spalte in ["Dichte_Polygon_Name", "Ortsdichte", "Ortsspezifisch", "Mindichte", "Maxdichte"]:
            if spalte in df_baggern.columns:
                mode_val = df_baggern[spalte].mode(dropna=True)
                dichte_info[spalte] = mode_val.iloc[0] if not mode_val.empty else None
            else:
                dichte_info[spalte] = None

    # 📐 Starte Delta-Berechnung für Verdrängung und Volumen
    verdraengung_leer, verdraengung_leer_ts, verdraengung_voll, verdraengung_voll_ts = berechne_delta_werte(df_baggern, "Verdraengung")
    volumen_leer, volumen_leer_ts, volumen_voll, volumen_voll_ts = berechne_delta_werte(df_baggern, "Ladungsvolumen")

    # ➗ Differenzwerte
    delta_verdraengung = (
        verdraengung_voll - verdraengung_leer
        if verdraengung_voll is not None and verdraengung_leer is not None else None
    )
    ladungsvolumen = (
        volumen_voll - volumen_leer
        if volumen_voll is not None and volumen_leer is not None else None
    )

    # 🧾 Formatierte Zahlen für UI
    delta_verdraengung_disp = format_number(delta_verdraengung)
    verdraengung_leer_disp = format_number(verdraengung_leer)
    verdraengung_voll_disp = format_number(verdraengung_voll)
    volumen_leer_disp = format_number(volumen_leer)
    volumen_voll_disp = format_number(volumen_voll)
    ladungsvolumen_disp = format_number(ladungsvolumen)

    # 📊 Weitere Metriken
    ladungsdichte = df_umlauf["Ladungsdichte"].max()
    abrechnungsvolumen = df_umlauf["Abrechnungsvolumen"].max() if "Abrechnungsvolumen" in df_umlauf.columns else None
    bonusfaktor = df_umlauf["Bonusfaktor"].max() if "Bonusfaktor" in df_umlauf.columns else None
    strecke_leerfahrt = df_umlauf["Strecke Leerfahrt"].sum() if "Strecke Leerfahrt" in df_umlauf.columns else None

    # ✅ Rückgabe aller berechneten Werte in strukturierter Form
    return {
        # Hauptwerte
        "Umlaufdauer": (t_ende - t_start).total_seconds() / 60,
        "Baggerzeit": (
            (row.get("Start Vollfahrt") - row.get("Start Baggern")).total_seconds() / 60
            if row.get("Start Vollfahrt") and row.get("Start Baggern") else None
        ),
        "Verdraengung": delta_verdraengung,
        "Ladungsvolumen": ladungsvolumen,
        "Ladungsdichte": ladungsdichte,
        "Abrechnungsvolumen": abrechnungsvolumen,
        "Bonusfaktor": bonusfaktor,
        "Strecke Leerfahrt": strecke_leerfahrt,

        # Rohdaten zur Analyse
        "verdraengung_leer": verdraengung_leer,
        "verdraengung_leer_ts": verdraengung_leer_ts,
        "verdraengung_voll": verdraengung_voll,
        "verdraengung_voll_ts": verdraengung_voll_ts,
        "volumen_leer": volumen_leer,
        "volumen_leer_ts": volumen_leer_ts,
        "volumen_voll": volumen_voll,
        "volumen_voll_ts": volumen_voll_ts,

        # Anzeigeformate
        "delta_verdraengung_disp": delta_verdraengung_disp,
        "verdraengung_leer_disp": verdraengung_leer_disp,
        "verdraengung_voll_disp": verdraengung_voll_disp,
        "ladungsvolumen_disp": ladungsvolumen_disp,
        "volumen_leer_disp": volumen_leer_disp,
        "volumen_voll_disp": volumen_voll_disp,

        # Dichtepolygon-Zuordnung
        "Dichte_Polygon_Name": dichte_info["Dichte_Polygon_Name"],
        "Ortsdichte": dichte_info["Ortsdichte"],
        "Ortsspezifisch": dichte_info["Ortsspezifisch"],
        "Mindichte": dichte_info["Mindichte"],
        "Maxdichte": dichte_info.get("Maxdichte"),
    }
