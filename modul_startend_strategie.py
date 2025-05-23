# ======================================================================================================================
# 📦 modul_startend_strategie.py – Ermittlung von Start- und Endwerten gemäß Strategie
# ======================================================================================================================

import pandas as pd
import streamlit as st
# ----------------------------------------------------------------------------------------------------------------------
# 🔧 Hilfsfunktionen
# ----------------------------------------------------------------------------------------------------------------------

# 🔄 Mapping: Status_neu → numerischer Status
STATUS_NEU_MAPPING = {
    "Leerfahrt": 1,
    "Baggern": 2,
    "Vollfahrt": 3,
    "Verbringen": 4,  # optional: auch 5/6 ergänzbar, je nach System
}

def ersetze_status_neu(df):
    """
    Ersetzt die Spalte 'Status_neu' durch numerische Werte gemäß Mapping.
    Bewahrt Originalspalte 'Status' in 'Status_alt'.
    """
    if "Status_neu" in df.columns:
        df = df.copy()
        df["Status_alt"] = df["Status"]
        df["Status"] = df["Status_neu"].map(STATUS_NEU_MAPPING).fillna(df["Status"])
    return df

def first_or_none(series):
    """Gibt den ersten Wert einer Series zurück oder None, wenn leer."""
    return series.iloc[0] if not series.empty else None

def first_index_or_none(series):
    """Gibt den Index des ersten Werts zurück oder None, wenn leer."""
    return series.index[0] if not series.empty else None

def get_statuswechselzeit(df, von, nach, zeit_col="timestamp"):
    """
    Sucht den Zeitpunkt eines direkten Statuswechsels von `von` nach `nach`.
    """
    mask = (df["Status"].shift(1) == von) & (df["Status"] == nach)
    wechsler = df[mask]
    return wechsler[zeit_col].iloc[0] if not wechsler.empty else None

def get_letzten_statuswechsel(df, von, nach, zeit_col="timestamp", ignorierte_status=None):
    """
    Sucht den letzten Statuswechsel von `von` zu `nach`, auch über ignorierte Zwischenstatus hinweg.
    """
    if ignorierte_status is None:
        ignorierte_status = []

    df = df[[zeit_col, "Status"]].copy()
    df["prev"] = df["Status"].shift(1)

    last_ts = None
    i = 1
    while i < len(df):
        s_prev = df.iloc[i - 1]["Status"]
        s_curr = df.iloc[i]["Status"]

        if s_prev == von and s_curr == nach:
            last_ts = df.iloc[i][zeit_col]
            i += 1
        elif s_prev == von and s_curr in ignorierte_status:
            for j in range(i + 1, len(df)):
                if df.iloc[j]["Status"] == nach:
                    last_ts = df.iloc[j][zeit_col]
                    i = j
                    break
                if df.iloc[j]["Status"] not in ignorierte_status:
                    break
        i += 1

    return last_ts

def suche_extrem_zweizeitfenster(df, zeitpunkt, vor, nach, col, art="max", zeit_col="timestamp"):
    """
    Sucht min/max-Wert innerhalb eines Zeitfensters (z. B. 5min vor bis 2min nach einem Referenzzeitpunkt).
    """
    t_start = zeitpunkt - pd.Timedelta(vor)
    t_ende = zeitpunkt + pd.Timedelta(nach)
    df_zeit = df[(df[zeit_col] >= t_start) & (df[zeit_col] <= t_ende)]
    if df_zeit.empty or col not in df_zeit.columns:
        return None, None
    val = df_zeit[col].max() if art == "max" else df_zeit[col].min()
    ts = df_zeit[df_zeit[col] == val][zeit_col].iloc[0] if not df_zeit[df_zeit[col] == val].empty else None
    return val, ts


# ----------------------------------------------------------------------------------------------------------------------
# 🔍 Hauptfunktion: berechne_start_endwerte
# ----------------------------------------------------------------------------------------------------------------------

