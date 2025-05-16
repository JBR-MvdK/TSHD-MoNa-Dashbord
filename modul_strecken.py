import numpy as np
import pandas as pd
import streamlit as st

def berechne_strecke_status(df, status, rw_col="RW_Schiff", hw_col="HW_Schiff", status_col="Status"):
    """
    Berechnet die Strecke für eine bestimmte Betriebsphase (Status), basierend auf den Koordinaten.
    Bezieht den letzten Punkt vor Beginn sowie den ersten Punkt nach Ende der Phase mit ein,
    um realistische Übergänge zu berücksichtigen.

    Parameter:
    - df         : Pandas DataFrame mit Zeit- und Positionsdaten
    - status     : Gewünschter Statuswert (int oder str), z. B. 1 oder "Leerfahrt"
    - rw_col     : Spaltenname für Rechtswert (X-Koordinate)
    - hw_col     : Spaltenname für Hochwert (Y-Koordinate)
    - status_col : Spaltenname für den Status ("Status" oder "Status_neu")

    Rückgabe:
    - Gesamtstrecke in Kilometern (float)
    """

    # ⏱️ Zeitlich sortieren
    df = df.sort_values("timestamp").reset_index(drop=True)

    # 🔍 Maske für den gewünschten Statuswert
    mask = df[status_col] == status
    if not mask.any():
        return 0.0  # Keine passenden Zeitpunkte vorhanden

    # 📌 Ersten und letzten Index der Statusphase
    indices = mask[mask].index.tolist()
    start_idx, end_idx = indices[0], indices[-1]

    # ➕ Punkt direkt vor dem Phasenbeginn hinzufügen (falls möglich)
    if start_idx > 0:
        indices = [start_idx - 1] + indices

    # ➕ Punkt direkt nach dem Phasenende hinzufügen (falls möglich)
    if end_idx < len(df) - 1:
        indices = indices + [end_idx + 1]

    # 🔢 Relevante Punkte extrahieren (RW/HW dürfen nicht leer sein)
    df_sub = df.loc[indices].dropna(subset=[rw_col, hw_col])
    coords = df_sub[[rw_col, hw_col]].values.astype(float)

    # 🧮 Strecke berechnen (euklidisch, in km)
    if len(coords) < 2:
        return 0.0  # Nicht genug Punkte zur Berechnung

    dists = np.sqrt(np.sum(np.diff(coords, axis=0)**2, axis=1)) / 1000.0
    return np.sum(dists)




def berechne_strecken(df, rw_col="RW_Schiff", hw_col="HW_Schiff", status_col=None, epsg_code=None):
    """
    Berechnet die Strecken für alle relevanten Fahrphasen.

    Automatischer Wechsel zu 'Status_neu', wenn Spalte vorhanden ist.

    Rückgabe:
    - Dictionary mit Strecken (in km) je Phase
    """

    # 🔁 Automatischer Wechsel zu Status_neu wenn vorhanden
    if status_col is None:
        status_col = "Status_neu" if "Status_neu" in df.columns else "Status"




    if status_col == "Status_neu":
        # 💡 Neue symbolische Statuswerte
        return {
            "leerfahrt": berechne_strecke_status(df, "Leerfahrt", rw_col, hw_col, status_col),
            "baggern": berechne_strecke_status(df, "Baggern", rw_col, hw_col, status_col),
            "vollfahrt": berechne_strecke_status(df, "Vollfahrt", rw_col, hw_col, status_col),
            "verbringen": berechne_strecke_status(df, "Verbringen", rw_col, hw_col, status_col),
            "gesamt": None
        }
    else:
        # 🧮 Klassische numerische Statuswerte
        return {
            "leerfahrt": berechne_strecke_status(df, 1, rw_col, hw_col, status_col),
            "baggern": berechne_strecke_status(df, 2, rw_col, hw_col, status_col),
            "vollfahrt": berechne_strecke_status(df, 3, rw_col, hw_col, status_col),
            "verbringen": sum([
                berechne_strecke_status(df, s, rw_col, hw_col, status_col) for s in [4, 5, 6]
            ]),
            "gesamt": None
        }



