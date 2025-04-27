import numpy as np
import pandas as pd

def berechne_strecke_status(df, status, rw_col="RW_Schiff", hw_col="HW_Schiff", status_col="Status", epsg_code=None):
    """
    Berechnet die Strecke für alle Datenpunkte mit Status=X,
    UTM-Koordinaten in [rw_col] und [hw_col] in Meter!
    Ergebnis: Strecke in Kilometern.
    """
    df_status = df[df[status_col] == status].sort_values("timestamp")
    if df_status.empty:
        return 0.0

    # Immer UTM: direkt euklidische Distanz in Meter → km
    coords = df_status[[rw_col, hw_col]].values.astype(float)
    dists = np.sqrt(np.sum(np.diff(coords, axis=0)**2, axis=1)) / 1000.0
    return np.sum(dists)

def berechne_strecken(df, rw_col="RW_Schiff", hw_col="HW_Schiff", status_col="Status", epsg_code=None):
    """Berechnet alle Strecken für die Phasen als Dictionary, gibt Werte in km zurück."""
    return {
        "leerfahrt": berechne_strecke_status(df, 1, rw_col, hw_col, status_col),
        "baggern": berechne_strecke_status(df, 2, rw_col, hw_col, status_col),
        "vollfahrt": berechne_strecke_status(df, 3, rw_col, hw_col, status_col),
        "verbringen": berechne_strecke_status(df, 4, rw_col, hw_col, status_col) +
                      berechne_strecke_status(df, 5, rw_col, hw_col, status_col) +
                      berechne_strecke_status(df, 6, rw_col, hw_col, status_col),
        "gesamt": None  # Summierst du unten im Hauptcode!
    }

