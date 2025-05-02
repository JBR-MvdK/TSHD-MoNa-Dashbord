import streamlit as st
import pandas as pd
from TSHD_MoNa_Dashbord import format_time

def zeige_umlauf_uebersicht(
    df_umlauf: pd.DataFrame,
    row: pd.Series,
    werte: dict,
    tds_werte: dict,
    strecken: dict,
    zeitzone: str,
    strategie: dict,
    debug_info: list,
    pf: float,
    pw: float,
    pb: float,
    zeitformat: str
):
    """
    Zeigt einen kombinierten Überblick über den gewählten Umlauf:
    Headerinformationen, Zeitphasen, Grafik, Baggerwerte und Strecken.
    """

    # 1. Headerinformationen
    st.markdown("### 🛥️ Umlauf-Überblick")
    col1, col2 = st.columns(2)
    col1.markdown(f"**Startzeit:** {format_time(row.get('Start Leerfahrt'), zeitzone)}")
    col2.markdown(f"**Endzeit:** {format_time(row.get('Ende'), zeitzone)}")

    st.divider()

    # 2. Statuszeiten im Umlauf
    st.markdown("### ⏱ Statuszeiten im Umlauf")
    # → Hier ggf. deine Panels von Tab 5 einfügen

    # 3. Prozessdaten-Grafik (eingebettet aus vorherigem Plotly-Diagramm)
    st.markdown("### 📈 Umlaufgrafik – Prozessdaten")
    # → Übergib ggf. bereits vorbereitete `fig` oder baue es hier nach Wunsch

    # 4. Baggerwerte im Umlauf (Masse, Volumen etc.)
    st.markdown("### ⚖️ Baggerwerte im Umlauf")
    # → Hier Panels für Masse, Volumen, Feststoffe usw. einfügen

    # 5. Streckenanzeige
    st.markdown("### 📍 Strecken im Umlauf")
    # → Darstellung von Leerfahrt, Baggern etc.

    # Optional: Debug/Strategiewerte
    with st.expander("🛠️ Debug-Infos & Strategie"):
        st.write(strategie)
        for zeile in debug_info:
            st.markdown(zeile)

