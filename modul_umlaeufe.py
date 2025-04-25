import pandas as pd

def nummeriere_umlaeufe(df: pd.DataFrame, startwert: int = 1) -> pd.DataFrame:
    umlauf = []
    umlauf_nr = startwert
    im_umlauf = False

    for status in df["Status"]:
        if str(status) == "1":
            im_umlauf = True
            umlauf.append(umlauf_nr)
            umlauf_nr += 1
        else:
            if im_umlauf:
                umlauf.append(umlauf_nr - 1)
            else:
                umlauf.append(None)

    df["Umlauf"] = umlauf
    return df

def extrahiere_umlauf_startzeiten(df, startwert=1, min_fahr_speed=0.3):
    result = []
    umlauf_nr = startwert
    aktueller_umlauf = {"Umlauf": umlauf_nr}
    status_phase = 1
    index = 0

    while index < len(df):
        row = df.iloc[index]
        status = int(row["Status"])
        geschw = float(row.get("Geschwindigkeit", 0))
        ts = row["timestamp"]

        # Nur Umlaufstart, wenn gefahren wird!
        if status_phase == 1 and status == 1 and geschw > min_fahr_speed:
            aktueller_umlauf = {"Umlauf": umlauf_nr, "Start Leerfahrt": ts}
            status_phase = 2

        elif status_phase == 2 and status == 2:
            aktueller_umlauf["Start Baggern"] = ts
            status_phase = 3

        elif status_phase == 3 and status == 3:
            aktueller_umlauf["Start Vollfahrt"] = ts
            status_phase = 4

        elif status_phase == 4 and status in [4, 5, 6]:
            if "Start Verklappen/Pump/Rainbow" not in aktueller_umlauf:
                aktueller_umlauf["Start Verklappen/Pump/Rainbow"] = ts
            aktueller_umlauf["Ende"] = ts
            # Umlauf abschließen nur, wenn nächster Status==1 ODER Ende erreicht
            if index + 1 == len(df) or int(df.iloc[index + 1]["Status"]) == 1:
                result.append(aktueller_umlauf)
                umlauf_nr += 1
                status_phase = 1

        index += 1
    return pd.DataFrame(result)

    

   
