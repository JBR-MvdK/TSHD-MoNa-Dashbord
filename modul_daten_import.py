import pandas as pd
import streamlit as st

def extrahiere_uhrzeit(z):
    if pd.isna(z):
        return None
    try:
        ts = pd.to_datetime(z)
        if ts.date() == pd.Timestamp("1900-01-01").date():
            return ts.time()
        return ts.time()
    except Exception:
        return z

def korrigiere_datum(row):
    """Wenn Baggerstart-Uhrzeit < Umlaufbeginn, dann ist es der Folgetag."""
    try:
        beginn_umlauf = pd.to_datetime(str(row["zeit_beginn_umlauf"])).time()
        beginn_baggern = pd.to_datetime(str(row["zeit_beginn_baggern"])).time()
        if beginn_baggern < beginn_umlauf:
            return row["datum_umlauf"] + pd.Timedelta(days=1)
    except Exception:
        pass
    return row["datum_umlauf"]

def lade_excel_feststoffdaten(file, zeitzone="Europe/Berlin"):
    """
    Wandelt manuell gepflegte Excel-Daten in eine standardisierte DataFrame um,
    inkl. lokaler Zeitstempel-Konvertierung in UTC.
    """
    df = pd.read_excel(file, header=None, skiprows=14)
    df = df[[1, 2, 7, 9, 29, 31]]
    df.columns = ["umlauf", "datum_umlauf", "zeit_beginn_umlauf", "zeit_beginn_baggern", "feststoff", "proz_wert"]

    df = df[df["umlauf"].notna()].copy()
    df["datum_umlauf"] = df["datum_umlauf"].fillna(method="ffill")

    # 🛠 Zeit bereinigen
    df["zeit_beginn_baggern"] = df["zeit_beginn_baggern"].apply(extrahiere_uhrzeit)

    # 📅 Datum für Baggerstart ggf. um +1 Tag verschieben
    df["datum_baggern"] = df.apply(korrigiere_datum, axis=1)

    # 🕒 Kombinieren zu lokalem Timestamp
    df["timestamp_local"] = pd.to_datetime(
        df["datum_baggern"].astype(str) + " " + df["zeit_beginn_baggern"].astype(str),
        errors="coerce"
    )
    df["timestamp_local"] = df["timestamp_local"].dt.tz_localize(
        zeitzone, ambiguous="NaT", nonexistent="shift_forward"
    )
    df["timestamp_beginn_baggern"] = df["timestamp_local"].dt.tz_convert("UTC")

    # 🎯 Prozentwerte konvertieren
    df["proz_wert"] = pd.to_numeric(df["proz_wert"], errors="coerce")
    if df["proz_wert"].max(skipna=True) <= 1:
        df["proz_wert"] *= 100

    ## 🧪 Debug
    #st.write("📋 Erste Zeilen der Rohdaten:")
    #st.dataframe(df.head(30))

    #st.write("🧪 Ungültige Zeilen (fehlender Timestamp):")
    #problematische = df[df["timestamp_local"].isna()]
    #st.dataframe(problematische)

    return df[["timestamp_beginn_baggern", "feststoff", "proz_wert"]]
