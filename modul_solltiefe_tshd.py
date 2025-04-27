#=========================================================================================

# modul_solltiefe_tshd.py

from shapely.geometry import Point
from pyproj import Transformer

def berechne_solltiefe_fuer_df(
    df, baggerfelder, seite, epsg_code, toleranz_oben=1.0, toleranz_unten=0.5, solltiefe_slider=0.0
):

    if not baggerfelder or "RW_Schiff" not in df or "HW_Schiff" not in df:
        # KEINE XML vorhanden – alle Werte auf Solltiefe-Slider setzen (außer ggf. None)
        df["Solltiefe_Aktuell"] = solltiefe_slider if solltiefe_slider != 0 else None
    else:
        # Koordinaten im WGS84 berechnen (wie im Map-Plot!)
        transformer = Transformer.from_crs(epsg_code, "EPSG:4326", always_xy=True)
        
        # Seite wählen: BB, SB, BB+SB (hier einfach: zuerst BB, dann SB – wie bei Map)
        rw_col = "RW_BB" if seite in ["BB", "BB+SB"] and "RW_BB" in df else "RW_SB"
        hw_col = "HW_BB" if seite in ["BB", "BB+SB"] and "HW_BB" in df else "HW_SB"

        # Wenn Spalten nicht vorhanden: auf RW_Schiff/HW_Schiff zurückfallen
        if rw_col not in df or hw_col not in df:
            rw_col = "RW_Schiff"
            hw_col = "HW_Schiff"

        solltiefen = []
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

        # Prüfen, ob IRGENDEIN gültiger Wert ungleich 0 existiert
        mask_valide = df["Solltiefe_Aktuell"].notnull() & (df["Solltiefe_Aktuell"] != 0)
        if not mask_valide.any():
            # Keine gültigen Werte in der XML: Spalte komplett mit Sliderwert füllen (außer wenn auch Slider 0)
            df["Solltiefe_Aktuell"] = solltiefe_slider if solltiefe_slider != 0 else None

    # Überall, wo Solltiefe_Aktuell == 0 ist, auf None setzen (damit sie im Diagramm nicht erscheinen)
    df.loc[df["Solltiefe_Aktuell"] == 0, "Solltiefe_Aktuell"] = None

    # Toleranzbereich berechnen, nur wo gültig
    if "Solltiefe_Aktuell" in df.columns:
        df["Solltiefe_Oben"] = df["Solltiefe_Aktuell"] + toleranz_oben
        df["Solltiefe_Unten"] = df["Solltiefe_Aktuell"] - toleranz_unten
        
    return df
