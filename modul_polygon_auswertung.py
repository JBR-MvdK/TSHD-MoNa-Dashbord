import pandas as pd

def berechne_punkte_und_zeit(df, statuswert, status_col="Status", sekunden_pro_punkt=10):
    """
    Zählt für einen Statuswert (z.B. 2 oder 4 oder 'Baggern'),
    wie viele Punkte in jedem Polygon lagen und berechnet daraus die Zeit in Minuten.

    Parameters:
    - df: Pandas DataFrame
    - statuswert: z. B. 2, 4 oder "Baggern"
    - status_col: "Status" oder "Status_neu" – wird explizit übergeben!
    - sekunden_pro_punkt: Zeitintervall pro Datenpunkt (Standard: 10s)

    Rückgabe: DataFrame mit 'Anzahl_Punkte' und 'Zeit_Minuten' je Polygonnamen.
    """

    if status_col not in df.columns:
        raise ValueError(f"Spalte '{status_col}' nicht im DataFrame enthalten.")

    df_status = df[df[status_col] == statuswert]

    if "Polygon_Name" not in df_status.columns:
        return pd.DataFrame(columns=["Anzahl_Punkte", "Zeit_Minuten"])

    punkte = df_status["Polygon_Name"].value_counts().sort_index()
    zeit = (punkte * sekunden_pro_punkt) / 60

    return pd.DataFrame({
        "Anzahl_Punkte": punkte,
        "Zeit_Minuten": zeit.round(1)
    })
