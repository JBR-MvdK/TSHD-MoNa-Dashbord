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


# === Funktion: finde_ende_nach_ladungsabfall(...) ============================================================================
def finde_ende_nach_ladungsabfall(
    df_original,
    start_ts,
    volumen_colname="Verdraengung",
    delta_schwelle=None,
    stabil_zeit_s=20
):
    # 🧪 Arbeitskopie und vorbereitende Filter
    df = df_original.copy()
    df = df.sort_values("timestamp")                          # Zeitsortierung
    df = df[df["timestamp"] >= start_ts].copy()               # Nur Daten nach Startzeit
    df = df[df["Status"].isin([4, 5, 6])].copy()              # Nur relevante Statusbereiche

    # ⛔ Sicherheitscheck: Zu wenige Datenpunkte → Fallback
    if len(df) < 3:
        return df["timestamp"].iloc[-1], None, None, None, None, None, None, None

    # 📈 Änderungsrate der Volumenwerte berechnen
    df["vol_diff"] = df[volumen_colname].diff().fillna(0)
    df["rate"] = df["vol_diff"] / 10                          # Annahme: Messintervall = 10s

    # 📊 Basiswerte für die spätere Analyse
    vol_start = df[volumen_colname].iloc[0]                   # Anfangsvolumen
    ts_start = df["timestamp"].iloc[0]                        # Startzeit
    vol_ende = df[volumen_colname].iloc[-1]                   # Endvolumen (letzter Wert)
    ts_ende = df["timestamp"].iloc[-1]                        # Endzeit

    abfall = vol_start - vol_ende                             # Gesamtvolumenabnahme
    duration_s = (ts_ende - ts_start).total_seconds()         # Gesamtdauer in Sekunden

    # 📐 Adaptive Schwellwertberechnung, wenn nicht manuell gesetzt
    if delta_schwelle is None:
        delta_schwelle = max(0.1, abs(abfall / duration_s))   # Mindestens 0.1 m³/s

    # 🪟 Fenstergröße für Gleitprüfung (z. B. 20s = 2 Werte bei 10s Intervall)
    window = stabil_zeit_s // 10

    # 🔍 Suche nach erstem stabilen Bereich mit geringer Änderungsrate
    for i in range(window, len(df)):
        window_slice = df["rate"].iloc[i - window:i]
        if window_slice.abs().max() < delta_schwelle:
            # ✅ Zeitpunkt gefunden, an dem Volumen stabil bleibt
            return (
                df["timestamp"].iloc[i],     # stabiler Zeitpunkt
                delta_schwelle,              # verwendete Schwelle
                duration_s,                  # Gesamtdauer
                abfall,                      # gesamter Volumenabfall
                vol_start, ts_start,         # Startwert & Zeit
                vol_ende, ts_ende            # Endwert & Zeit
            )

    # ❗ Fallback: Kein stabiler Zeitpunkt gefunden → Rückgabe letzter Wert
    return (
        df["timestamp"].iloc[-1],
        delta_schwelle,
        duration_s,
        abfall,
        vol_start,
        ts_start,
        vol_ende,
        ts_ende
    )

