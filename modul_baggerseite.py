import pandas as pd

def erkenne_baggerseite(df: pd.DataFrame, toleranz: float = 0.01) -> str:
    """
    Erkennt, ob der Bagger Backbord (BB), Steuerbord (SB) oder BB+SB nutzt.
    Nutzt nur Rohsensorwerte (keine berechneten Felder) und ignoriert numerisches Rauschen unterhalb der Toleranz.
    """

    # Rohdaten-Spalten, KEINE berechneten Felder wie Abs_Tiefe_Kopf_*
    bb_rohdaten = [
        'RW_BB', 'HW_BB', 'Tiefe_Kopf_BB', 'Gemischdichte_BB',
        'Gemischgeschwindigkeit_BB', 'Druck_vor_Baggerpumpe_BB',
        'Druck_hinter_Baggerpumpe_BB', 'AMOB_Zeit_BB',
        'Druck_Druckwasserpumpe_BB'
    ]

    sb_rohdaten = [
        'RW_SB', 'HW_SB', 'Tiefe_Kopf_SB', 'Gemischdichte_SB',
        'Gemischgeschwindigkeit_SB', 'Druck_vor_Baggerpumpe_SB',
        'Druck_hinter_Baggerpumpe_SB', 'AMOB_Zeit_SB',
        'Druck_Druckwasserpumpe_SB'
    ]

    # Nur vorhandene Spalten prüfen
    bb_cols = [col for col in bb_rohdaten if col in df.columns]
    sb_cols = [col for col in sb_rohdaten if col in df.columns]

    # Summiere Anzahl "nicht-nahe-0"-Werte je Seite
    bb_aktiv = (df[bb_cols].abs() > toleranz).sum(numeric_only=True).sum()
    sb_aktiv = (df[sb_cols].abs() > toleranz).sum(numeric_only=True).sum()

    if bb_aktiv > 0 and sb_aktiv == 0:
        return "BB"
    elif sb_aktiv > 0 and bb_aktiv == 0:
        return "SB"
    elif sb_aktiv > 0 and bb_aktiv > 0:
        return "BB+SB"
    else:
        return "Unbekannt"
