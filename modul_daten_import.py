import pandas as pd

def lade_excel_feststoffdaten(file, zeitzone="Europe/Berlin"):
    """
    Wandelt manuell gepflegte Excel-Daten in eine standardisierte DataFrame um,
    inkl. lokaler Zeitstempel-Konvertierung in UTC.
    """

    df = pd.read_excel(file, header=None)
    df = df[[1, 2, 9, 29, 31]]  # Umlauf, Datum, Zeit (Bagger), Feststoff, Zentrifuge
    df.columns = ["umlauf", "datum", "zeit_beginn", "feststoff", "proz_wert"]
    df = df[df["umlauf"].notna()].copy()
    df["datum"] = df["datum"].fillna(method="ffill")

    # Zeitstempel kombinieren und in UTC umwandeln
    df["timestamp_local"] = pd.to_datetime(
        df["datum"].astype(str) + " " + df["zeit_beginn"].astype(str),
        errors="coerce"
    )
    df["timestamp_local"] = df["timestamp_local"].dt.tz_localize(
        zeitzone, ambiguous="NaT", nonexistent="shift_forward"
    )
    df["timestamp_beginn_baggern"] = df["timestamp_local"].dt.tz_convert("UTC")

    # Prozentwerte korrekt umwandeln (z. B. 0.75 → 75 oder 75 → 75)
    df["proz_wert"] = pd.to_numeric(df["proz_wert"], errors="coerce")
    if df["proz_wert"].max(skipna=True) <= 1:
        df["proz_wert"] *= 100

    return df[["timestamp_beginn_baggern", "feststoff", "proz_wert"]]