# === Funktion: extrahiere_umlauf_startzeiten(...) ============================================================================
def extrahiere_umlauf_startzeiten(
    df,
    startwert=1,
    min_fahr_speed=0.3,
    nutze_gemischdichte=True,
    seite=None,
    dichte_grenze=1.10,
    rueckblick_minute=2,
    min_vollfahrt_dauer_min=1.0,
    validiere_verbring_start=False,
    verbring_ende_smart=True
):
    """
    Extrahiert Start- und Endzeiten je Umlauf anhand definierter Übergangslogik (Status & Sensordaten).

    Erweiterung:
    ✔ Unterstützt verschiedene Baggerseiten (BB/SB/BB+SB)
    ✔ Berücksichtigt konfigurierbare Dichtegrenze & Rückblickfenster
    ✔ Optionaler Rückfall auf Statuswechsel ohne Dichteprüfung
    """
    debug_logs = []
    result = []
    statuswechsel_kandidaten = []
    umlauf_nr = startwert
    aktueller_umlauf = {"Umlauf": umlauf_nr}
    status_phase = 1
    index = 0
    status_vorher = None
    absink_schwelle = 5.0 
    
    
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
    
    letztes_umlaufende = None
    entlade_debug_ausgegeben = False

    
    # === Phasenbasierte Statuslogik je Zeile durchlaufen ====================================================================
    while index < len(df):
        row = df.iloc[index]
        ts = row["timestamp"]
    
        # ❗️Wichtig: Nie gleiches oder früheres ts nochmal als Start akzeptieren
        if letztes_umlaufende and ts <= letztes_umlaufende:
            index += 1
            continue

    
        status = int(row["Status"])
        geschw = float(row.get("Geschwindigkeit", 0))
    
        # === Sonderfall-Korrekturen: Falsche Zwischen-Statuswerte ignorieren =====================
    
        if status_vorher == 3 and status in [4, 5, 6]:
            statuswechsel_kandidaten.append(ts)
    
        # 2 → 1 → 3 → ...  (Fehlerhafter 1er nach Baggern)
        if status_phase == 3 and status == 1 and status_vorher == 2:
            index += 1
            continue
    
        # 3 → 1 → 4/5/6 → ... (Fehlerhafter 1er vor Verbringen)
        if status_phase == 4 and status == 1 and status_vorher == 3:
            index += 1
            continue
    


        # === Phase 1: Leerfahrt erkennen ===
        if status_phase == 1:
            if letztes_umlaufende is None:
                # Nur allererster Umlauf – prüfe wie bisher auf gültigen Start
                if status == 1 and geschw > min_fahr_speed:
                    aktueller_umlauf = {"Umlauf": umlauf_nr, "Start Leerfahrt": ts}
                    status_phase = 2
            else:
                # Für Folgeumlauf: setze Start **immer exakt** auf letztes_umlaufende
                if ts >= letztes_umlaufende:
                    aktueller_umlauf = {"Umlauf": umlauf_nr, "Start Leerfahrt": letztes_umlaufende}
                    status_phase = 2
                    
                    # ✅ Logging an dieser Stelle
                    #st.write(f"🆕 Starte Umlauf {umlauf_nr} exakt bei Ende von Umlauf {umlauf_nr - 1}: {letztes_umlaufende}")

                    # Optional: Springe index direkt zum nächsten gültigen Eintrag ab Startzeit
                    index = df[df["timestamp"] >= letztes_umlaufende].index.min()


                    
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


        # === Phase 4: Verklappung / Pumpen / Rainbow ===
        elif status_phase == 4 and status in [4, 5, 6]:
        
            # 📍 Initialer Startzeitpunkt des Verbringens: letzter erkannter Statuswechsel oder aktueller Timestamp
            verbring_start_ts = statuswechsel_kandidaten[-1] if statuswechsel_kandidaten else ts
        
            # 🧷 Optionaler Marker für den Beginn des tatsächlichen Volumenabfalls (wird separat gemerkt)
            verbring_absink_start_ts = None
        
            # ▶ Gemeinsame Analyse des Volumenverlaufs ab dem erkannten Verbringstart
            df_after = df[df["timestamp"] >= verbring_start_ts].copy().reset_index(drop=True)
        
            if "Ladungsvolumen" in df_after.columns and len(df_after) > 1:
                # 📈 Volumenverlauf vorbereiten (Nullwerte auffüllen)
                volumes = df_after["Ladungsvolumen"].fillna(method="ffill")
        
                # 🎯 Ausgangswert direkt zum Statuswechsel als Referenz
                start_vol = volumes.iloc[0]
        
                # 📉 Differenz zum Startwert – negativ = Volumen sinkt
                drops = volumes - start_vol
        
                # 🔍 Suche ersten Punkt, an dem das Volumen signifikant gesunken ist
                absink_index = drops[drops < -absink_schwelle].first_valid_index()
        
                if absink_index is not None and absink_index > 0:
                    # 🕰 Zeitpunkt direkt vor dem Absinken
                    refined_ts = df_after.loc[absink_index - 1, "timestamp"]
        
                    if refined_ts >= verbring_start_ts:
                        # 📌 Speichere verlässlichen Absinkbeginn für spätere Analyse (Umlaufende)
                        verbring_absink_start_ts = refined_ts
        
                        # ✅ Falls Validierung aktiviert ist: Setze auch offiziellen Startpunkt auf diesen Zeitstempel
                        if validiere_verbring_start:
                            verbring_start_ts = refined_ts
        
            # 📝 Speichere den Verbringstart im aktuellen Umlauf
            aktueller_umlauf["Start Verklappen/Pump/Rainbow"] = verbring_start_ts



            if verbring_ende_smart:
                # ⏱ Analysebeginn: verbring_absink_start_ts wenn vorhanden, sonst fallback auf verbring_start_ts
                analyse_start_ts = verbring_absink_start_ts if verbring_absink_start_ts else verbring_start_ts
            
                # 🧭 Ermittlung der Schranke – erstes Auftreten von Status 1 nach dem Analysebeginn
                verbring_ende_schranke = df[
                    (df["timestamp"] > analyse_start_ts) & (df["Status"] == 1)
                ]["timestamp"].min()
            
                # 📉 Eingrenzung auf Verbring-Zeitraum (Status 4/5/6)
                if pd.notnull(verbring_ende_schranke):
                    df_verbringen = df[
                        (df["timestamp"] >= analyse_start_ts) &
                        (df["timestamp"] < verbring_ende_schranke) &
                        (df["Status"].isin([4, 5, 6]))
                    ].copy()
                else:
                    df_verbringen = df[
                        (df["timestamp"] >= analyse_start_ts) &
                        (df["Status"].isin([4, 5, 6]))
                    ].copy()
            
                if not df_verbringen.empty:
                    # 🔁 Differenz und gleitender Mittelwert berechnen zur Glättung kleiner Schwankungen
                    df_verbringen["vol_diff"] = df_verbringen["Verdraengung"].diff().fillna(0)
                    window_size = 5
                    df_verbringen["vol_diff_mean"] = df_verbringen["vol_diff"].rolling(window_size, center=True).mean()
            
                    # 📍 Finde erstes signif. Absinken nach geglättetem Wert
                    absink_index = df_verbringen[df_verbringen["vol_diff_mean"] < -absink_schwelle].first_valid_index()
            
                    if absink_index is not None:
                        start_abfall_ts = df_verbringen.loc[absink_index, "timestamp"]
            
                        # 📐 Berechne stabilen Endpunkt ab dem erkannten Absinken
                        umlauf_ende_ts, _, _, _, _, _, _, _ = finde_ende_nach_ladungsabfall(
                            df_verbringen,
                            start_ts=start_abfall_ts,
                            volumen_colname="Verdraengung",
                            delta_schwelle=None,
                            stabil_zeit_s=40
                        )
            
                        # 🛑 Begrenze auf Schranke, falls vorhanden
                        if pd.notnull(verbring_ende_schranke) and umlauf_ende_ts > verbring_ende_schranke:
                            umlauf_ende_ts = verbring_ende_schranke
                    else:
                        umlauf_ende_ts = ts  # Fallback, kein Absinken erkannt
                else:
                    umlauf_ende_ts = ts  # Fallback, keine Verbringdaten
            else:
                umlauf_ende_ts = ts  # Kein Smart-Ende aktiviert
            
            # ⏺ Speichere Endzeitpunkt
            aktueller_umlauf["Ende"] = umlauf_ende_ts

            # Abschluss
            if index + 1 == len(df) or int(df.iloc[index + 1]["Status"]) == 1:
                result.append(aktueller_umlauf)
                umlauf_nr += 1
                status_phase = 1
                statuswechsel_kandidaten = []
                letztes_umlaufende = aktueller_umlauf.get("Ende", ts)
                entlade_debug_ausgegeben = False 

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




