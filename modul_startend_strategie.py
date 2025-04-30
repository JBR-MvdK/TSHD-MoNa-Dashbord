import pandas as pd

def first_or_none(series):
    return series.iloc[0] if not series.empty else None

def get_statuswechselzeit(df, von, nach, zeit_col="timestamp"):
    mask = (df["Status"].shift(1) == von) & (df["Status"] == nach)
    wechsler = df[mask]
    return wechsler[zeit_col].iloc[0] if not wechsler.empty else None

def suche_extrem(df, zeitpunkt, dauer, col, art="max", zeit_col="timestamp"):
    t_start = zeitpunkt - pd.Timedelta(dauer)
    t_ende = zeitpunkt + pd.Timedelta(dauer)
    df_zeit = df[(df[zeit_col] >= t_start) & (df[zeit_col] <= t_ende)]
    if df_zeit.empty or col not in df_zeit.columns:
        return None
    return df_zeit[col].max() if art == "max" else df_zeit[col].min()


def berechne_start_endwerte(df, strategie=None, zeit_col="timestamp"):
    """
    Liefert Start-/Endwerte für Verdraengung und Ladungsvolumen – je nach Strategie oder Standardlogik.
    Gibt zusätzlich Debug-Messages als Liste zurück.
    """
    strat_v = strategie.get("Verdraengung", {}) if strategie else {}
    strat_l = strategie.get("Ladungsvolumen", {}) if strategie else {}

    debug_info = []  # ⬅️ Sammle hier Textausgaben

    statuszeit_2_3 = get_statuswechselzeit(df, 2, 3, zeit_col)
    statuszeit_1_2 = get_statuswechselzeit(df, 1, 2, zeit_col)
    statuszeit_456_1 = get_statuswechselzeit(df, 456, 1, zeit_col)

    debug_info.append(f"📍 Statuszeit 456→1: {statuszeit_456_1}")
    debug_info.append(f"📍 Statuszeit 1→2: {statuszeit_1_2}")
    debug_info.append(f"📍 Statuszeit 2→3: {statuszeit_2_3}")

    # Verdraengung Start
    if strat_v.get("Start") == "min_in_1min_um_1" and statuszeit_1_2:
        debug_info.append("✅ Verdraengung Start: min_in_1min_um_1")
        verdr_start = suche_extrem(df, statuszeit_1_2, "1min", "Verdraengung", "min", zeit_col)
    elif strat_v.get("Start") == "nach_456_auf_1" and statuszeit_456_1:
        debug_info.append("✅ Verdraengung Start: nach_456_auf_1")
        verdr_start = first_or_none(df[df[zeit_col] > statuszeit_456_1]["Verdraengung"])
    else:
        debug_info.append("⚠️ Verdraengung Start: Standardwert (Status 2→3)")
        verdr_start = first_or_none(df[df[zeit_col] == statuszeit_2_3]["Verdraengung"]) if statuszeit_2_3 else None

    # Verdraengung Ende
    if strat_v.get("Ende") == "max_in_1min_um_2_3" and statuszeit_2_3:
        debug_info.append("✅ Verdraengung Ende: max_in_1min_um_2_3")
        verdr_ende = suche_extrem(df, statuszeit_2_3, "1min", "Verdraengung", "max", zeit_col)
    else:
        debug_info.append("⚠️ Verdraengung Ende: Standardwert (Status 2→3)")
        verdr_ende = first_or_none(df[df[zeit_col] == statuszeit_2_3]["Verdraengung"]) if statuszeit_2_3 else None

    # Ladungsvolumen Start
    if strat_l.get("Start") == "nach_456_auf_1" and statuszeit_456_1:
        debug_info.append("✅ Ladungsvolumen Start: nach_456_auf_1")
        try:
            ladung_start = df[df[zeit_col] > statuszeit_456_1]["Ladungsvolumen"].iloc[0]
        except:
            ladung_start = 0.0
    elif strat_l.get("Start") == "null":
        debug_info.append("✅ Ladungsvolumen Start: null (0.0 m³)")
        ladung_start = 0.0
    else:
        debug_info.append("⚠️ Ladungsvolumen Start: Standardwert (Status 2→3)")
        ladung_start = first_or_none(df[df[zeit_col] == statuszeit_2_3]["Ladungsvolumen"]) if statuszeit_2_3 else None

    # Ladungsvolumen Ende
    if strat_l.get("Ende") == "2min_nach_2_3" and statuszeit_2_3:
        debug_info.append("✅ Ladungsvolumen Ende: 2min_nach_2_3")
        t_ziel = statuszeit_2_3 + pd.Timedelta("2min")
        ladung_ende = first_or_none(df[df[zeit_col] >= t_ziel]["Ladungsvolumen"])
    else:
        debug_info.append("⚠️ Ladungsvolumen Ende: Standardwert (Status 2→3)")
        ladung_ende = first_or_none(df[df[zeit_col] == statuszeit_2_3]["Ladungsvolumen"]) if statuszeit_2_3 else None

    return {
        "Verdraengung Start": verdr_start,
        "Verdraengung Ende": verdr_ende,
        "Ladungsvolumen Start": ladung_start,
        "Ladungsvolumen Ende": ladung_ende
    }, debug_info 


