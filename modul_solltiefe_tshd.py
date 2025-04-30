# =========================================================================================
# modul_solltiefe_tshd.py
# =========================================================================================

from shapely.geometry import Point
from pyproj import Transformer

def berechne_solltiefe_fuer_df(
    df, baggerfelder, seite, epsg_code, toleranz_oben=1.0, toleranz_unten=0.5, solltiefe_slider=0.0
):
    """
    Weist jedem Punkt im DataFrame eine Solltiefe zu – je nach Lage in einem Baggerfeld (aus XML) oder über einen Default-Sliderwert.

    Parameter:
    - df : Pandas DataFrame der MoNa-Daten
    - baggerfelder : Liste von Polygonen und Solltiefen aus XML-Datei
    - seite : Baggerseite ("BB", "SB" oder "BB+SB")
    - epsg_code : EPSG-Code der Originaldaten (z.B. 'EPSG:25832')
    - toleranz_oben : Toleranz in Meter nach oben (default: 1.0 m)
    - toleranz_unten : Toleranz in Meter nach unten (default: 0.5 m)
    - solltiefe_slider : Solltiefe aus Slider (nur, wenn keine XML-Daten vorhanden)

    Rückgabe:
    - df : DataFrame mit neuen Spalten 'Solltiefe_Aktuell', 'Solltiefe_Oben', 'Solltiefe_Unten'
    """

    # === Fall 1: Keine Baggerfelder oder fehlende Positionsspalten ===
    if not baggerfelder or "RW_Schiff" not in df or "HW_Schiff" not in df:
        # Alle Punkte bekommen den Wert aus dem Solltiefen-Slider
        df["Solltiefe_Aktuell"] = solltiefe_slider if solltiefe_slider != 0 else None

    else:
        # === Fall 2: Baggerfelder sind vorhanden ===
        # Transformer von EPSG-Code nach WGS84 erstellen
        transformer = Transformer.from_crs(epsg_code, "EPSG:4326", always_xy=True)
        
        # Spaltenwahl je nach Baggerseite
        rw_col = "RW_BB" if seite in ["BB", "BB+SB"] and "RW_BB" in df else "RW_SB"
        hw_col = "HW_BB" if seite in ["BB", "BB+SB"] and "HW_BB" in df else "HW_SB"

        # Wenn gewählte Spalten nicht existieren: auf "RW_Schiff" und "HW_Schiff" zurückfallen
        if rw_col not in df or hw_col not in df:
            rw_col = "RW_Schiff"
            hw_col = "HW_Schiff"

        # Liste für Solltiefen je Punkt vorbereiten
        solltiefen = []
        
        # --- Punktweise Abfrage: liegt Punkt in einem Polygon? ---
        for idx, row in df.iterrows():
            try:
                x, y = row[rw_col], row[hw_col]
                lon, lat = transformer.transform(x, y)
                punkt = Point(lon, lat)
                matched = False
                for feld in baggerfelder:
                    if feld["polygon"].contains(punkt):
                        solltiefen.append(feld["solltiefe"])
                        matched = True
                        break
                if not matched:
                    solltiefen.append(None)
            except Exception:
                solltiefen.append(None)

        df["Solltiefe_Aktuell"] = solltiefen

        # === Fallback: Falls alle Werte leer oder 0 sind (z.B. XML fehlerhaft) ===
        mask_valide = df["Solltiefe_Aktuell"].notnull() & (df["Solltiefe_Aktuell"] != 0)
        if not mask_valide.any():
            # Alles mit Sliderwert überschreiben
            df["Solltiefe_Aktuell"] = solltiefe_slider if solltiefe_slider != 0 else None

    # === Nachbehandlung ===
    # 0-Werte als None markieren, damit sie im Plot nicht auftauchen
    df.loc[df["Solltiefe_Aktuell"] == 0, "Solltiefe_Aktuell"] = None

    # === Toleranzbereiche erzeugen ===
    if "Solltiefe_Aktuell" in df.columns:
        df["Solltiefe_Oben"] = df["Solltiefe_Aktuell"] + toleranz_oben
        df["Solltiefe_Unten"] = df["Solltiefe_Aktuell"] - toleranz_unten
        
    return df
