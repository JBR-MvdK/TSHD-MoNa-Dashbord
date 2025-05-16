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
    dichte_grenze=1.10,
    rueckblick_minute=2,
    min_vollfahrt_dauer_min=1.0
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
                    (nutze_bb and pd.notnull(dichte_bb) and dichte_bb > dichte_grenze) or
                    (nutze_sb and pd.notnull(dichte_sb) and dichte_sb > dichte_grenze)
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
            # 🧪 Prüfe, ob die folgende Vollfahrtphase lang genug anhält
            ts_vollfahrt_start_kandidat = row["timestamp"]
            ts_vollfahrt_grenze = ts_vollfahrt_start_kandidat + pd.Timedelta(minutes=min_vollfahrt_dauer_min)
        
            gueltig = False
            for k in range(index + 1, len(df)):
                ts_k = df.iloc[k]["timestamp"]
                status_k = int(df.iloc[k]["Status"])
                if ts_k >= ts_vollfahrt_grenze:
                    if status_k == 3:
                        gueltig = True
                    break
                if status_k != 3:
                    break  # zu früh wieder unterbrochen → keine echte Vollfahrt
        
            if not gueltig:
                index += 1
                continue  # ➡️ Sonderfall: ignoriere diesen Übergang und mach weiter
        
            # ✅ Gültige Vollfahrtphase → Rückblick zur Dichteprüfung
            ts_grenze = ts - pd.Timedelta(minutes=rueckblick_minute)
            gueltiger_dichte_ts = None
        
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
                    bb_ok = nutze_bb and pd.notnull(dichte_bb) and dichte_bb <= dichte_grenze
                    sb_ok = nutze_sb and pd.notnull(dichte_sb) and dichte_sb <= dichte_grenze
        
                    if bb_ok or sb_ok:
                        gueltiger_dichte_ts = ts_prev
                else:
                    gueltiger_dichte_ts = ts_prev
                    break
        
            # ⏩ Einen Datenpunkt nach dem gültigen nehmen (wenn möglich)
            start_vollfahrt_ts = ts
            if gueltiger_dichte_ts:
                df_after = df[df["timestamp"] > gueltiger_dichte_ts]
                next_row = df_after.iloc[0] if not df_after.empty else None
                if next_row is not None:
                    start_vollfahrt_ts = next_row["timestamp"]
                else:
                    start_vollfahrt_ts = gueltiger_dichte_ts  # Fallback
        
            aktueller_umlauf["Start Vollfahrt"] = start_vollfahrt_ts
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


    

   
