import streamlit as st

def reset_layer_toggle_state():
    """Setzt alle Layer-Toggle-Keys im Session State zurück."""
    keys = [
        "s1_b", "s2_b", "s3_b", "s456_b",
        "s1_v", "s2_v", "s3_v", "s456_v"
    ]
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]

def zeige_layer_steuerung(umlauf_auswahl: str) -> tuple:
    """
    Zeigt einen Expander mit Layersteuerung für zwei Karten (Baggern & Verbringen),
    umschaltbar zwischen Automatisch und Manuell.

    Die Funktion verwaltet den Moduswechsel und setzt bei Bedarf den Session State zurück.

    Rückgabe:
        - 8 Layer-Booleans
        - auto_modus_aktiv (True, wenn "Automatisch")
    """

    with st.sidebar.expander("🗺️ Kartenlayer-Steuerung"):
        # Interner Modusumschalter mit Reset-Logik
        aktueller_modus = st.radio("Steuerungsmodus", ["Automatisch", "Manuell"], horizontal=True, key="layer_modus_radio")
        letzter_modus = st.session_state.get("layer_modus")

        if letzter_modus != aktueller_modus:
            reset_layer_toggle_state()
            st.session_state.layer_modus = aktueller_modus

        auto_modus_aktiv = aktueller_modus == "Automatisch"
        ist_einzel_umlauf = umlauf_auswahl != "Alle"

        layer_namen = ["Leerfahrt", "Baggern", "Vollfahrt", "Verbringen"]

        def fake_toggle(label: str, value: bool):
            icon = "✅" if value else "❌"
            st.markdown(f"{icon} {label}")

        col_label, col_b, col_v = st.columns([1.2, 1, 1])

        with col_label:
            st.markdown("**Layer**")
            for name in layer_namen:
                st.markdown(name)

        if auto_modus_aktiv:
            # Automatische Logik
            if ist_einzel_umlauf:
                show_status1_b = show_status2_b = show_status3_b = show_status456_b = True
                show_status1_v = show_status2_v = show_status3_v = show_status456_v = True
            else:
                show_status1_b = False
                show_status2_b = True
                show_status3_b = False
                show_status456_b = False

                show_status1_v = False
                show_status2_v = False
                show_status3_v = False
                show_status456_v = True

            with col_b:
                st.markdown("**Baggern**")
                fake_toggle("", show_status1_b)
                fake_toggle("", show_status2_b)
                fake_toggle("", show_status3_b)
                fake_toggle("", show_status456_b)

            with col_v:
                st.markdown("**Verbringen**")
                fake_toggle("", show_status1_v)
                fake_toggle("", show_status2_v)
                fake_toggle("", show_status3_v)
                fake_toggle("", show_status456_v)

        else:
            with col_b:
                st.markdown("**Baggern**")
                show_status1_b = st.toggle("", value=False, key="s1_b")
                show_status2_b = st.toggle("", value=True, key="s2_b")
                show_status3_b = st.toggle("", value=False, key="s3_b")
                show_status456_b = st.toggle("", value=True, key="s456_b")

            with col_v:
                st.markdown("**Verbringen**")
                show_status1_v = st.toggle("", value=False, key="s1_v")
                show_status2_v = st.toggle("", value=True, key="s2_v")
                show_status3_v = st.toggle("", value=False, key="s3_v")
                show_status456_v = st.toggle("", value=True, key="s456_v")

    return (
        show_status1_b, show_status2_b, show_status3_b, show_status456_b,
        show_status1_v, show_status2_v, show_status3_v, show_status456_v,
        auto_modus_aktiv
    )
