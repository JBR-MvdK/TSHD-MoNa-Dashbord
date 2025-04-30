# === Importieren der benötigten Bibliothek ============================================================================
import pandas as pd

# === Funktion: erkenne_baggerseite(df, toleranz) ============================================================================
def erkenne_baggerseite(df: pd.DataFrame, toleranz: float = 0.01) -> str:
    """
    Erkennt automatisch, ob auf der Backbord-Seite (BB), Steuerbord-Seite (SB) oder auf beiden Seiten (BB+SB) gebaggert wurde.

    Die Erkennung basiert ausschließlich auf Rohsensordaten.
    Werte unterhalb einer Toleranzgrenze (z.B. Sensorrauschen) werden ignoriert.

    Parameter:
    - df : Pandas DataFrame mit den MoNa-Daten
    - toleranz : float, Schwelle zur Filterung sehr kleiner Werte (z.B. 0.01)

    Rückgabe:
    - "BB"      → Es wurde nur auf der Backbord-Seite gearbeitet
    - "SB"      → Es wurde nur auf der Steuerbord-Seite gearbeitet
    - "BB+SB"   → Es wurde auf beiden Seiten gearbeitet
    - "Unbekannt" → Keine Aktivität erkennbar
    """

    # --- Definiere relevante Rohdatenspalten für BB und SB ---
    # (KEINE berechneten Felder wie "Abs_Tiefe_Kopf_*", sondern nur Rohdaten)

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

    # --- Prüfe, welche der erwarteten Spalten im DataFrame tatsächlich vorhanden sind ---
    bb_cols = [col for col in bb_rohdaten if col in df.columns]
    sb_cols = [col for col in sb_rohdaten if col in df.columns]

    # --- Erkenne Aktivität ---
    # Zähle je Seite, wie viele Werte "nennenswert von 0 verschieden" sind (über Toleranz)

    bb_aktiv = (df[bb_cols].abs() > toleranz).sum(numeric_only=True).sum()
    sb_aktiv = (df[sb_cols].abs() > toleranz).sum(numeric_only=True).sum()

    # --- Entscheidung auf Basis der erkannten Aktivität ---
    if bb_aktiv > 0 and sb_aktiv == 0:
        return "BB"
    elif sb_aktiv > 0 and bb_aktiv == 0:
        return "SB"
    elif sb_aktiv > 0 and bb_aktiv > 0:
        return "BB+SB"
    else:
        return "Unbekannt"