def berechne_start_endwerte(df, strategie=None, zeit_col="timestamp", df_gesamt=None):
    """
    Wendet eine Strategie zur Bestimmung von Start- und Endwerten (Verdrängung, Volumen) an.
    Gibt zusätzlich Debug-Infos zurück.
    """
 

    df = ersetze_status_neu(df)
    if df_gesamt is not None:
        df_gesamt = ersetze_status_neu(df_gesamt)



    debug_info = []
    result = {}

    # Strategien extrahieren
    strat_v = strategie.get("Verdraengung", {}) if strategie else {}
    strat_l = strategie.get("Ladungsvolumen", {}) if strategie else {}

    # Referenz-DataFrame festlegen (z. B. Gesamtdaten)
    df_ref = df_gesamt if df_gesamt is not None else df

    # --- Statuswechsel-Zeitpunkte suchen ---
    statuszeit_1_2 = get_statuswechselzeit(df_ref, 1, 2, zeit_col)
    statuszeit_2_3 = get_letzten_statuswechsel(df_ref, 2, 3, zeit_col, ignorierte_status=[1])
    statuszeit_456_1 = get_statuswechselzeit(df_ref, 456, 1, zeit_col)

    if statuszeit_456_1 is None and not df.empty and df.iloc[0]["Status"] == 1:
        statuszeit_456_1 = df.iloc[0][zeit_col]
        debug_info.append("⚠️ Kein 456→1 gefunden – erster Eintrag mit Status 1 als Fallback verwendet.")

    debug_info.append(f"📍 Statuszeit 1→2: {statuszeit_1_2}")
    debug_info.append(f"📍 Statuszeit 2→3: {statuszeit_2_3}")
    debug_info.append(f"📍 Statuszeit 456→1: {statuszeit_456_1}")

    # ------------------------------------------------------------------------------------------------------------------
    # 🔧 Subfunktionen innerhalb der Hauptfunktion
    # ------------------------------------------------------------------------------------------------------------------

    def standardwert(df, ts, col, label):
        """Gibt Wert exakt am Statuszeitpunkt zurück (Fallback)."""
        sub = df[df[zeit_col] == ts] if ts else pd.DataFrame()
        val = first_or_none(sub[col]) if col in sub.columns else None
        ts_out = first_index_or_none(sub[col])
        ts_out = sub.loc[ts_out, zeit_col] if ts_out in sub.index else None
        debug_info.append(f"⚠️ {label}: Standardwert (exakter Statuszeitpunkt)")
        return val, ts_out

    def strategie_extremwert(df, art, ts_ref, vor, nach, col, zeit_col, debug_info, label):
        """Sucht Min/Max-Wert im definierten Zeitbereich um einen Referenzzeitpunkt."""
        if ts_ref is None:
            debug_info.append(f"⚠️ {label}: Kein Statuszeitpunkt – Strategie nicht anwendbar.")
            return None, None
        wert, ts = suche_extrem_zweizeitfenster(df, ts_ref, vor, nach, col, art, zeit_col)
        debug_info.append(f"✅ {label}: {art} in {vor} vor bis {nach} nach Statuszeit")
        return wert, ts

    def strategie_wert_vor_extremwert(df, art, ts_ref, vor, nach, col, zeit_col, debug_info, label):
        """
        Gibt den Wert *vor dem letzten* Extremwert im Zeitfenster zurück.
        """
        if ts_ref is None:
            debug_info.append(f"⚠️ {label}: Kein Statuszeitpunkt – Strategie nicht anwendbar.")
            return None, None
    
        t_start = ts_ref - pd.Timedelta(vor)
        t_ende = ts_ref + pd.Timedelta(nach)
        df_zeit = df[(df[zeit_col] >= t_start) & (df[zeit_col] <= t_ende)]
    
        if df_zeit.empty or col not in df_zeit.columns:
            debug_info.append(f"⚠️ {label}: Kein gültiger Datenbereich.")
            return None, None
    
        extrem_val = df_zeit[col].max() if art == "max" else df_zeit[col].min()
        extrem_idx_list = df_zeit[df_zeit[col] == extrem_val].index.tolist()
    
        if not extrem_idx_list:
            return None, None
    
        letzter_extrem_idx = extrem_idx_list[-1]
        idx_liste = list(df_zeit.index)
        extrem_pos = idx_liste.index(letzter_extrem_idx)
    
        if extrem_pos == 0:
            debug_info.append(f"⚠️ {label}: Kein Wert vor dem letzten Extremwert.")
            return None, None
    
        vor_idx = idx_liste[extrem_pos - 1]
        ts = df_zeit.loc[vor_idx, zeit_col]
        val = df_zeit.loc[vor_idx, col]
        debug_info.append(f"✅ {label}: Wert vor *letztem* {art} in {vor} vor bis {nach} nach Statuszeit")
        return val, ts


    def strategie_wert_vor_letztem_max_nach(df, ts_ref, nach, col, zeit_col, debug_info, label):
        """
        Sucht den letzten Maximalwert im Bereich [ts_ref, ts_ref + nach] und gibt den Wert davor zurück.
        Wenn der Maximalwert am Anfang liegt, wird der vorherige Punkt aus dem Gesamt-DF geholt.
        """
        if ts_ref is None:
            debug_info.append(f"⚠️ {label}: Kein Statuszeitpunkt – Strategie nicht anwendbar.")
            return None, None
    
        t_start = ts_ref
        t_ende = ts_ref + pd.Timedelta(nach)
        df_zeit = df[(df[zeit_col] >= t_start) & (df[zeit_col] <= t_ende)]
    
        if df_zeit.empty or col not in df_zeit.columns:
            debug_info.append(f"⚠️ {label}: Kein gültiger Datenbereich.")
            return None, None
    
        extrem_val = df_zeit[col].max()
        extrem_idx_list = df_zeit[df_zeit[col] == extrem_val].index.tolist()
    
        if not extrem_idx_list:
            return None, None
    
        letzter_extrem_idx = extrem_idx_list[-1]
    
        # Finde Position im Gesamt-DF
        df_indices = df.index.tolist()
        pos_im_df = df_indices.index(letzter_extrem_idx)
    
        if pos_im_df == 0:
            debug_info.append(f"⚠️ {label}: Max liegt ganz am Anfang der Daten – kein vorheriger Punkt vorhanden.")
            return None, None
    
        vor_idx = df_indices[pos_im_df - 1]
        ts = df.loc[vor_idx, zeit_col]
        val = df.loc[vor_idx, col]
    
        debug_info.append(f"✅ {label}: Wert vor letztem Max im Bereich [2→3, +{nach}]")
        return val, ts



    def strategie_wert_vor_statuswechsel(df, von, nach, col, zeit_col, debug_info, label):
        """
        Sucht den Datenpunkt *vor* dem Wechsel von `von` nach `nach` und gibt dessen Wert zurück.
        """
        df = df.reset_index(drop=True)  # Index durchgängig machen
        mask = (df["Status"].shift(1) == von) & (df["Status"] == nach)
        wechsler_idx = mask[mask].index.tolist()
    
        if not wechsler_idx:
            debug_info.append(f"⚠️ {label}: Kein Statuswechsel {von}→{nach} gefunden.")
            return None, None
    
        idx = wechsler_idx[0]
        davor_idx = idx - 1 if idx > 0 else None
    
        if davor_idx is None or davor_idx not in df.index:
            debug_info.append(f"⚠️ {label}: Kein Datenpunkt vor dem Statuswechsel.")
            return None, None
    
        ts = df.loc[davor_idx, zeit_col]
        val = df.loc[davor_idx, col]
        debug_info.append(f"✅ {label}: Wert direkt vor {von}→{nach}")
        return val, ts


    def strategie_min_vor_1_2_oder_5min_min(df, ts_ref, col, zeit_col, debug_info, label):
        """
        Ermittelt den niedrigeren von:
        - dem Wert direkt vor dem Statuswechsel ts_ref
        - dem minimalen Wert in den ersten 5 Minuten von Status_neu == Baggern
        """
        val1, ts1 = None, None
        val2, ts2 = None, None
    
        # 1️⃣ Wert direkt vor dem Statuswechsel
        if ts_ref:
            df_davor = df[df[zeit_col] < ts_ref]
            if not df_davor.empty and col in df_davor.columns:
                val1 = df_davor[col].iloc[-1]
                ts1 = df_davor[zeit_col].iloc[-1]
                debug_info.append(f"🟦 {label}: Wert direkt vor 1→2 = {val1:.3f} @ {ts1}")
    
        # 2️⃣ Min-Wert in den ersten 5 Minuten mit Status_neu == Baggern
        df_bagg = df[(df["Status_neu"] == "Baggern") & (df[zeit_col] >= ts_ref)]
        if not df_bagg.empty:
            zeit_ende = ts_ref + pd.Timedelta("5min")
            df_bagg_5min = df_bagg[df_bagg[zeit_col] <= zeit_ende]
            if not df_bagg_5min.empty and col in df_bagg_5min.columns:
                val2 = df_bagg_5min[col].min()
                ts2 = df_bagg_5min[df_bagg_5min[col] == val2][zeit_col].iloc[0]
                debug_info.append(f"🟨 {label}: Min-Wert in Baggern (5min) = {val2:.3f} @ {ts2}")
    
        # 3️⃣ Vergleich
        if val1 is not None and val2 is not None:
            if val1 < val2:
                debug_info.append(f"✅ {label}: Direkter Wert davor ist kleiner → {val1:.3f}")
                return val1, ts1
            else:
                debug_info.append(f"✅ {label}: Min-Wert in Baggern ist kleiner → {val2:.3f}")
                return val2, ts2
        elif val1 is not None:
            return val1, ts1
        elif val2 is not None:
            return val2, ts2
    
        debug_info.append(f"⚠️ {label}: Keine geeigneten Daten für Vergleich.")
        return None, None






    # ------------------------------------------------------------------------------------------------------------------
    # 🟦 Verdrängung Start
    # ------------------------------------------------------------------------------------------------------------------
    strat = strat_v.get("Start", "standard")
    if strat == "min_in_5vor2nach_1_2":
        wert, ts = strategie_extremwert(df, "min", statuszeit_1_2, "5min", "2min", "Verdraengung", zeit_col, debug_info, "Verdraengung Start")
    elif strat == "min_in_1min_um_1":
        wert, ts = strategie_extremwert(df, "min", statuszeit_1_2, "1min", "1min", "Verdraengung", zeit_col, debug_info, "Verdraengung Start")
    elif strat == "nach_456_auf_1":
        sub = df[df[zeit_col] > statuszeit_456_1] if statuszeit_456_1 else pd.DataFrame()
        wert = first_or_none(sub["Verdraengung"])
        ts_idx = first_index_or_none(sub["Verdraengung"])
        ts = sub.loc[ts_idx, zeit_col] if ts_idx in sub.index else None
        debug_info.append("✅ Verdraengung Start: direkt nach 456→1")
    elif strat == "ein_davor_1_2":
        wert, ts = strategie_wert_vor_statuswechsel(df, 1, 2, "Verdraengung", zeit_col, debug_info, "Verdraengung Start")
    elif strat == "min_vor_1_2_oder_min5":
        wert, ts = strategie_min_vor_1_2_oder_5min_min(df, statuszeit_1_2, "Verdraengung", zeit_col, debug_info, "Verdraengung Start")
    
        
        
    else:
        wert, ts = standardwert(df, statuszeit_1_2, "Verdraengung", "Verdraengung Start")
    result["Verdraengung Start"] = wert
    result["Verdraengung Start TS"] = ts

    # ------------------------------------------------------------------------------------------------------------------
    # 🟥 Verdrängung Ende
    # ------------------------------------------------------------------------------------------------------------------
    strat = strat_v.get("Ende", "standard")
    if strat == "max_in_2min_um_2_3":
        wert, ts = strategie_extremwert(df, "max", statuszeit_2_3, "2min", "2min", "Verdraengung", zeit_col, debug_info, "Verdraengung Ende")
    elif strat == "max_in_1min_um_2_3":
        wert, ts = strategie_extremwert(df, "max", statuszeit_2_3, "1min", "1min", "Verdraengung", zeit_col, debug_info, "Verdraengung Ende")
    elif strat == "vor_max_in_1min_um_2_3":
        wert, ts = strategie_wert_vor_extremwert(df, "max", statuszeit_2_3, "1min", "1min", "Verdraengung", zeit_col, debug_info, "Verdraengung Ende")

    elif strat == "vor_letztem_max_in_1min_nach_2_3":
        wert, ts = strategie_wert_vor_letztem_max_nach(df, statuszeit_2_3, "1min", "Verdraengung", zeit_col, debug_info, "Verdraengung Ende")

    elif strat == "vor_max_in_2min_um_2_3":
        wert, ts = strategie_wert_vor_extremwert(df, "max", statuszeit_2_3, "2min", "2min", "Verdraengung", zeit_col, debug_info, "Verdraengung Ende")

        
        
    
    else:
        wert, ts = standardwert(df, statuszeit_2_3, "Verdraengung", "Verdraengung Ende")
    result["Verdraengung Ende"] = wert
    result["Verdraengung Ende TS"] = ts

    # ------------------------------------------------------------------------------------------------------------------
    # 🟧 Ladungsvolumen Start
    # ------------------------------------------------------------------------------------------------------------------
    strat = strat_l.get("Start", "standard")
    if strat == "min_in_5vor2nach_1_2":
        wert, ts = strategie_extremwert(df, "min", statuszeit_1_2, "5min", "2min", "Ladungsvolumen", zeit_col, debug_info, "Ladungsvolumen Start")
    elif strat == "nach_456_auf_1":
        sub = df[df[zeit_col] > statuszeit_456_1] if statuszeit_456_1 else pd.DataFrame()
        wert = first_or_none(sub["Ladungsvolumen"])
        ts_idx = first_index_or_none(sub["Ladungsvolumen"])
        ts = sub.loc[ts_idx, zeit_col] if ts_idx in sub.index else None
        debug_info.append("✅ Ladungsvolumen Start: direkt nach 456→1")
    elif strat == "erster_wert":
        wert = first_or_none(df["Ladungsvolumen"])
        ts_idx = first_index_or_none(df["Ladungsvolumen"])
        ts = df.loc[ts_idx, zeit_col] if ts_idx in df.index else None
        debug_info.append("✅ Ladungsvolumen Start: erster Wert im Umlauf")
    elif strat == "ein_davor_1_2":
        wert, ts = strategie_wert_vor_statuswechsel(df, 1, 2, "Ladungsvolumen", zeit_col, debug_info, "Ladungsvolumen Start")
    elif strat == "min_vor_1_2_oder_min5":
        wert, ts = strategie_min_vor_1_2_oder_5min_min(df, statuszeit_1_2, "Ladungsvolumen", zeit_col, debug_info, "Ladungsvolumen Start")
    elif strat == "null":
        wert, ts = 0.0, None
        debug_info.append("✅ Ladungsvolumen Start: null (0.0 m³)")
    else:
        wert, ts = standardwert(df, statuszeit_1_2, "Ladungsvolumen", "Ladungsvolumen Start")
    result["Ladungsvolumen Start"] = wert
    result["Ladungsvolumen Start TS"] = ts

    # ------------------------------------------------------------------------------------------------------------------
    # 🟨 Ladungsvolumen Ende
    # ------------------------------------------------------------------------------------------------------------------
    strat = strat_l.get("Ende", "standard")
    if strat == "2min_nach_2_3" and statuszeit_2_3:
        ziel = statuszeit_2_3 + pd.Timedelta("2min")
        sub = df[df[zeit_col] >= ziel]
        wert = first_or_none(sub["Ladungsvolumen"])
        ts_idx = first_index_or_none(sub["Ladungsvolumen"])
        ts = sub.loc[ts_idx, zeit_col] if ts_idx in sub.index else None
        debug_info.append("✅ Ladungsvolumen Ende: erster Wert ≥ 2min nach 2→3")
    elif strat == "max_in_2min_um_2_3":
        wert, ts = strategie_extremwert(df, "max", statuszeit_2_3, "2min", "2min", "Ladungsvolumen", zeit_col, debug_info, "Ladungsvolumen Ende")
        
    elif strat == "vor_max_in_2min_um_2_3":
        wert, ts = strategie_wert_vor_extremwert(df, "max", statuszeit_2_3, "2min", "2min", "Ladungsvolumen", zeit_col, debug_info, "Ladungsvolumen Ende")

        
    
    else:
        wert, ts = standardwert(df, statuszeit_2_3, "Ladungsvolumen", "Ladungsvolumen Ende")
    result["Ladungsvolumen Ende"] = wert
    result["Ladungsvolumen Ende TS"] = ts

    return result, debug_info

