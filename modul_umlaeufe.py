# === Imports ============================================================================
import pandas as pd
import streamlit as st
from modul_baggerseite import erkenne_baggerseite  # ⚓ Automatische Erkennung der aktiven Baggerseite


# === Funktion: nummeriere_umlaeufe(df, startwert) ============================================================================
def nummeriere_umlaeufe(df: pd.DataFrame, startwert: int = 1) -> pd.DataFrame:
    """
    Robuste Umlaufnummerierung basierend auf Statuswechseln – auch ohne Status==1.

    Ein neuer Umlauf beginnt bei:
    - Status==1 (Standardbedingung)
    - ODER nach einem Übergang von Status 4/5/6 zu einem anderen Status
    - ODER: wenn kein Status==1 existiert, wird der gesamte Datensatz einem Umlauf zugeordnet
    """

    umlauf = []
    umlauf_nr = startwert
    im_umlauf = False

    status_liste = df["Status"].tolist()
    status_vorher = None

    for i, status in enumerate(status_liste):
        if str(status) == "1" or (status_vorher in [4, 5, 6] and str(status) != str(status_vorher)):
            im_umlauf = True
            umlauf.append(umlauf_nr)
            umlauf_nr += 1
        else:
            if im_umlauf:
                umlauf.append(umlauf_nr - 1)
            else:
                umlauf.append(None)
        status_vorher = status

    # Fallback: Kein Status==1 → alles einem Umlauf zuordnen
    if all(x is None for x in umlauf):
        umlauf = [startwert] * len(df)

    df["Umlauf"] = umlauf
    return df




# === Funktion: extrahiere_umlauf_startzeiten(...) ============================================================================
def extrahiere_umlauf_startzeiten(
    df,
    startwert=1,
    min_fahr_speed=0.3,
    nutze_gemischdichte=True,
    seite=None,
    dichte_grenze=1.01,
    rueckblick_minute=2
):
    """
    Extrahiert Start- und Endzeiten je Umlauf anhand definierter Übergangslogik (Status & Sensordaten).

    Erweiterung:
    ✔ Unterstützt verschiedene Baggerseiten (BB/SB/BB+SB)
    ✔ Berücksichtigt konfigurierbare Dichtegrenze & Rückblickfenster
    ✔ Optionaler Rückfall auf Statuswechsel ohne Dichteprüfung
    """

    result = []
    umlauf_nr = startwert
    aktueller_umlauf = {"Umlauf": umlauf_nr}
    status_phase = 1
    index = 0
    status_vorher = None

    # 🧭 Aktive Baggerseite bestimmen (manuell oder automatisch erkannt)
    if not seite:
        seite = erkenne_baggerseite(df)

    nutze_bb = seite in ["BB", "BB+SB"]
    nutze_sb = seite in ["SB", "BB+SB"]

    # 🔍 Prüfe, ob Dichtewerte vorhanden und brauchbar sind – sonst Fallback auf reine Statuslogik
    bb_dichte_gueltig = (
        nutze_bb and "Gemischdichte_BB" in df.columns and
        df["Gemischdichte_BB"].dropna().gt(0).sum() > 5
    )
    sb_dichte_gueltig = (
        nutze_sb and "Gemischdichte_SB" in df.columns and
        df["Gemischdichte_SB"].dropna().gt(0).sum() > 5
    )

    if nutze_gemischdichte and not (bb_dichte_gueltig or sb_dichte_gueltig):
        st.warning("⚠️ Dichteprüfung aktiv, aber keine brauchbaren Messwerte gefunden – Fallback auf Statuswechsel.")
        nutze_gemischdichte = False

    # === Phasenbasierte Statuslogik je Zeile durchlaufen ====================================================================
    while index < len(df):
        row = df.iloc[index]
        status = int(row["Status"])
        geschw = float(row.get("Geschwindigkeit", 0))
        ts = row["timestamp"]

        # Phase 1: Leerfahrt erkennen (Startbedingung: Status==1 + Mindestfahrt)
        if status_phase == 1 and status == 1 and geschw > min_fahr_speed:
            aktueller_umlauf = {"Umlauf": umlauf_nr, "Start Leerfahrt": ts}
            status_phase = 2

        # Phase 2: Baggerbeginn erkennen (optional abhängig von Dichte)
        elif status_phase == 2 and status == 2:
            dichte_bb = pd.to_numeric(row.get("Gemischdichte_BB", None), errors="coerce")
            dichte_sb = pd.to_numeric(row.get("Gemischdichte_SB", None), errors="coerce")

            if nutze_gemischdichte:
                dichte_verfuegbar = (
                    (nutze_bb and pd.notnull(dichte_bb) and dichte_bb > 1.0) or
                    (nutze_sb and pd.notnull(dichte_sb) and dichte_sb > 1.0)
                )
                if dichte_verfuegbar:
                    # 👉 Einen Schritt zurück, falls möglich
                    if index > 0:
                        ts_vorher = df.iloc[index - 1]["timestamp"]
                        aktueller_umlauf["Start Baggern"] = ts_vorher
                    else:
                        aktueller_umlauf["Start Baggern"] = ts  # Fallback
                    status_phase = 3

            else:
                aktueller_umlauf["Start Baggern"] = ts
                status_phase = 3

        # Phase 3: Start Vollfahrt – Rückblick von Status 3 in die letzten Minuten von Status 2
        elif status_phase == 3 and status_vorher == 2 and status == 3:
            ts_grenze = ts - pd.Timedelta(minutes=rueckblick_minute)
            best_ts = None
            last_valid_found = False

            for j in range(index - 1, -1, -1):
                row_prev = df.iloc[j]
                ts_prev = row_prev["timestamp"]
                if ts_prev < ts_grenze:
                    break
                if int(row_prev["Status"]) != 2:
                    continue

                dichte_bb = pd.to_numeric(row_prev.get("Gemischdichte_BB", None), errors="coerce")
                dichte_sb = pd.to_numeric(row_prev.get("Gemischdichte_SB", None), errors="coerce")

                if nutze_gemischdichte:
                    gilt_bb = nutze_bb and pd.notnull(dichte_bb) and dichte_bb < dichte_grenze
                    gilt_sb = nutze_sb and pd.notnull(dichte_sb) and dichte_sb < dichte_grenze

                    if gilt_bb or gilt_sb:
                        best_ts = ts_prev
                        last_valid_found = True
                    elif last_valid_found:
                        break
                else:
                    best_ts = ts_prev
                    break

            aktueller_umlauf["Start Vollfahrt"] = best_ts if best_ts else ts
            status_phase = 4

        # Phase 4: Verklappung / Pumpen / Rainbow (Ende eines Umlaufs)
        elif status_phase == 4 and status in [4, 5, 6]:
            if "Start Verklappen/Pump/Rainbow" not in aktueller_umlauf:
                aktueller_umlauf["Start Verklappen/Pump/Rainbow"] = ts
            aktueller_umlauf["Ende"] = ts

            if index + 1 == len(df) or int(df.iloc[index + 1]["Status"]) == 1:
                result.append(aktueller_umlauf)
                umlauf_nr += 1
                status_phase = 1

        status_vorher = status
        index += 1

    return pd.DataFrame(result)



