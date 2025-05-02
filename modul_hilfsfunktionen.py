# ==================================================================================================
# 🔧 Allgemeine Hilfsfunktionen für Zeitreihen, Zeitdauern, Zeitzonen, Formatierung & Parameterprüfung
# ==================================================================================================

import pandas as pd
import pytz
import os
import json
import streamlit as st

# --------------------------------------------------------------------------------------------------
# 📋 DataFrame-Hilfsfunktionen
# --------------------------------------------------------------------------------------------------

def split_by_gap(df, max_gap_minutes=2):
    """
    Teilt ein DataFrame anhand von Zeitlücken (Gaps) in Segmente.

    Parameter:
    - df: DataFrame mit Zeitstempelspalte ('timestamp')
    - max_gap_minutes: maximale zulässige Lücke (in Minuten), bevor neuer Abschnitt beginnt

    Rückgabe:
    - df mit zusätzlicher 'segment'-Spalte für Gruppierung
    """
    df = df.sort_values(by="timestamp")
    df["gap"] = df["timestamp"].diff().dt.total_seconds() > (max_gap_minutes * 60)
    df["segment"] = df["gap"].cumsum()
    return df


# --------------------------------------------------------------------------------------------------
# 🕒 Zeit- und Zeitzonenfunktionen
# --------------------------------------------------------------------------------------------------

def convert_timestamp(ts, zeitzone):
    """
    Konvertiert einen Zeitstempel in die gewünschte Zeitzone.

    - UTC: bleibt oder wird zu UTC
    - Lokal: wird zu Europe/Berlin umgerechnet

    Gibt:
    - neuen Zeitstempel mit Zeitzone
    """
    if ts is None or pd.isnull(ts):
        return None
    if zeitzone == "UTC":
        return ts.tz_localize("UTC") if ts.tzinfo is None else ts.astimezone(pytz.UTC)
    elif zeitzone == "Lokal (Europe/Berlin)":
        return ts.tz_localize("UTC").astimezone(pytz.timezone("Europe/Berlin")) if ts.tzinfo is None else ts.astimezone(pytz.timezone("Europe/Berlin"))
    return ts

def format_time(ts, zeitzone):
    """
    Gibt einen Zeitstempel formatiert als String 'DD.MM.YYYY HH:MM:SS' zurück.
    Berücksichtigt gewählte Zeitzone.
    """
    ts_conv = convert_timestamp(ts, zeitzone)
    return "-" if ts_conv is None or pd.isnull(ts_conv) else ts_conv.strftime("%d.%m.%Y %H:%M:%S")

def plot_x(df, mask, zeitzone):
    """
    Gibt Zeitachse für Plotly zurück – abhängig von gewählter Zeitzone.
    """
    col = "timestamp"
    if zeitzone == "Lokal (Europe/Berlin)":
        return df.loc[mask, col].dt.tz_convert("Europe/Berlin")
    return df.loc[mask, col]


# --------------------------------------------------------------------------------------------------
# ⚙️ Schiffsspezifische Parameterfunktionen (z. B. für Plausibilitätsfilterung)
# --------------------------------------------------------------------------------------------------

def lade_schiffsparameter(pfad="schiffsparameter.json"):
    """
    Lädt die Schiffsparameterdatei (JSON) mit Min/Max-Grenzen für Sensorwerte.

    Rückgabe:
    - Dictionary {schiff_name: {parameter: {min, max}}}
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
    Wendet Min/Max-Grenzen aus schiffsparameter.json an und filtert ungültige Werte heraus.

    Rückgabe:
    - bereinigter DataFrame
    - Liste der betroffenen Spalten mit Anzahl gelöschter Werte
    """
    if schiff_name not in parameter_dict:
        return df, []

    fehlerhafte_werte = []
    limits = parameter_dict[schiff_name]

    for spalte, grenz in limits.items():
        if spalte in df.columns:
            mask = pd.Series([True] * len(df))
            if grenz.get("min") is not None:
                mask &= df[spalte] >= grenz["min"]
            if grenz.get("max") is not None:
                mask &= df[spalte] <= grenz["max"]
            entfernt = (~mask).sum()
            if entfernt > 0:
                fehlerhafte_werte.append((spalte, entfernt))
                df = df[mask]

    return df, fehlerhafte_werte


# --------------------------------------------------------------------------------------------------
# 🔢 Zahlenformatierung – deutsch (Komma, Tausenderpunkt)
# --------------------------------------------------------------------------------------------------

def format_de(wert, nachkommastellen=2):
    """
    Wandelt eine Zahl ins deutsche Format mit , als Dezimaltrenner und . als Tausenderpunkt.
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
    """Format: hh:mm:ss"""
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
    """Format: 1,250 h (mit Komma, drei Nachkommastellen)"""
    try:
        if pd.isnull(td) or td is None:
            return "-"
        val = td.total_seconds() / 3600
        return f"{val:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".") + " h"
    except:
        return "-"

def to_dezimalminuten(td):
    """Format: 75 min (als ganze Minuten)"""
    try:
        if pd.isnull(td) or td is None:
            return "-"
        return f"{int(td.total_seconds() // 60):,} min".replace(",", ".")
    except:
        return "-"

def format_dauer(td, zeitformat="dezimalminuten"):
    """
    Wrapper: Wandelt Timedelta in gewähltes Format ('hh:mm:ss', 'dezimalstunden', 'dezimalminuten')
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
    Gibt die Dauer zwischen zwei Timestamps sicher zurück (robust gegen None oder NaT).
    """
    if pd.notnull(start) and pd.notnull(ende):
        return format_dauer(ende - start, zeitformat)
    return "-"

def sichere_zeit(ts, zeitzone):
    """
    Gibt einen Zeitstempel formatiert zurück (robust gegen None/NaT).
    """
    if ts is None or pd.isnull(ts):
        return "-"
    return format_time(ts, zeitzone)


# --------------------------------------------------------------------------------------------------
# 🏷️ Spaltennamen dynamisch bilden (z. B. für BB / SB)
# --------------------------------------------------------------------------------------------------

def get_spaltenname(base, seite):
    """
    Erzeugt den passenden Spaltennamen für einen Messwert (z. B. 'Tiefgang_' + 'BB').

    Rückgabe:
    - bei 'BB+SB': Liste mit beiden Seiten
    - sonst: einzelner Spaltenname
    """
    if base.endswith("_") and seite in ["BB", "SB"]:
        return base + seite
    elif base.endswith("_") and seite == "BB+SB":
        return [base + "BB", base + "SB"]
    return base
