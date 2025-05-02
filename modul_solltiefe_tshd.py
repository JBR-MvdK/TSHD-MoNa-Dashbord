# =========================================================================================
# modul_solltiefe_tshd.py
# =========================================================================================

from shapely.geometry import Point
from pyproj import Transformer

def berechne_solltiefe_fuer_df(
    df, baggerfelder, seite, epsg_code, toleranz_oben=1.0, toleranz_unten=0.5, solltiefe_slider=0.0
):
    """
    Weist jedem Punkt im DataFrame eine Solltiefe und den Namen des zugehörigen Baggerfeldes zu.

    Parameter:
    - df : Pandas DataFrame der MoNa-Daten
    - baggerfelder : Liste von Polygonen mit Attributen aus XML-Datei
    - seite : Baggerseite ("BB", "SB" oder "BB+SB")
    - epsg_code : EPSG-Code der Originaldaten (z.B. 'EPSG:25832')
    - toleranz_oben : Toleranz in Meter nach oben (default: 1.0 m)
    - toleranz_unten : Toleranz in Meter nach unten (default: 0.5 m)
    - solltiefe_slider : Solltiefe aus Slider (wenn keine XML-Daten vorhanden)

    Rückgabe:
    - df : DataFrame mit Spalten:
        'Solltiefe_Aktuell', 'Solltiefe_Oben', 'Solltiefe_Unten', 'Polygon_Name'
    """

    if not baggerfelder or "RW_Schiff" not in df or "HW_Schiff" not in df:
        # Fallback: alle mit Sliderwert belegen
        df["Solltiefe_Aktuell"] = solltiefe_slider if solltiefe_slider != 0 else None
        df["Polygon_Name"] = None
    else:
        transformer = Transformer.from_crs(epsg_code, "EPSG:4326", always_xy=True)

        rw_col = "RW_BB" if seite in ["BB", "BB+SB"] and "RW_BB" in df else "RW_SB"
        hw_col = "HW_BB" if seite in ["BB", "BB+SB"] and "HW_BB" in df else "HW_SB"

        if rw_col not in df or hw_col not in df:
            rw_col = "RW_Schiff"
            hw_col = "HW_Schiff"

        solltiefen = []
        polygonnamen = []

        for idx, row in df.iterrows():
            try:
                x, y = row[rw_col], row[hw_col]
                lon, lat = transformer.transform(x, y)
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
                    polygonnamen.append(None)

            except Exception:
                solltiefen.append(None)
                polygonnamen.append(None)

        df["Solltiefe_Aktuell"] = solltiefen
        df["Polygon_Name"] = polygonnamen

        # Fallback: Wenn alle Werte None oder 0
        mask_valide = df["Solltiefe_Aktuell"].notnull() & (df["Solltiefe_Aktuell"] != 0)
        if not mask_valide.any():
            df["Solltiefe_Aktuell"] = solltiefe_slider if solltiefe_slider != 0 else None
            df["Polygon_Name"] = None

    # 0-Werte maskieren
    df.loc[df["Solltiefe_Aktuell"] == 0, "Solltiefe_Aktuell"] = None

    # Toleranzbereiche
    if "Solltiefe_Aktuell" in df.columns:
        df["Solltiefe_Oben"] = df["Solltiefe_Aktuell"] + toleranz_oben
        df["Solltiefe_Unten"] = df["Solltiefe_Aktuell"] - toleranz_unten

    return df
