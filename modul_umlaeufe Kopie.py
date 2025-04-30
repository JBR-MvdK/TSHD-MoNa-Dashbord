# === Imports ============================================================================
import pandas as pd

# === Funktion: nummeriere_umlaeufe(df, startwert) ============================================================================
def nummeriere_umlaeufe(df: pd.DataFrame, startwert: int = 1) -> pd.DataFrame:
    """
    Nummeriert die Umläufe basierend auf Status-Änderungen im DataFrame.
    
    Regeln:
    - Jeder neue Status==1 (Leerfahrtstart) startet einen neuen Umlauf.
    - Alle folgenden Zeilen bekommen dieselbe Umlaufnummer, bis der nächste Status==1 auftritt.
    
    Parameter:
    - df : DataFrame der MoNa-Daten
    - startwert : Erste Nummer des Umlaufs (z.B. 1, 10, 100 je nach Projekt)

    Rückgabe:
    - DataFrame mit neuer Spalte "Umlauf"
    """

    umlauf = []           # Liste zur Speicherung der Umlaufnummern
    umlauf_nr = startwert # Startwert initialisieren
    im_umlauf = False     # Status, ob gerade innerhalb eines Umlaufs

    for status in df["Status"]:
        if str(status) == "1":
            # Start eines neuen Umlaufs
            im_umlauf = True
            umlauf.append(umlauf_nr)
            umlauf_nr += 1
        else:
            # Innerhalb eines Umlaufs oder noch nicht begonnen
            if im_umlauf:
                umlauf.append(umlauf_nr - 1)
            else:
                umlauf.append(None)

    df["Umlauf"] = umlauf
    return df


# === Funktion: extrahiere_umlauf_startzeiten(df, startwert, min_fahr_speed) ============================================================================
def extrahiere_umlauf_startzeiten(df, startwert=1, min_fahr_speed=0.3):
    """
    Extrahiert wichtige Start- und Endzeiten der Phasen innerhalb eines Umlaufs.
    
    Regeln:
    - Ein Umlauf startet nur bei Status==1 und Mindestgeschwindigkeit.
    - Baggern beginnt bei Status==2.
    - Vollfahrt beginnt bei Status==3.
    - Verbringen/Pumpen beginnt bei Status==4/5/6.
    - Ende eines Umlaufs wird gesetzt, wenn entweder der nächste Status==1 ist oder das Datenende erreicht wird.

    Parameter:
    - df : DataFrame der MoNa-Daten
    - startwert : Startwert der Umlaufzählung
    - min_fahr_speed : Mindestgeschwindigkeit in Knoten zum Starten der Leerfahrt

    Rückgabe:
    - DataFrame mit den extrahierten Zeitpunkten je Umlauf
    """

    result = []            # Liste zum Sammeln der Umlauf-Infos
    umlauf_nr = startwert  # Startnummer für Umläufe
    aktueller_umlauf = {"Umlauf": umlauf_nr}
    status_phase = 1       # 1 = Leerfahrt, 2 = Baggern, 3 = Vollfahrt, 4 = Verbringen
    index = 0              # Zeilenindex

    while index < len(df):
        row = df.iloc[index]
        status = int(row["Status"])
        geschw = float(row.get("Geschwindigkeit", 0))
        ts = row["timestamp"]

        # Phase 1: Start der Leerfahrt (nur wenn Geschwindigkeit > Mindestwert)
        if status_phase == 1 and status == 1 and geschw > min_fahr_speed:
            aktueller_umlauf = {"Umlauf": umlauf_nr, "Start Leerfahrt": ts}
            status_phase = 2

        # Phase 2: Start Baggern
        elif status_phase == 2 and status == 2:
            aktueller_umlauf["Start Baggern"] = ts
            status_phase = 3

        # Phase 3: Start Vollfahrt
        elif status_phase == 3 and status == 3:
            aktueller_umlauf["Start Vollfahrt"] = ts
            status_phase = 4

        # Phase 4: Verbringen / Pumpen / Rainbow
        elif status_phase == 4 and status in [4, 5, 6]:
            # Zeitpunkt merken, falls noch nicht gesetzt
            if "Start Verklappen/Pump/Rainbow" not in aktueller_umlauf:
                aktueller_umlauf["Start Verklappen/Pump/Rainbow"] = ts
            aktueller_umlauf["Ende"] = ts

            # Umlauf beenden, wenn nächster Status==1 ODER letztes Datenpaket erreicht
            if index + 1 == len(df) or int(df.iloc[index + 1]["Status"]) == 1:
                result.append(aktueller_umlauf)
                umlauf_nr += 1
                status_phase = 1  # Neue Leerfahrtphase

        index += 1

    return pd.DataFrame(result)


    

   