# === Funktion: mappe_umlaufnummer(...) ============================================================================
def mappe_umlaufnummer(df: pd.DataFrame, umlauf_info_df: pd.DataFrame) -> pd.DataFrame:
    """
    Ergänzt das DataFrame `df` um eine neue Spalte 'Umlauf_korrekt', 
    die für jeden Datenpunkt die zugehörige Umlaufnummer aus `umlauf_info_df` einträgt.

    Die Zuordnung basiert auf dem Zeitfenster 'Start Leerfahrt' bis 'Ende' je Umlauf.

    Parameter:
    ----------
    df : pd.DataFrame
        Der Haupt-Datensatz mit Zeitstempeln (Spalte: 'timestamp')

    umlauf_info_df : pd.DataFrame
        DataFrame mit den Zeitfenstern pro Umlauf (Spalten: 'Start Leerfahrt', 'Ende', 'Umlauf')

    Rückgabe:
    --------
    pd.DataFrame
        Das ursprüngliche df mit einer zusätzlichen Spalte 'Umlauf_korrekt'
    """

    # === Validierungsprüfungen (für sauberes Debugging) ===
    if "timestamp" not in df.columns:
        raise ValueError("❌ Spalte 'timestamp' fehlt im DataFrame `df`.")
    
    required_cols = {"Start Leerfahrt", "Ende", "Umlauf"}
    if not required_cols.issubset(umlauf_info_df.columns):
        raise ValueError("❌ `umlauf_info_df` muss die Spalten 'Start Leerfahrt', 'Ende' und 'Umlauf' enthalten.")

    # === Initialisiere Zielspalte ===
    df["Umlauf_korrekt"] = None

    # === Zeilenweise Durchlauf: für jeden Umlauf ein Zeitfenster festlegen ===
    for _, row in umlauf_info_df.iterrows():
        try:
            # Setze Zeitfenster mit expliziter Zeitzone (UTC)
            start = pd.to_datetime(row["Start Leerfahrt"], utc=True)
            ende = pd.to_datetime(row["Ende"], utc=True)
            nummer = row["Umlauf"]

            # Filtermaske: Alle Zeitstempel im Zeitfenster
            mask = (df["timestamp"] >= start) & (df["timestamp"] <= ende)
            df.loc[mask, "Umlauf_korrekt"] = nummer

        except Exception as e:
            print(f"⚠️ Fehler beim Verarbeiten von Umlauf {row.get('Umlauf', '?')}: {e}")

    return df