# === Funktion: berechne_status_neu(...) ============================================================================
def berechne_status_neu(df, umlauf_df):
    """
    Ergänzt df um eine neue Spalte 'Status_neu', die auf Basis der Zeitmarken aus den Umläufen echte Betriebsphasen markiert.

    Mögliche Werte:
    - 'Leerfahrt'
    - 'Baggern'
    - 'Vollfahrt'
    - 'Verbringen'
    - 'Unbekannt' (Default für Lücken oder unzugeordnete Phasen)
    """

    df["Status_neu"] = "Unbekannt"

    for _, row in umlauf_df.iterrows():
        beg = row.get("Start Leerfahrt")
        bag = row.get("Start Baggern")
        voll = row.get("Start Vollfahrt")
        verkl = row.get("Start Verklappen/Pump/Rainbow")
        ende = row.get("Ende")

        if pd.notnull(beg) and pd.notnull(bag):
            df.loc[(df["timestamp"] >= beg) & (df["timestamp"] < bag), "Status_neu"] = "Leerfahrt"
        if pd.notnull(bag) and pd.notnull(voll):
            df.loc[(df["timestamp"] >= bag) & (df["timestamp"] < voll), "Status_neu"] = "Baggern"
        if pd.notnull(voll) and pd.notnull(verkl):
            df.loc[(df["timestamp"] >= voll) & (df["timestamp"] < verkl), "Status_neu"] = "Vollfahrt"
        if pd.notnull(verkl) and pd.notnull(ende):
            df.loc[(df["timestamp"] >= verkl) & (df["timestamp"] <= ende), "Status_neu"] = "Verbringen"

    return df


    

   
