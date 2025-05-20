from shapely.geometry import Point
from pyproj import Transformer
import pandas as pd

def weise_dichtepolygonwerte_zu(df, dichte_polygone, epsg_code, rw_col="RW_Schiff", hw_col="HW_Schiff"):
    """
    Weist Dichtewerte zu, wenn RW/HW innerhalb eines Polygons liegen – nur bei Status_neu == "Baggern".
    Achtung: Dichtepolygone sind in WGS84, daher werden Punkte transformiert.
    """

    # 📋 Arbeitskopie erstellen, um Originaldaten nicht zu verändern
    df = df.copy()

    # 🆕 Zielspalten vorbereiten, in die ggf. Dichteinformationen geschrieben werden
    df["Dichte_Polygon_Name"] = None         # Name des getroffenen Dichtepolygons
    df["Ortsdichte"] = None                  # Referenzdichte des Polygons
    df["Ortsspezifisch"] = None              # ortsspezifischer tTDS/m³-Wert
    df["Mindichte"] = None                   # untere Schwelle für Bonusregelung

    # 🌐 Transformer definieren: Von Projektionssystem (z. B. UTM) in WGS84
    transformer = Transformer.from_crs(epsg_code, "EPSG:4326", always_xy=True)

    # 🔁 Alle Zeilen des DataFrames durchgehen
    for idx, row in df.iterrows():

        # 🚫 Nur berücksichtigen, wenn die Zeile zur Baggerphase gehört
        if row.get("Status_neu") != "Baggern":
            continue

        # 🗺️ Koordinaten abgreifen (Rechtswert / Hochwert)
        rw, hw = row.get(rw_col), row.get(hw_col)

        # ❗ Wenn Koordinaten fehlen, diesen Datensatz überspringen
        if pd.isna(rw) or pd.isna(hw):
            continue

        # 🔄 Umrechnung RW/HW → geografische Koordinaten (Longitude/Latitude)
        lon, lat = transformer.transform(rw, hw)
        punkt = Point(lon, lat)

        # 📦 Durch alle Dichtepolygone iterieren und auf Punktprüfung testen
        for polygon in dichte_polygone:
            if polygon["polygon"].contains(punkt):
                # ✅ Treffer: Dichtewerte aus Polygon in Zeile eintragen
                df.at[idx, "Dichte_Polygon_Name"] = polygon["name"]
                df.at[idx, "Ortsdichte"] = polygon["ortsdichte"]
                df.at[idx, "Ortsspezifisch"] = polygon["ortspezifisch"]
                df.at[idx, "Mindichte"] = polygon["mindichte"]
                break  # ⛔ Stop: erstes zutreffendes Polygon reicht

    # ✅ Rückgabe: neuer DataFrame mit zugewiesenen Dichtewerten
    return df

