# === Funktion: erkenne_koordinatensystem(df, st, sidebar) ====================================================================
def erkenne_koordinatensystem(df, st=None, sidebar=None):
    """
    Erkennt automatisch das verwendete Koordinatensystem anhand der RW_Schiff- und HW_Schiff-Werte.

    Parameter:
    - df : Pandas DataFrame mit den MoNa-Daten
    - st : Optional, Streamlit-Element für Statusmeldungen
    - sidebar : Optional, Streamlit-Element für Auswahlmöglichkeiten in der Sidebar (falls automatische Erkennung fehlschlägt)

    Rückgabe:
    - proj_system : erkannter Name des Koordinatensystems ("UTM", "Gauß-Krüger" oder "RD")
    - epsg_code : zugehöriger EPSG-Code als String (z.B. "EPSG:25832")
    - auto_erkannt : True, wenn das Koordinatensystem automatisch erkannt werden konnte
    """

    # --- Bestimme die maximalen Rechts- und Hochwerte ---
    rw_max = df["RW_Schiff"].dropna().astype(float).max()
    hw_max = df["HW_Schiff"].dropna().astype(float).max()

    # --- Initialisierung der Rückgabewerte ---
    proj_system = None
    epsg_code = None
    auto_erkannt = False

    # --- Regeln für automatische Erkennung ---
    if rw_max > 30_000_000:
        # Vermutlich UTM: Zone aus RW ableiten (erste zwei Stellen)
        erkannte_zone = str(int(rw_max))[:2]
        proj_system = "UTM"
        epsg_code = f"EPSG:258{erkannte_zone}"
        auto_erkannt = True

    elif 2_000_000 < rw_max < 5_000_000:
        # Vermutlich Gauß-Krüger (GK): Zone aus erster Stelle ableiten
        zone = str(int(rw_max))[0]
        proj_system = "Gauß-Krüger"
        epsg_code = f"EPSG:3146{zone}"
        auto_erkannt = True

    elif 150_000 < rw_max < 300_000 and 300_000 < hw_max < 620_000:
        # Vermutlich RD-Koordinaten (Niederlande)
        proj_system = "RD"
        epsg_code = "EPSG:28992"
        auto_erkannt = True

    # --- Statusmeldung (optional, falls st übergeben wird) ---
    if st:  # z.B. st.empty() für Textanzeige
        if auto_erkannt:
            st.success(f"Automatisch erkannt: {proj_system} ({epsg_code})")
        else:
            st.warning("Koordinatensystem konnte nicht sicher erkannt werden.")

    # --- Manuelle Auswahl (optional, falls sidebar übergeben wird) ---
    if sidebar:
        if not auto_erkannt:
            # Benutzer soll Koordinatensystem auswählen
            proj_system = sidebar.selectbox("Bitte Koordinatensystem auswählen", ["UTM", "Gauß-Krüger", "RD (Niederlande)"])
            if proj_system == "UTM":
                utm_zone = sidebar.selectbox("UTM-Zone", ["31", "32", "33", "34"], index=1)
                epsg_code = f"EPSG:258{utm_zone}"
            elif proj_system == "Gauß-Krüger":
                gk_zone = sidebar.selectbox("GK-Zone", ["2", "3", "4", "5"], index=1)
                epsg_code = f"EPSG:3146{gk_zone}"
            elif proj_system == "RD (Niederlande)":
                epsg_code = "EPSG:28992"

    return proj_system, epsg_code, auto_erkannt
