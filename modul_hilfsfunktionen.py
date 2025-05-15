# ==================================================================================================
# 🔧 Allgemeine Hilfsfunktionen für Zeitreihen, Zeitdauern, Zeitzonen, Formatierung & Parameterprüfung
# ==================================================================================================

# 📚 Import von Standard- und Drittanbieter-Bibliotheken
import pandas as pd               # Datenanalyse (DataFrames etc.)
import pytz                      # Zeitzonenbehandlung
import os, json                  # Dateizugriff & JSON-Parsing
import streamlit as st           # UI-Komponenten in der Streamlit-App

# --------------------------------------------------------------------------------------------------
# 📋 DataFrame-Hilfsfunktionen
# --------------------------------------------------------------------------------------------------

def split_by_gap(df, max_gap_minutes=2):
    """
    Teilt ein DataFrame in Segmente, wenn der Abstand zwischen zwei Zeitstempeln
    größer ist als `max_gap_minutes`.

    Beispiel: Bei Zeitlücken > 2 Minuten wird ein neues Segment begonnen.
    Ergebnis ist ein neues Feld 'segment', das gruppiert verwendet werden kann.
    """
    df = df.sort_values(by="timestamp")  # chronologische Sortierung
    df["gap"] = df["timestamp"].diff().dt.total_seconds() > (max_gap_minutes * 60)  # Boolean-Spalte: True bei Lücke
    df["segment"] = df["gap"].cumsum()  # Inkrementiert bei jedem True → Segmentnummern
    return df


# --------------------------------------------------------------------------------------------------
# 🕒 Zeit- und Zeitzonenfunktionen
# --------------------------------------------------------------------------------------------------

def convert_timestamp(ts, zeitzone):
    """
    Konvertiert einen Zeitstempel in eine gewünschte Zeitzone (UTC oder Lokalzeit).

    - Bei 'UTC' wird (wenn nötig) lokalisiert oder konvertiert.
    - Bei 'Lokal' wird immer nach Europe/Berlin umgewandelt.
    """
    if ts is None or pd.isnull(ts):
        return None
    if zeitzone == "UTC":
        return ts.tz_localize("UTC") if ts.tzinfo is None else ts.astimezone(pytz.UTC)
    elif zeitzone == "Lokal (Europe/Berlin)":
        return ts.tz_localize("UTC").astimezone(pytz.timezone("Europe/Berlin")) if ts.tzinfo is None else ts.astimezone(pytz.timezone("Europe/Berlin"))
    return ts  # Rückfall: keine Konvertierung

def format_time(ts, zeitzone):
    """
    Formatiert ein Zeitstempelobjekt in lesbares Format ('dd.mm.yyyy hh:mm:ss').
    Nutzt zuvor die Konvertierung in die gewünschte Zeitzone.
    """
    ts_conv = convert_timestamp(ts, zeitzone)
    return "-" if ts_conv is None or pd.isnull(ts_conv) else ts_conv.strftime("%d.%m.%Y %H:%M:%S")

def plot_x(df, mask, zeitzone):
    """
    Gibt die X-Achse für Plotly zurück – je nach Zeitzone.
    Filtert mit einer Maske für gültige Datenzeilen.
    """
    col = "timestamp"
    if zeitzone == "Lokal (Europe/Berlin)":
        return df.loc[mask, col].dt.tz_convert("Europe/Berlin")
    return df.loc[mask, col]  # default: UTC


# --------------------------------------------------------------------------------------------------
# ⚙️ Schiffsspezifische Parameterfunktionen (z. B. für Plausibilitätsfilterung)
# --------------------------------------------------------------------------------------------------