# ------------------------------------------------------------------------------------------------------------------
# Strategien für dropdown
# ------------------------------------------------------------------------------------------------------------------

STRATEGIE_REGISTRY = {
    "Start": {
        "standard": "Standard (am Statuswechsel)",
        "min_in_5vor2nach_1_2": "Minimalwert 5 min vor bis 2 min nach 1→2",
        "min_in_1min_um_1": "Minimalwert ±1 min um 1→2",
        "nach_456_auf_1": "Erster Wert nach 456→1",
        "erster_wert": "Erster Wert im Zyklus",
        "null": "Fester Wert: 0.0",
        "ein_davor_1_2": "HPA - Wert direkt vor 1→2",
        "min_vor_1_2_oder_min5":"HPA - Wert direkt vor 1→2 oder min. 5 Minuten"
    },
    "Ende": {
        "standard": "Standard (am Statuswechsel)",
        "max_in_1min_um_2_3": "Maximalwert ±1 min um 2→3",
        "max_in_2min_um_2_3": "Maximalwert ±2 min um 2→3",
        "2min_nach_2_3": "Erster Wert ab 2 min nach 2→3",
        "vor_letztem_max_in_1min_nach_2_3": "HPA - Wert vor letztem Maximum in 1 min nach 2→3",
        "vor_max_in_2min_um_2_3": "Wert vor Maximum ±2 min um 2→3",

    }
}

