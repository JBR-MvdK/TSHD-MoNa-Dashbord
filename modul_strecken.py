import numpy as np
import pandas as pd

def berechne_strecke_status(df, status, rw_col="RW_Schiff", hw_col="HW_Schiff", status_col="Status", epsg_code=None):
    """
    Berechnet die Strecke für einen bestimmten Status innerhalb des DataFrames.
    
    Parameter:
    - df : Pandas DataFrame mit Positionsdaten
    - status : Statusnummer, z.B. 1 = Leerfahrt, 2 = Baggern etc.
    - rw_col : Name der Spalte mit Rechtswerten (X-Koordinate)
    - hw_col : Name der Spalte mit Hochwerten (Y-Koordinate)
    - status_col : Name der Status-Spalte
    - epsg_code : nicht genutzt hier, optionaler Parameter
    
    Rückgabe:
    - Strecke in Kilometern (float)
    """

    # Filtere Datenpunkte mit gewünschtem Status und sortiere sie zeitlich
    df_status = df[df[status_col] == status].sort_values("timestamp")
    
    if df_status.empty:
        return 0.0  # Keine Daten -> 0 km

    # Koordinaten extrahieren und in Float-Array konvertieren
    coords = df_status[[rw_col, hw_col]].values.astype(float)

    # Euklidische Distanzen zwischen aufeinanderfolgenden Punkten berechnen (in Meter)
    dists = np.sqrt(np.sum(np.diff(coords, axis=0)**2, axis=1)) / 1000.0  # Umrechnen in Kilometer

    # Summe aller Teilstrecken = Gesamtdistanz
    return np.sum(dists)

def berechne_strecken(df, rw_col="RW_Schiff", hw_col="HW_Schiff", status_col="Status", epsg_code=None):
    """
    Berechnet alle Hauptstrecken (Leerfahrt, Baggern, Vollfahrt, Verbringen) als Dictionary.

    Parameter:
    - df : Pandas DataFrame
    - rw_col : Name der Spalte mit Rechtswerten
    - hw_col : Name der Spalte mit Hochwerten
    - status_col : Name der Status-Spalte
    - epsg_code : optional, wird hier nicht genutzt

    Rückgabe:
    - Dictionary mit den Strecken in km:
      {"leerfahrt": ..., "baggern": ..., "vollfahrt": ..., "verbringen": ..., "gesamt": None}
    """

    return {
        "leerfahrt": berechne_strecke_status(df, 1, rw_col, hw_col, status_col),
        "baggern": berechne_strecke_status(df, 2, rw_col, hw_col, status_col),
        "vollfahrt": berechne_strecke_status(df, 3, rw_col, hw_col, status_col),
        "verbringen": berechne_strecke_status(df, 4, rw_col, hw_col, status_col) +
                      berechne_strecke_status(df, 5, rw_col, hw_col, status_col) +
                      berechne_strecke_status(df, 6, rw_col, hw_col, status_col),
        "gesamt": None  # Gesamtstrecke summierst du später im Hauptcode!
    }
