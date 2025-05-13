# === Imports für das Modul ============================================================================
import pandas as pd
from datetime import datetime

# === Funktion: parse_mona(files) ============================================================================
def parse_mona(files):
    """
    Liest MoNa-Datendateien (.txt) ein und wandelt sie in ein DataFrame um.
    
    Schritte:
    - Dateien dekodieren und aufbereiten
    - Zeilen splitten und in Spalten umwandeln
    - Zeitstempel generieren
    - Datentypen konvertieren
    - Zusatzspalten berechnen (z.B. absolute Baggertiefe, Mittelwert Füllstände)
    - Schiffsname aus Baggernummer zuordnen
    
    Rückgabe:
    - DataFrame (nur mit gültigen Timestamps)
    - Maximaler Rechtswert (RW_Schiff)
    - Maximaler Hochwert (HW_Schiff)
    """

    all_data = []

    # Durch alle hochgeladenen Dateien iterieren
    for file in files:
        
        try:
            content = file.getvalue().decode("utf-8")
        except UnicodeDecodeError:
            content = file.getvalue().decode("latin-1")  # Fallback, z. B. für Windows-Dateien
        
        lines = content.splitlines()               # In Zeilen aufteilen
        cleaned = [line.strip().strip("\x02").strip("\x03").split("\t") 
                   for line in lines if line.strip()]  # Bereinigen + Spalten trennen
        all_data.extend(cleaned)                   # Alle Zeilen sammeln

    # Spaltennamen definieren
    columns = [
        'Datum', 'Zeit', 'Status', 'RW_BB', 'HW_BB', 'RW_SB', 'HW_SB', 'RW_Schiff', 'HW_Schiff',
        'Geschwindigkeit', 'Kurs', 'Tiefgang_vorne', 'Tiefgang_hinten', 'Verdraengung',
        'Tiefe_Kopf_BB', 'Tiefe_Kopf_SB', 'Pegel', 'Pegelkennung', 'Pegelstatus',
        'Gemischdichte_BB', 'Gemischdichte_SB', 'Gemischgeschwindigkeit_BB', 'Gemischgeschwindigkeit_SB',
        'Fuellstand_BB_vorne', 'Fuellstand_SB_vorne', 'Fuellstand_BB_mitte', 'Fuellstand_SB_mitte',
        'Fuellstand_SB_hinten', 'Fuellstand_BB_hinten', 'Masse_Feststoff_TDS', 'Masse_leeres_Schiff',
        'Ladungsvolumen', 'Druck_vor_Baggerpumpe_BB', 'Druck_vor_Baggerpumpe_SB',
        'Druck_hinter_Baggerpumpe_BB', 'Druck_hinter_Baggerpumpe_SB', 'Ballast', 'AMOB_Zeit_BB',
        'AMOB_Zeit_SB', 'Druck_Druckwasserpumpe_BB', 'Druck_Druckwasserpumpe_SB',
        'Baggerfeld', 'Baggernummer'
    ]

    # Erzeuge DataFrame
    df = pd.DataFrame(all_data, columns=columns)

    # Zeitstempel ("timestamp") aus Datum und Zeit erzeugen
    df['timestamp'] = pd.to_datetime(
        df['Datum'].astype(str) + df['Zeit'].astype(str).str.zfill(6),
        format="%Y%m%d%H%M%S",
        errors='coerce'
    )
    df = df.sort_values(by="timestamp")

    # Datentypen aller Spalten konvertieren (außer String-Spalten)
    for col in df.columns.difference(['Datum', 'Zeit', 'timestamp', 'Baggernummer', 'Pegelkennung']):
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Baggernummer säubern (Leerzeichen entfernen)
    df['Baggernummer'] = df['Baggernummer'].astype(str).str.strip()

    # Berechnung der absoluten Baggertiefe relativ zum Wasserstand (Pegel)
    df['Abs_Tiefe_Kopf_BB'] = (df['Tiefe_Kopf_BB'].fillna(0) - df['Pegel'].fillna(0)) * (-1)
    df['Abs_Tiefe_Kopf_SB'] = (df['Tiefe_Kopf_SB'].fillna(0) - df['Pegel'].fillna(0)) * (-1)

    # Mittelwert der verfügbaren Füllstandsmessungen berechnen
    fuell_cols = [
        'Fuellstand_BB_vorne', 'Fuellstand_SB_vorne',
        'Fuellstand_BB_mitte', 'Fuellstand_SB_mitte',
        'Fuellstand_BB_hinten', 'Fuellstand_SB_hinten'
    ]
    df['Fuellstand_Mittel'] = df[fuell_cols].mean(axis=1)

    # KPIs berechnen: Maximaler Rechtswert (RW) und Hochwert (HW) für Übersichtskarten
    rw_max = df["RW_Schiff"].dropna().max()
    hw_max = df["HW_Schiff"].dropna().max()

    # Schiffsname zuordnen anhand der Baggernummer
    df["Schiffsname"] = df["Baggernummer"].map({
        "131": "WID AKKE",
        "167": "WID AQUADELTA",
        "137": "WID JAN",
        "129": "WID MAASMOND",
        "209": "TSHD IJSSELDELTA",
        "155": "TSHD ANKE"
    })
    
    # Rückgabe: nur gültige Zeilen (ohne fehlenden timestamp)
    return df.dropna(subset=['timestamp']), rw_max, hw_max


# === Funktion: berechne_tds_parameter(df, pf, pw) ============================================================================
def berechne_tds_parameter(df, pf, pw):
    """
    Berechnet verschiedene Kenngrößen basierend auf Rohdaten und Dichteangaben:
    - Ladungsmasse
    - Ladungsdichte
    - Feststoffkonzentration
    - Feststoffvolumen
    - Feststoffmasse

    Parameter:
    - df : DataFrame der MoNa-Daten
    - pf : Feststoffdichte [t/m³]
    - pw : Wasserdichte [t/m³]

    Rückgabe:
    - DataFrame mit zusätzlichen Spalten
    """

    df['Ladungsmasse'] = df['Verdraengung'] - df['Masse_leeres_Schiff']
    df['Ladungsdichte'] = df['Ladungsmasse'] / df['Ladungsvolumen']
    df['Feststoffkonzentration'] = (df['Ladungsdichte'] - pw) / (pf - pw)
    df['Feststoffvolumen'] = df['Feststoffkonzentration'] * df['Ladungsvolumen']
    df['Feststoffmasse'] = df['Feststoffkonzentration'] * df['Ladungsvolumen'] * pf
    return df
