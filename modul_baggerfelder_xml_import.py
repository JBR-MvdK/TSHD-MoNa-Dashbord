# === Imports ============================================================================
import xml.etree.ElementTree as ET  # Modul zum Parsen von XML-Dateien
from shapely.geometry import Polygon  # Modul zum Erstellen von Polygon-Objekten
from pyproj import Transformer  # Modul für Koordinatentransformationen

# === Funktion: parse_baggerfelder(xml_path, epsg_code_from_mona) ============================================================================
def parse_baggerfelder(xml_path, epsg_code_from_mona):
    """
    Liest Baggerfelder aus einer LandXML-Datei ein und wandelt sie von lokalen Koordinaten ins WGS84-Koordinatensystem um.

    Parameter:
    - xml_path : Pfad oder Dateiobjekt der hochgeladenen XML-Datei
    - epsg_code_from_mona : EPSG-Code der MoNa-Daten, z.B. 'EPSG:25832' (z.B. UTM Zone 32N)

    Rückgabe:
    - Liste von Dictionaries, jedes mit:
        - 'name'      → Name des Baggerfeldes (aus XML)
        - 'polygon'   → Polygon-Objekt (shapely.geometry.Polygon)
        - 'solltiefe' → Mittlere Solltiefe des Feldes (berechnet aus den Koordinaten)

    """

    # Transformer von MoNa-Koordinatensystem zu WGS84 aufbauen
    transformer = Transformer.from_crs(epsg_code_from_mona, "EPSG:4326", always_xy=True)

    # XML-Namespace definieren (LandXML-Standard)
    ns = {'ns': 'http://www.landxml.org/schema/LandXML-1.2'}
    
    # XML-Datei einlesen und Wurzel-Element bestimmen
    tree = ET.parse(xml_path)
    root = tree.getroot()

    polygons = []  # Ergebnisliste

    # Schleife über alle PlanFeatures (ein PlanFeature entspricht einem Baggerfeld)
    for plan_feature in root.findall(".//ns:PlanFeature", ns):
        name = plan_feature.attrib.get("name", "Unbenannt")  # Name des Baggerfeldes
        coord_geom = plan_feature.find("ns:CoordGeom", ns)   # Geometrie des Feldes
        if coord_geom is None:
            continue  # Falls keine Geometrie vorhanden, überspringen

        points = []  # Liste der Eckpunkte
        tiefen = []  # Liste der Tiefenwerte

        # Schleife über alle Liniensegmente
        for line in coord_geom.findall("ns:Line", ns):
            start = line.find("ns:Start", ns)
            end = line.find("ns:End", ns)
            if start is not None and end is not None:
                start_vals = list(map(float, start.text.strip().split()))
                end_vals = list(map(float, end.text.strip().split()))

                # Startpunkt verarbeiten: HW = Y, RW = X
                hw_raw = start_vals[0]
                rw_raw = start_vals[1]

                # Normalisierung: Falls UTM-Koordinate mit Zonenkennung (>30 Mio)
                if epsg_code_from_mona.startswith("EPSG:258") and rw_raw > 30_000_000:
                    rw_raw -= int(epsg_code_from_mona[-2:]) * 1_000_000

                points.append((rw_raw, hw_raw))  # (RW, HW) speichern
                tiefen.append(start_vals[2])     # Tiefe extrahieren

        # Polygon schließen, falls Startpunkt ≠ Endpunkt
        if points and points[0] != points[-1]:
            points.append(points[0])

        # Transformation der Punkte ins WGS84-System
        transformed = [transformer.transform(x, y) for x, y in points]

        # Mittlere Solltiefe berechnen
        solltiefe = round(sum(tiefen) / len(tiefen), 2) if tiefen else None

        # Polygon und Metadaten speichern
        polygons.append({
            "name": name,
            "polygon": Polygon(transformed),
            "solltiefe": solltiefe
        })

    return polygons
