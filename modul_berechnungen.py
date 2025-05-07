import pandas as pd
from modul_strecken import berechne_strecken
from modul_startend_strategie import berechne_start_endwerte
from modul_hilfsfunktionen import sichere_dauer


# ------------------------------------------------------------
# 🧮 TDS-Berechnung basierend auf 4 Start/End-Werten
# ------------------------------------------------------------
def berechne_tds_aus_werte(verd_leer, verd_voll, vol_leer, vol_voll, pf, pw, pb):
    if None in [verd_leer, verd_voll, vol_leer, vol_voll]:
        return {k: None for k in [
            "ladungsmasse", "ladungsvolumen", "ladungsdichte", "feststoffkonzentration",
            "feststoffvolumen", "feststoffmasse", "bodenvolumen"
        ]}
    ladungsmasse = verd_voll - verd_leer
    ladungsvolumen = vol_voll - vol_leer
    ladungsdichte = ladungsmasse / ladungsvolumen if ladungsvolumen else None
    feststoffkonzentration = (ladungsdichte - pw) / (pf - pw) if ladungsdichte else None
    feststoffvolumen = feststoffkonzentration * ladungsvolumen if feststoffkonzentration else None
    feststoffmasse = feststoffvolumen * pf if feststoffvolumen else None
    bodenvolumen = ((pf - pw) / (pf * (pb - pw))) * feststoffmasse if feststoffmasse and pb else None
    return {
        "ladungsmasse": ladungsmasse,
        "ladungsvolumen": ladungsvolumen,
        "ladungsdichte": ladungsdichte,
        "feststoffkonzentration": feststoffkonzentration,
        "feststoffvolumen": feststoffvolumen,
        "feststoffmasse": feststoffmasse,
        "bodenvolumen": bodenvolumen
    }
    
    
def berechne_umlauf_auswertung(df, row, schiffsparameter, strategie, pf, pw, pb, zeitformat, epsg_code):
    """
    Vollständige Auswertung eines Umlaufs:
    - Filtert Daten auf den Zeitbereich des Umlaufs
    - Ermittelt Start-/Endwerte nach Strategie
    - Berechnet TDS-Kennzahlen (Volumen, Masse, Konzentration usw.)
    - Misst Strecken (Leerfahrt, Baggern, Verbringen)
    - Liefert formatierte Werte für UI
    """

    # ------------------------------------------------------------
    # 🕓 Zeitbereich definieren und sicherstellen, dass alles timezone-aware ist
    # ------------------------------------------------------------
    t_start = pd.to_datetime(row["Start Leerfahrt"])
    t_ende = pd.to_datetime(row["Ende"])
    if t_start.tzinfo is None:
        t_start = t_start.tz_localize("UTC")
    if t_ende.tzinfo is None:
        t_ende = t_ende.tz_localize("UTC")
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")

    # Filtere DataFrame auf den gewählten Umlaufzeitraum
    df_umlauf = df[(df["timestamp"] >= t_start) & (df["timestamp"] <= t_ende)]

    # ------------------------------------------------------------
    # 📍 Aktive Polygone extrahieren (für Info-Ausgabe)
    # ------------------------------------------------------------
    bagger_namen = df_umlauf[df_umlauf["Status"] == 2]["Polygon_Name"].dropna().unique()
    verbring_namen = df_umlauf[df_umlauf["Status"].isin([4, 5, 6])]["Polygon_Name"].dropna().unique()

  
    # ------------------------------------------------------------
    # 🔍 Strategieauswertung nur, wenn nötige Spalten existieren
    # ------------------------------------------------------------
    if "Verdraengung" in df_umlauf.columns and "Ladungsvolumen" in df_umlauf.columns:
        werte, debug_info = berechne_start_endwerte(df_umlauf, strategie, df_gesamt=df)
        tds_werte = berechne_tds_aus_werte(
            werte.get("Verdraengung Start"),
            werte.get("Verdraengung Ende"),
            werte.get("Ladungsvolumen Start"),
            werte.get("Ladungsvolumen Ende"),
            pf, pw, pb
        )
    else:
        werte = {
            "Verdraengung Start": None, "Verdraengung Ende": None,
            "Ladungsvolumen Start": None, "Ladungsvolumen Ende": None
        }
        tds_werte = berechne_tds_aus_werte(None, None, None, None, pf, pw, pb)
        debug_info = ["⚠️ Spalten fehlen – keine Strategieauswertung möglich."]

    # ------------------------------------------------------------
    # 📦 Ableitung einfacher Differenzkennzahlen
    # ------------------------------------------------------------
    kennzahlen = {
        "verdraengung_leer": werte.get("Verdraengung Start"),
        "verdraengung_voll": werte.get("Verdraengung Ende"),
        "volumen_leer": werte.get("Ladungsvolumen Start"),
        "volumen_voll": werte.get("Ladungsvolumen Ende"),
    }
    kennzahlen["delta_verdraengung"] = (
        werte.get("Verdraengung Ende") - werte.get("Verdraengung Start")
        if None not in [werte.get("Verdraengung Start"), werte.get("Verdraengung Ende")] else None
    )
    kennzahlen["delta_volumen"] = (
        werte.get("Ladungsvolumen Ende") - werte.get("Ladungsvolumen Start")
        if None not in [werte.get("Ladungsvolumen Start"), werte.get("Ladungsvolumen Ende")] else None
    )

    # ------------------------------------------------------------
    # 📏 Streckenberechnung (inkl. 15 min Vorlauf, falls Startpunkt verfehlt)
    # ------------------------------------------------------------
    df_umlauf_ext = df[(df["timestamp"] >= (t_start - pd.Timedelta("15min"))) & (df["timestamp"] <= t_ende)]
    strecken = berechne_strecken(df_umlauf_ext, "RW_Schiff", "HW_Schiff", "Status", epsg_code)

    # Formatierung für die Anzeige (z. B. km mit Komma)
    def format_km(val):
        return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if val is not None else "-"

    strecke_disp = {
        "leerfahrt": format_km(strecken.get("leerfahrt")),
        "baggern": format_km(strecken.get("baggern")),
        "vollfahrt": format_km(strecken.get("vollfahrt")),
        "verbringen": format_km(strecken.get("verbringen")),
        "gesamt": format_km(sum(v for v in strecken.values() if v is not None))
    }

    # ------------------------------------------------------------
    # ⏱ Dauerberechnung der einzelnen Phasen (formatiert fürs UI)
    # ------------------------------------------------------------
    dauer_disp = {
        "leerfahrt": sichere_dauer(row.get("Start Leerfahrt"), row.get("Start Baggern"), zeitformat),
        "baggern": sichere_dauer(row.get("Start Baggern"), row.get("Start Vollfahrt"), zeitformat),
        "vollfahrt": sichere_dauer(row.get("Start Vollfahrt"), row.get("Start Verklappen/Pump/Rainbow"), zeitformat),
        "verbringen": sichere_dauer(row.get("Start Verklappen/Pump/Rainbow"), row.get("Ende"), zeitformat),
        "umlauf": sichere_dauer(row.get("Start Leerfahrt"), row.get("Ende"), zeitformat),
    }

    # ------------------------------------------------------------
    # 🔁 Rückgabe aller relevanten Werte
    # ------------------------------------------------------------
    return (
        tds_werte, werte, kennzahlen, strecken,
        strecke_disp, dauer_disp, debug_info,
        bagger_namen, verbring_namen
    )

# 🔚 Modulexport (optional, aber korrekt)
__all__ = ["berechne_tds_aus_werte", "berechne_umlauf_auswertung"]

