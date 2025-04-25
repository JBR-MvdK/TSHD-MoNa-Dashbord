import pandas as pd
from datetime import datetime

def parse_mona(files):
    all_data = []

    for file in files:
        content = file.getvalue().decode("utf-8")
        lines = content.splitlines()
        cleaned = [line.strip().strip("\x02").strip("\x03").split("\t") for line in lines if line.strip()]
        all_data.extend(cleaned)

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

    df = pd.DataFrame(all_data, columns=columns)

    # Zeitstempel berechnen
    df['timestamp'] = pd.to_datetime(
        df['Datum'].astype(str) + df['Zeit'].astype(str).str.zfill(6),
        format="%Y%m%d%H%M%S",
        errors='coerce'
    )
    df = df.sort_values(by="timestamp")

    # Datentypen konvertieren (ausgenommen String-Felder)
    for col in df.columns.difference(['Datum', 'Zeit', 'timestamp', 'Baggernummer', 'Pegelkennung']):
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df['Baggernummer'] = df['Baggernummer'].astype(str).str.strip()

    # Neue Variablen berechnen
    df['Abs_Tiefe_Kopf_BB'] = (df['Tiefe_Kopf_BB'].fillna(0) - df['Pegel'].fillna(0)) * (-1)
    df['Abs_Tiefe_Kopf_SB'] = (df['Tiefe_Kopf_SB'].fillna(0) - df['Pegel'].fillna(0)) * (-1)


    # Mittelwert der Füllstände (automatisch nur gültige Spalten berücksichtigen)
    fuell_cols = [
        'Fuellstand_BB_vorne', 'Fuellstand_SB_vorne',
        'Fuellstand_BB_mitte', 'Fuellstand_SB_mitte',
        'Fuellstand_BB_hinten', 'Fuellstand_SB_hinten'
    ]
    df['Fuellstand_Mittel'] = df[fuell_cols].mean(axis=1)

    # KPIs
    rw_max = df["RW_Schiff"].dropna().max()
    hw_max = df["HW_Schiff"].dropna().max()
    
    df["Baggernummer"] = df["Baggernummer"].astype(str).str.strip()    
    df["Schiffsname"] = df["Baggernummer"].map({
        "131": "WID AKKE",
        "167": "WID AQUADELTA",
        "137": "WID JAN",
        "129": "WID MAASMOND",
        "209": "TSHD IJSSELDELTA"
    })
    
    return df.dropna(subset=['timestamp']), rw_max, hw_max
    
def berechne_tds_parameter(df, pf, pw):
    df['Ladungsmasse'] = df['Verdraengung'] - df['Masse_leeres_Schiff']
    df['Ladungsdichte'] = df['Ladungsmasse'] / df['Ladungsvolumen']
    df['Feststoffkonzentration'] = (df['Ladungsdichte'] - pw) / (pf - pw)
    df['Feststoffvolumen'] = df['Feststoffkonzentration'] * df['Ladungsvolumen']
    df['Feststoffmasse'] = df['Feststoffkonzentration'] * df['Ladungsvolumen'] * pf
    return df

