import pandas as pd
from shapely.geometry import Polygon
from pyproj import Transformer

def parse_dichte_polygone(txt_file, referenz_data=None, epsg_code=None):
    """
    Liest Dichtepolygone aus einer ASCII-Datei mit Tab-getrennten Werten
    und wandelt sie optional ins WGS84-Koordinatensystem um.
    Unterstützt optional eine siebte Spalte: maxdichte
    """

    # ------------------------------------------------------------
    # 📄 Datei einlesen – auch wenn nur 6 Spalten vorhanden sind
    # ------------------------------------------------------------
    df = pd.read_csv(
        txt_file, sep="\t", header=None, engine="python"
    )

    # 🔤 Spaltennamen je nach tatsächlicher Anzahl in der Datei zuweisen
    spalten_namen = ["name", "rw", "hw", "ortsdichte", "ortspezifisch", "mindichte", "maxdichte"]
    df.columns = spalten_namen[:df.shape[1]]

    # 🧹 Nur Zeilen mit gültigen Koordinaten und Dichtewerten weiterverarbeiten
    df = df.dropna(subset=["rw", "hw", "ortsdichte"])

    # 📁 Falls keine Referenzdaten übergeben: leeres Dict verwenden
    if referenz_data is None:
        referenz_data = {}

    # 🌍 Koordinatentransformation vorbereiten (lokal → WGS84), falls EPSG angegeben
    transformer = Transformer.from_crs(epsg_code, "EPSG:4326", always_xy=True) if epsg_code else None

    result = []  # Liste für zurückzugebende Polygondaten

    # 🔁 Gruppiere nach Polygon-Namen
    for name, gruppe in df.groupby("name"):
        punkte = list(zip(gruppe["rw"], gruppe["hw"]))  # Alle Eckpunkte für das Polygon

        # ❌ Ein Polygon braucht mindestens 3 Punkte
        if len(punkte) < 3:
            continue

        # 🔄 Falls gewünscht, Koordinaten in WGS84 umrechnen
        if transformer:
            punkte = [transformer.transform(x, y) for x, y in punkte]

        # 🧱 Polygonobjekt erzeugen
        polygon = Polygon(punkte)
        erste = gruppe.iloc[0]  # Referenzzeile für weitere Werte

        # 📊 Dichtewerte aus der Datei (erste Zeile der Gruppe)
        ortsdichte = round(float(erste["ortsdichte"]), 2)
        ortsspez = float(erste.get("ortspezifisch", 0))
        mindichte = float(erste.get("mindichte", 0))
        maxdichte = float(erste["maxdichte"]) if "maxdichte" in erste and pd.notna(erste["maxdichte"]) else None

        # 🧠 Fallback: Werte aus Referenzdaten ergänzen, falls in Datei 0 steht
        if ortsspez == 0 or mindichte == 0:
            # Zugriff direkt oder verschachtelt (z. B. nach Profilnamen wie "HPA")
            lookup = referenz_data.get(str(ortsdichte)) or \
                     referenz_data.get("HPA", {}).get(str(ortsdichte))

            # 📘 Wenn Lookup ein Dict ist (z. B. {"ortspezifisch": x, "mindichte": y})
            if isinstance(lookup, dict):
                ortsspez = lookup.get("ortspezifisch", ortsspez)
                mindichte = lookup.get("mindichte", mindichte)
                if "maxdichte" in lookup:
                    maxdichte = lookup.get("maxdichte", maxdichte)

            # 📘 Wenn Lookup ein Tupel/Liste ist (z. B. [x, y, z])
            elif isinstance(lookup, (list, tuple)):
                if len(lookup) >= 2:
                    ortsspez, mindichte = lookup[:2]
                if len(lookup) >= 3:
                    maxdichte = lookup[2]

        # 📦 Zusammenstellen des Ergebnisobjekts für dieses Polygon
        result.append({
            "name": name.strip(),
            "polygon": polygon,
            "ortsdichte": ortsdichte,
            "ortspezifisch": ortsspez,
            "mindichte": mindichte,
            "maxdichte": maxdichte  # ← optional, wenn vorhanden
        })

    # ✅ Rückgabe der Polygonliste mit allen zugewiesenen Dichtewerten
    return result






