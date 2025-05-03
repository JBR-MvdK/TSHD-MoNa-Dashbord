# =========================================================================================
# modul_solltiefe_tshd.py
# =========================================================================================

from shapely.geometry import Point
from pyproj import Transformer

def berechne_solltiefe_fuer_df(
    df, baggerfelder, seite, epsg_code,
    toleranz_oben=1.0, toleranz_unten=0.5, solltiefe_slider=0.0
):
    """
    Weist nur bei Status 2 (Baggern) oder Status 4 (Verbringen) eine Solltiefe und den Polygonnamen zu.
    
    - Status 2 → nutzt BB oder SB-Koordinaten je nach gewählter Seite
    - Status 4 → nutzt zentrale Schiffskoordinaten
    - Andere Status → keine Wertezuweisung

    Parameter:
    - df                : Pandas DataFrame mit MoNa-Datenpunkten
    - baggerfelder      : Liste von Polygonen mit Attributen (aus XML)
    - seite             : Aktive Baggerseite ("BB", "SB", "BB+SB")
    - epsg_code         : EPSG-Code der Originaldaten (z. B. "EPSG:25832")
    - toleranz_oben     : Aufschlag zur Solltiefe nach oben (Standard: 1.0 m)
    - toleranz_unten    : Abzug zur Solltiefe nach unten (Standard: 0.5 m)
    - solltiefe_slider  : Manuell gesetzte Solltiefe als Fallback

    Rückgabe:
    - df : Original-DataFrame ergänzt um:
        'Solltiefe_Aktuell', 'Solltiefe_Oben', 'Solltiefe_Unten', 'Polygon_Name'
    """

    # Wenn keine Polygone oder grundlegende Koordinaten vorhanden sind
    if not baggerfelder or "RW_Schiff" not in df or "HW_Schiff" not in df:
        df["Solltiefe_Aktuell"] = None
        df["Polygon_Name"] = None
        return df

    transformer = Transformer.from_crs(epsg_code, "EPSG:4326", always_xy=True)

    solltiefen = []
    polygonnamen = []

    for _, row in df.iterrows():
        try:
            status = row.get("Status", None)

            # Nur Status 2 und 4 werden ausgewertet
            if status == 2:
                rw = row.get("RW_BB") if seite in ["BB", "BB+SB"] and "RW_BB" in df else row.get("RW_SB")
                hw = row.get("HW_BB") if seite in ["BB", "BB+SB"] and "HW_BB" in df else row.get("HW_SB")
            elif status == 4:
                rw = row.get("RW_Schiff")
                hw = row.get("HW_Schiff")
            else:
                solltiefen.append(None)
                polygonnamen.append(None)
                continue  # Alle anderen Status überspringen

            if rw is None or hw is None:
                solltiefen.append(None)
                polygonnamen.append("außerhalb")
                continue

            lon, lat = transformer.transform(rw, hw)
            punkt = Point(lon, lat)

            matched = False
            for feld in baggerfelder:
                if feld["polygon"].contains(punkt):
                    solltiefen.append(feld["solltiefe"])
                    polygonnamen.append(feld.get("name", "Unbenannt"))
                    matched = True
                    break

            if not matched:
                solltiefen.append(None)
                polygonnamen.append("außerhalb")

        except Exception:
            solltiefen.append(None)
            polygonnamen.append("außerhalb")

    # Spalten zuweisen
    df["Solltiefe_Aktuell"] = solltiefen
    df["Polygon_Name"] = polygonnamen

    # Toleranzbereiche berechnen (nur dort, wo Solltiefe gesetzt wurde)
    df.loc[df["Solltiefe_Aktuell"] == 0, "Solltiefe_Aktuell"] = None
    if "Solltiefe_Aktuell" in df.columns:
        df["Solltiefe_Oben"] = df["Solltiefe_Aktuell"] + toleranz_oben
        df["Solltiefe_Unten"] = df["Solltiefe_Aktuell"] - toleranz_unten

    return df
