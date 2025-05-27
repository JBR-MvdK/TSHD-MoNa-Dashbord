import pandas as pd

def initialisiere_manuell_df(umlauf_info_df, df_auswertung):
    """
    Erstellt die Grundstruktur für die manuelle Eingabetabelle `df_manuell`.

    - Nimmt Startzeitpunkt und Dichteinfos je Umlauf auf
    - Legt leere Felder für manuelle Werte an
    """
    df = umlauf_info_df[["Umlauf", "Start Baggern"]].copy()
    df = df.rename(columns={"Start Baggern": "timestamp_beginn_baggern"})
    df["timestamp_beginn_baggern"] = pd.to_datetime(df["timestamp_beginn_baggern"], utc=True)

    if not df_auswertung.empty and "Umlauf" in df_auswertung.columns:
        df = df.merge(
            df_auswertung[[
                "Umlauf", "Dichte_Polygon_Name", "Ortsdichte", "Ortsspezifisch", "Mindichte", "Maxdichte"
            ]],
            on="Umlauf", how="left"
        )

    # Leerspalten für manuelle Eingaben
    df["feststoff"] = None
    df["proz_wert"] = None

    return df


def merge_manuelle_daten(df_manuell, df_csv=None, df_excel=None):
    """
    Führt manuelle CSV- oder Excel-Daten in `df_manuell` ein.

    - CSV: exakter Timestamp-Match
    - Excel: nearest match mit Toleranz ±5min
    """
    def ensure_utc(df, spalte):
        df[spalte] = pd.to_datetime(df[spalte], errors="coerce", utc=True)
        return df

    df_manuell = ensure_utc(df_manuell, "timestamp_beginn_baggern")

    # === CSV-Merge ===
    if df_csv is not None and not df_csv.empty:
        df_csv = ensure_utc(df_csv, "timestamp_beginn_baggern")
        df_import_cols = [col for col in df_csv.columns if col != "timestamp_beginn_baggern"]

        df_manuell = df_manuell.merge(
            df_csv[["timestamp_beginn_baggern"] + df_import_cols],
            on="timestamp_beginn_baggern",
            how="left",
            suffixes=("", "_import")
        )

        for col in df_import_cols:
            col_import = f"{col}_import"
            if col_import in df_manuell.columns:
                df_manuell[col] = df_manuell[col_import].combine_first(df_manuell[col])
                df_manuell.drop(columns=[col_import], inplace=True)

    # === Excel-Merge (nearest match ±5min) ===
    if df_excel is not None and not df_excel.empty:
        df_excel = ensure_utc(df_excel, "timestamp_beginn_baggern")

        df_manuell = df_manuell.sort_values("timestamp_beginn_baggern")
        df_excel = df_excel.sort_values("timestamp_beginn_baggern")

        df_manuell = pd.merge_asof(
            df_manuell,
            df_excel,
            on="timestamp_beginn_baggern",
            direction="nearest",
            tolerance=pd.Timedelta(minutes=5),
            suffixes=("", "_excel")
        )

        for col in ["feststoff", "proz_wert"]:
            col_excel = f"{col}_excel"
            if col_excel in df_manuell.columns:
                df_manuell[col] = df_manuell[col_excel].combine_first(df_manuell[col])
                df_manuell.drop(columns=[col_excel], inplace=True)

    # Erkennung von fehlgeschlagenen Matches (z. B. zur Anzeige in UI)
    fehlende = df_manuell[df_manuell["feststoff"].isna() | df_manuell["proz_wert"].isna()]

    return df_manuell, fehlende
