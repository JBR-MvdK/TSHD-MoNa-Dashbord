import pandas as pd
import io

def konvertiere_hpa_ascii(files_hpa):
    """
    Konvertiert HPA-Daten ins MoNa-kompatible Format (Tab-getrennt),
    sodass sie direkt an `parse_mona()` übergeben werden können.
    """
    
    converted_files = []

    for file in files_hpa:
        # 1. Dateiinhalt dekodieren
        try:
            content = file.getvalue().decode("utf-8")
        except UnicodeDecodeError:
            content = file.getvalue().decode("latin-1")

        # 2. Zeilen bereinigen (STX, ETX, Leerzeichen)
        lines = content.splitlines()
        cleaned_lines = [line.strip("\x02").strip("\x03").strip() for line in lines if line.strip()]
        rows = [line.split("\t") for line in cleaned_lines]

        # 3. HPA-Spalten (bitte ggf. anpassen!)
        hpa_columns = [
            "timestamp", "Status", "RW_BB", "HW_BB", "RW_SB", "HW_SB", "Geschwindigkeit", "Kurs",
            "Tiefgang_vorne", "Tiefgang_hinten", "Verdraengung",
            "Abs_Tiefe_Kopf_BB", "Abs_Tiefe_Kopf_SB", "Pegel",
            "Gemischdichte_BB", "Gemischdichte_SB",
            "Gemischgeschwindigkeit_BB", "Gemischgeschwindigkeit_SB",
            "Fuellstand_BB_vorne", "Fuellstand_SB_vorne",
            "Fuellstand_BB_mitte", "Fuellstand_SB_mitte",
            "Fuellstand_SB_hinten", "Fuellstand_BB_hinten",
            "Masse_Feststoff_TDS", "Masse_leeres_Schiff", "Ladungsvolumen",
            "Druck_vor_Baggerpumpe_BB", "Druck_vor_Baggerpumpe_SB",
            "Druck_hinter_Baggerpumpe_BB", "Druck_hinter_Baggerpumpe_SB",
            "Ballast", "AMOB_Zeit_BB", "AMOB_Zeit_SB", "Zusatzwassermenge",
            "Gemischdichte_Verspuelen", "Gemischgeschwindigkeit_Verspuelen"
        ]

        df_hpa = pd.DataFrame(rows, columns=hpa_columns)

        # 4. Typumwandlung für numerische Spalten
        for col in df_hpa.columns:
            df_hpa[col] = pd.to_numeric(df_hpa[col], errors='ignore')

        # Tiefe_Kopf_* leer lassen – MoNa wird es dann nicht verrechnen
        df_hpa["Tiefe_Kopf_BB"] = df_hpa["Abs_Tiefe_Kopf_BB"] + df_hpa["Pegel"]
        df_hpa["Tiefe_Kopf_SB"] = df_hpa["Abs_Tiefe_Kopf_SB"] + df_hpa["Pegel"]

        # 5. RW_Schiff / HW_Schiff aus BB/SB-Werten berechnen (ggf. nur BB)
        df_hpa["RW_BB"] = pd.to_numeric(df_hpa["RW_BB"], errors="coerce")
        df_hpa["RW_SB"] = pd.to_numeric(df_hpa["RW_SB"], errors="coerce")
        df_hpa["RW_Schiff"] = df_hpa[["RW_BB", "RW_SB"]].apply(
            lambda row: row["RW_BB"] if pd.isna(row["RW_SB"]) or row["RW_SB"] == 0
            else (row["RW_BB"] + row["RW_SB"]) / 2, axis=1
        )

        df_hpa["HW_BB"] = pd.to_numeric(df_hpa["HW_BB"], errors="coerce")
        df_hpa["HW_SB"] = pd.to_numeric(df_hpa["HW_SB"], errors="coerce")
        df_hpa["HW_Schiff"] = df_hpa[["HW_BB", "HW_SB"]].apply(
            lambda row: row["HW_BB"] if pd.isna(row["HW_SB"]) or row["HW_SB"] == 0
            else (row["HW_BB"] + row["HW_SB"]) / 2, axis=1
        )

        # 6. Datum / Zeit aus timestamp zerlegen
        df_hpa['timestamp'] = pd.to_datetime(
            df_hpa['timestamp'], format="%d.%m.%Y %H:%M:%S", errors='coerce'
            )
        df_hpa["Datum"] = df_hpa["timestamp"].dt.strftime("%Y%m%d")
        df_hpa["Zeit"] = df_hpa["timestamp"].dt.strftime("%H%M%S")

        # 7. Baggernummer setzen (fiktiv z. B. für HPA)
        df_hpa["Baggernummer"] = "999"

        # 8. Alle erwarteten MoNa-Spalten
        mona_columns = [
            'Datum', 'Zeit', 'Status', 'RW_BB', 'HW_BB', 'RW_SB', 'HW_SB',
            'RW_Schiff', 'HW_Schiff', 'Geschwindigkeit', 'Kurs',
            'Tiefgang_vorne', 'Tiefgang_hinten', 'Verdraengung',
            'Tiefe_Kopf_BB', 'Tiefe_Kopf_SB', 'Pegel', 'Pegelkennung', 'Pegelstatus',
            'Gemischdichte_BB', 'Gemischdichte_SB', 'Gemischgeschwindigkeit_BB', 'Gemischgeschwindigkeit_SB',
            'Fuellstand_BB_vorne', 'Fuellstand_SB_vorne', 'Fuellstand_BB_mitte', 'Fuellstand_SB_mitte',
            'Fuellstand_SB_hinten', 'Fuellstand_BB_hinten', 'Masse_Feststoff_TDS', 'Masse_leeres_Schiff',
            'Ladungsvolumen', 'Druck_vor_Baggerpumpe_BB', 'Druck_vor_Baggerpumpe_SB',
            'Druck_hinter_Baggerpumpe_BB', 'Druck_hinter_Baggerpumpe_SB', 'Ballast', 'AMOB_Zeit_BB',
            'AMOB_Zeit_SB', 'Druck_Druckwasserpumpe_BB', 'Druck_Druckwasserpumpe_SB',
            'Baggerfeld', 'Baggernummer'
        ]

        # 9. Fehlende Spalten ergänzen mit None
        for col in mona_columns:
            if col not in df_hpa.columns:
                df_hpa[col] = None

        # 10. Nur relevante Spalten in korrekter Reihenfolge
        df_final = df_hpa[mona_columns]

        # 11. Als tab-getrennte Textdatei (wie echte MoNa-Datei)
        text_lines = ["\t".join(df_final.columns)] + [
            "\t".join(str(x) if pd.notnull(x) else "" for x in row)
            for row in df_final.values
        ]
        text_data = "\n".join(text_lines)

        # 12. Als In-Memory-Datei zurückgeben
        memory_file = io.BytesIO(text_data.encode("utf-8"))
        converted_files.append(memory_file)

    return converted_files
