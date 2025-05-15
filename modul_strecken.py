import numpy as np
import pandas as pd

def berechne_strecke_status(df, status, rw_col="RW_Schiff", hw_col="HW_Schiff", status_col="Status"):
    """
    Berechnet die Strecke für einen bestimmten Statuswert (z. B. 1, 2, 3, 4...) 
    oder symbolischen Phasenwert (z. B. 'Leerfahrt', 'Baggern').

    Parameter:
    - df: Pandas DataFrame mit Positionsdaten
    - status: int oder str → gewünschter Statuswert (numerisch oder als Bezeichner)
    - rw_col, hw_col: Spaltennamen für Koordinaten (Rechts-/Hochwert)
    - status_col: 'Status' oder 'Status_neu' – legt fest, mit welcher Spalte gearbeitet wird

    Rückgabe:
    - Gesamtstrecke in Kilometern (float)
    """

    # Filtere Zeilen mit gewünschtem Statuswert und sortiere sie nach Zeit
    df_status = df[df[status_col] == status].sort_values("timestamp")
    
    if df_status.empty:
        return 0.0  # Kein passender Abschnitt gefunden

    # Koordinaten extrahieren und Distanz berechnen (euklidisch, in km)
    coords = df_status[[rw_col, hw_col]].dropna().values.astype(float)
    dists = np.sqrt(np.sum(np.diff(coords, axis=0)**2, axis=1)) / 1000.0
    return np.sum(dists)


def berechne_strecken(df, rw_col="RW_Schiff", hw_col="HW_Schiff", status_col="Status", epsg_code=None):
    """
    Berechnet die Strecken für alle relevanten Fahrphasen:

    Je nach gewählter Spalte (Status vs. Status_neu) unterscheidet sich die Auswertung:
    - 'Status': klassisch numerisch (1=Leerfahrt, 2=Baggern, ...)
    - 'Status_neu': symbolisch ('Leerfahrt', 'Baggern', ...)

    Rückgabe:
    - Dictionary mit Strecken (in km) je Phase: leerfahrt, baggern, vollfahrt, verbringen, gesamt (optional)
    """

    if status_col == "Status_neu":
        # 💡 Phasenlogik über neue Statusbezeichnungen (Strings)
        return {
            "leerfahrt": berechne_strecke_status(df, "Leerfahrt", rw_col, hw_col, status_col),
            "baggern": berechne_strecke_status(df, "Baggern", rw_col, hw_col, status_col),
            "vollfahrt": berechne_strecke_status(df, "Vollfahrt", rw_col, hw_col, status_col),
            "verbringen": berechne_strecke_status(df, "Verbringen", rw_col, hw_col, status_col),
            "gesamt": None  # Kann bei Bedarf summiert werden
        }
    else:
        # 🧮 Klassische Statuslogik (1–6)
        return {
            "leerfahrt": berechne_strecke_status(df, 1, rw_col, hw_col, status_col),
            "baggern": berechne_strecke_status(df, 2, rw_col, hw_col, status_col),
            "vollfahrt": berechne_strecke_status(df, 3, rw_col, hw_col, status_col),
            "verbringen": sum([
                berechne_strecke_status(df, s, rw_col, hw_col, status_col) for s in [4, 5, 6]
            ]),
            "gesamt": None
        }