def lade_schiffsparameter(pfad="schiffsparameter.json"):
    """
    Lädt die JSON-Datei mit Parametern für jedes Schiff.
    Diese enthalten z. B. min/max-Grenzen für Messwerte.

    Gibt ein Dictionary zurück: {Schiffsname → Parameter → Min/Max}
    """
    if os.path.exists(pfad):
        try:
            with open(pfad, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            st.sidebar.error(f"❌ Fehler in JSON-Datei: {e}")
            return {}
    return {}

def pruefe_werte_gegen_schiffsparameter(df, schiff_name, parameter_dict):
    """
    Wendet für ein gegebenes Schiff definierte Min/Max-Grenzen auf das DataFrame an.
    Ungültige Werte (außerhalb des erlaubten Bereichs) werden entfernt.

    Gibt zurück:
    - Bereinigtes DataFrame
    - Liste mit Spaltennamen und Anzahl der entfernten Werte
    """
    if schiff_name not in parameter_dict:
        return df, []

    fehlerhafte_werte = []
    limits = parameter_dict[schiff_name]

    for spalte, grenz in limits.items():
        if spalte in df.columns:
            mask = pd.Series([True] * len(df), index=df.index)  # initial: alles gültig

            # Werte filtern, die außerhalb liegen
            if grenz.get("min") is not None:
                mask &= df[spalte] >= grenz["min"]
            if grenz.get("max") is not None:
                mask &= df[spalte] <= grenz["max"]

            mask = mask.reindex(df.index, fill_value=False)  # sicheres Reindexing

            entfernt = (~mask).sum()
            if entfernt > 0:
                fehlerhafte_werte.append((spalte, entfernt))
                df = df[mask]  # nur gültige Zeilen behalten

    return df, fehlerhafte_werte


# --------------------------------------------------------------------------------------------------
# 🔢 Zahlenformatierung – deutsch (Komma, Tausenderpunkt)
# --------------------------------------------------------------------------------------------------

def format_de(wert, nachkommastellen=2):
    """
    Wandelt einen numerischen Wert ins deutsche Zahlenformat:
    - Komma als Dezimaltrenner
    - Punkt als Tausendertrennzeichen

    Beispiel: 1234.56 → '1.234,56'
    """
    if wert is None or pd.isnull(wert):
        return "-"
    try:
        return f"{wert:,.{nachkommastellen}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "-"


# --------------------------------------------------------------------------------------------------
# ⏳ Zeitdauern (Timedelta) in verschiedenen Formaten darstellen
# --------------------------------------------------------------------------------------------------

def to_hhmmss(td):
    """
    Wandelt eine Zeitdifferenz (Timedelta) in ein klassisches Format hh:mm:ss um.
    
    Beispiel:
    - 4500 Sekunden → '01:15:00'
    """
    try:
        if pd.isnull(td) or td is None:
            return "-"
        total_seconds = int(td.total_seconds())
        h, rem = divmod(total_seconds, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02}:{m:02}:{s:02}"
    except:
        return "-"

def to_dezimalstunden(td):
    """
    Wandelt eine Zeitdifferenz in Stunden mit Dezimalstellen um, deutsch formatiert.

    Beispiel:
    - 4500 Sekunden → '1,250 h'
    """
    try:
        if pd.isnull(td) or td is None:
            return "-"
        val = td.total_seconds() / 3600
        return f"{val:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".") + " h"
    except:
        return "-"

def to_dezimalminuten(td):
    """
    Wandelt eine Zeitdifferenz in ganze Minuten um (als Ganzzahl, deutsch formatiert).

    Beispiel:
    - 4500 Sekunden → '75 min'
    """
    try:
        if pd.isnull(td) or td is None:
            return "-"
        return f"{int(td.total_seconds() // 60):,} min".replace(",", ".")
    except:
        return "-"

def format_dauer(td, zeitformat="dezimalminuten"):
    """
    Wrapper-Funktion: Gibt eine Zeitdifferenz im gewünschten Format zurück.

    Unterstützte Formate:
    - 'hh:mm:ss'
    - 'dezimalstunden'
    - 'dezimalminuten'

    Gibt bei ungültigen Werten einen Bindestrich zurück.
    """
    if td is None or pd.isnull(td):
        return "-"
    if zeitformat == "hh:mm:ss":
        return to_hhmmss(td)
    elif zeitformat == "dezimalstunden":
        return to_dezimalstunden(td)
    elif zeitformat == "dezimalminuten":
        return to_dezimalminuten(td)
    return "-"

def sichere_dauer(start, ende, zeitformat):
    """
    Gibt sicher die Dauer zwischen zwei Zeitpunkten zurück, falls beide vorhanden.

    Falls einer der Zeitpunkte fehlt, wird ein Bindestrich zurückgegeben.
    """
    if pd.notnull(start) and pd.notnull(ende):
        return format_dauer(ende - start, zeitformat)
    return "-"

def sichere_zeit(ts, zeitzone):
    """
    Gibt einen Zeitstempel sicher und formatiert zurück – inkl. Zeitzonenumrechnung.
    
    Beispiel: '13.05.2025 14:12:00'
    """
    if ts is None or pd.isnull(ts):
        return "-"
    return format_time(ts, zeitzone)


# --------------------------------------------------------------------------------------------------
# 🏷️ Spaltennamen dynamisch bilden (z. B. für BB / SB)
# --------------------------------------------------------------------------------------------------

def get_spaltenname(base, seite):
    """
    Erzeugt dynamisch einen oder mehrere Spaltennamen für Backbord/Steuerbord.

    Beispiele:
    - get_spaltenname("Tiefgang_", "BB")       → "Tiefgang_BB"
    - get_spaltenname("Tiefgang_", "BB+SB")    → ["Tiefgang_BB", "Tiefgang_SB"]

    Parameter:
    - base: Spaltenprefix, z. B. "Tiefgang_"
    - seite: "BB", "SB" oder "BB+SB"

    Rückgabe:
    - Einzelner Spaltenname oder Liste mit beiden Seiten
    """
    if base.endswith("_") and seite in ["BB", "SB"]:
        return base + seite
    elif base.endswith("_") and seite == "BB+SB":
        return [base + "BB", base + "SB"]
    return base


# --------------------------------------------------------------------------------------------------
# ⚓ Schiff manuell auswählen, falls nicht automatisch erkannt (z. B. bei HPA-Daten)
# --------------------------------------------------------------------------------------------------

def setze_schiff_manuell_wenn_notwendig(df, st):
    """
    Falls im DataFrame keine Schiffszuordnung vorhanden ist, 
    bietet diese Funktion eine manuelle Auswahl an.

    Parameter:
    - df: Datenframe mit Spalte 'Schiffsname'
    - st: Streamlit-Objekt

    Rückgabe:
    - df mit gesetztem Schiffsname
    - Liste erkannter Schiffe (max. 1)
    """
    if df["Schiffsname"].isna().all():
        schiffsparameter = lade_schiffsparameter()
        moegliche_schiffe = list(schiffsparameter.keys())

        if moegliche_schiffe:
            manueller_schiff = st.sidebar.selectbox("⚓ Schiff (manuelle Auswahl)", moegliche_schiffe)
            df["Schiffsname"] = manueller_schiff
            return df, [manueller_schiff]
        else:
            st.sidebar.warning("⚠️ Keine Schiffsparameter verfügbar.")
            return df, []
    return df, df["Schiffsname"].dropna().unique().tolist()


# --------------------------------------------------------------------------------------------------
# 📄 Datenformat automatisch erkennen anhand erster Zeile
# --------------------------------------------------------------------------------------------------

def erkenne_datenformat(uploaded_files):
    """
    Erkennt automatisch, ob die hochgeladene Datei im MoNa- oder HPA-Format vorliegt.

    Erkennung:
    - MoNa: beginnt mit Datum im Format YYYYMMDD ohne Punkt
    - HPA: enthält z. B. "12.04.2025 04:00:00" (Datum mit Punkt) und Tabs

    Rückgabe:
    - "MoNa", "HPA" oder "Unbekannt"
    """
    first_file = uploaded_files[0]
    try:
        content = first_file.getvalue().decode("utf-8", errors="ignore")
    except UnicodeDecodeError:
        content = first_file.getvalue().decode("latin-1", errors="ignore")
    
    # Steuerzeichen entfernen
    lines = content.splitlines()
    cleaned_lines = [line.strip("\x02").strip("\x03").strip() for line in lines if line.strip()]
    if not cleaned_lines:
        return "Unbekannt"
    
    first_line = cleaned_lines[0]

    if "." in first_line[:10] and "\t" in first_line:
        return "HPA"
    elif first_line[:8].isdigit():
        return "MoNa"
    else:
        return "Unbekannt"


# --------------------------------------------------------------------------------------------------
# 🧾 Schiffsname aus Dateinamen ableiten (z. B. bei HPA-Dateien)
# --------------------------------------------------------------------------------------------------

def erkenne_schiff_aus_dateiname(uploaded_files):
    """
    Versucht, den Schiffsnamen aus dem Dateinamen abzuleiten.

    Beispiel:
    - Datei: "250418_utc_ijsseldelta.txt" → Schiff: "TSHD IJSSELDELTA"

    Rückgabe:
    - Schiffname (str) oder None
    """
    dateiname = uploaded_files[0].name.lower()
    schiffe = {
        "ijsseldelta": "TSHD IJSSELDELTA",
        "anke": "TSHD ANKE",
        "maasmond": "WID MAASMOND",
        "jan": "WID JAN",
        "akk": "WID AKKE",
        "aquadelta": "WID AQUADELTA",
        "ecodelta": "TSHD ECODELTA",
        "hein": "TSHD HEIN",
        "pieter_hubert":"TSHD PIETER HUBERT"
    }
    for key, name in schiffe.items():
        if key in dateiname:
            return name
    return None

        
    
