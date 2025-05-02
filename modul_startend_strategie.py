# ======================================================================================================================
# 📦 modul_startend_strategie.py – Ermittlung von Start- und Endwerten gemäß Strategie
# ======================================================================================================================

import pandas as pd

# ----------------------------------------------------------------------------------------------------------------------
# 🔧 Hilfsfunktionen
# ----------------------------------------------------------------------------------------------------------------------

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

def get_statuswechselzeit_flexibel(df, von, nach, zeit_col="timestamp", ignorierte_status=None):
    """
    Findet auch indirekte Wechsel von `von` nach `nach` unter Überspringung von definierten Zwischenstatus.
    """
    if ignorierte_status is None:
        ignorierte_status = []
    df = df[[zeit_col, "Status"]].copy()
    df["prev"] = df["Status"].shift(1)

    for i in range(1, len(df)):
        s_prev = df.iloc[i - 1]["Status"]
        s_curr = df.iloc[i]["Status"]
        if s_prev == von and s_curr == nach:
            return df.iloc[i][zeit_col]
        if s_prev == von and s_curr in ignorierte_status:
            for j in range(i + 1, len(df)):
                if df.iloc[j]["Status"] == nach:
                    return df.iloc[j][zeit_col]
                if df.iloc[j]["Status"] not in ignorierte_status:
                    break
    return None

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

    debug_info = []
    result = {}

    # Strategien extrahieren
    strat_v = strategie.get("Verdraengung", {}) if strategie else {}
    strat_l = strategie.get("Ladungsvolumen", {}) if strategie else {}

    # Referenz-DataFrame festlegen (z. B. Gesamtdaten)
    df_ref = df_gesamt if df_gesamt is not None else df

    # --- Statuswechsel-Zeitpunkte suchen ---
    statuszeit_1_2 = get_statuswechselzeit(df_ref, 1, 2, zeit_col)
    statuszeit_2_3 = get_statuswechselzeit_flexibel(df_ref, 2, 3, zeit_col, ignorierte_status=[1])
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
    else:
        wert, ts = standardwert(df, statuszeit_2_3, "Ladungsvolumen", "Ladungsvolumen Ende")
    result["Ladungsvolumen Ende"] = wert
    result["Ladungsvolumen Ende TS"] = ts

    return result, debug_info
