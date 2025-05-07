import pandas as pd

def berechne_punkte_und_zeit(df, statuswert, sekunden_pro_punkt=10):
    """
    Zählt für einen Statuswert (z.B. 2 oder 4), wie viele Punkte in jedem Polygon lagen,
    und berechnet daraus die Zeit in Minuten.

    Rückgabe: DataFrame mit 'Anzahl_Punkte' und 'Zeit_Minuten' je Polygonnamen.
    """
    df_status = df[df["Status"] == statuswert]
    punkte = df_status["Polygon_Name"].value_counts().sort_index()
    zeit = (punkte * sekunden_pro_punkt) / 60

    return pd.DataFrame({
        "Anzahl_Punkte": punkte,
        "Zeit_Minuten": zeit.round(1)
    })

