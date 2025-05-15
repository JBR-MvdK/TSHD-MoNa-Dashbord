import pandas as pd

def ensure_utc(timestamp, reference_series):
    if hasattr(reference_series.iloc[0], "tzinfo") and reference_series.dt.tz is not None:
        if timestamp.tzinfo is None:
            return timestamp.tz_localize("UTC")
    return timestamp

def format_number(value):
    return f"{value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".") if value is not None else "-"

def berechne_delta_werte(df, spalte):
    if not df.empty:
        leer = df[spalte].iloc[0]
        leer_ts = df["timestamp"].iloc[0]
        voll = df[spalte].iloc[-1]
        voll_ts = df["timestamp"].iloc[-1]
        return leer, leer_ts, voll, voll_ts
    return None, None, None, None

def berechne_umlauf_kennzahlen(row, df):
    # Start- und Endzeit mit Zeitzonenprüfung
    t_start = ensure_utc(pd.to_datetime(row["Start Leerfahrt"]), df["timestamp"])
    t_ende = ensure_utc(pd.to_datetime(row["Ende"]), df["timestamp"])

    # Relevanter Zeitraum
    df_umlauf = df[(df["timestamp"] >= t_start) & (df["timestamp"] <= t_ende)]

    # Status == 2 → Baggern
    df_baggern = df_umlauf[df_umlauf["Status_neu"] == "Baggern"]


    # Verdraengung und Volumen bestimmen
    verdraengung_leer, verdraengung_leer_ts, verdraengung_voll, verdraengung_voll_ts = berechne_delta_werte(df_baggern, "Verdraengung")
    volumen_leer, volumen_leer_ts, volumen_voll, volumen_voll_ts = berechne_delta_werte(df_baggern, "Ladungsvolumen")

    # Differenzen berechnen
    delta_verdraengung = (
        verdraengung_voll - verdraengung_leer
        if verdraengung_voll is not None and verdraengung_leer is not None else None
    )
    ladungsvolumen = (
        volumen_voll - volumen_leer
        if volumen_voll is not None and volumen_leer is not None else None
    )

    # Formatiert für Anzeige
    delta_verdraengung_disp = format_number(delta_verdraengung)
    verdraengung_leer_disp = format_number(verdraengung_leer)
    verdraengung_voll_disp = format_number(verdraengung_voll)
    volumen_leer_disp = format_number(volumen_leer)
    volumen_voll_disp = format_number(volumen_voll)
    ladungsvolumen_disp = format_number(ladungsvolumen)

    # Weitere Kennzahlen
    ladungsdichte = df_umlauf["Ladungsdichte"].max()
    abrechnungsvolumen = df_umlauf["Abrechnungsvolumen"].max() if "Abrechnungsvolumen" in df_umlauf.columns else None
    bonusfaktor = df_umlauf["Bonusfaktor"].max() if "Bonusfaktor" in df_umlauf.columns else None
    strecke_leerfahrt = df_umlauf["Strecke Leerfahrt"].sum() if "Strecke Leerfahrt" in df_umlauf.columns else None

    return {
        # Berechnete Werte
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

        # Debug-Rohdaten
        "verdraengung_leer": verdraengung_leer,
        "verdraengung_leer_ts": verdraengung_leer_ts,
        "verdraengung_voll": verdraengung_voll,
        "verdraengung_voll_ts": verdraengung_voll_ts,
        "volumen_leer": volumen_leer,
        "volumen_leer_ts": volumen_leer_ts,
        "volumen_voll": volumen_voll,
        "volumen_voll_ts": volumen_voll_ts,

        # Formatierte Anzeige
        "delta_verdraengung_disp": delta_verdraengung_disp,
        "verdraengung_leer_disp": verdraengung_leer_disp,
        "verdraengung_voll_disp": verdraengung_voll_disp,
        "ladungsvolumen_disp": ladungsvolumen_disp,
        "volumen_leer_disp": volumen_leer_disp,
        "volumen_voll_disp": volumen_voll_disp,
    }


