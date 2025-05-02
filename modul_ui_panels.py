import streamlit as st
from modul_hilfsfunktionen import format_time, sichere_dauer, format_de

# =================================================================================================
# 📊 Anzeige-Funktionen für Tab5 (Panels mit Zeiten, Mengen, Strecken, Feldern etc.)
# =================================================================================================

# -------------------------------------------------------------------------------------------------
# ⏱ Statuszeiten (Leerfahrt, Baggern, Vollfahrt, Verbringen, Umlaufdauer)
# -------------------------------------------------------------------------------------------------

def zeige_statuszeiten_panels(row, zeitzone, zeitformat, panel_template):
    """
    Zeigt fünf Panels für Statuszeiten an: Leerfahrt, Baggern, Vollfahrt, Verbringen, Umlaufdauer.
    
    Parameter:
    - row: eine Zeile aus umlauf_info_df (mit Zeitangaben)
    - zeitzone: gewählte Zeitzone
    - zeitformat: Format der Daueranzeige (z. B. hh:mm:ss)
    - panel_template: HTML-Vorlage für Panels
    """

    # Dauerwerte berechnen
    dauer_leerfahrt_disp   = sichere_dauer(row.get("Start Leerfahrt"), row.get("Start Baggern"), zeitformat)
    dauer_baggern_disp     = sichere_dauer(row.get("Start Baggern"), row.get("Start Vollfahrt"), zeitformat)
    dauer_vollfahrt_disp   = sichere_dauer(row.get("Start Vollfahrt"), row.get("Start Verklappen/Pump/Rainbow"), zeitformat)
    dauer_verbringen_disp  = sichere_dauer(row.get("Start Verklappen/Pump/Rainbow"), row.get("Ende"), zeitformat)
    dauer_umlauf_disp      = sichere_dauer(row.get("Start Leerfahrt"), row.get("Ende"), zeitformat)

    # Darstellung in 5 Spalten
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.markdown(panel_template.format(
        caption="Leerfahrt",
        value=dauer_leerfahrt_disp,
        change_label1="Startzeit:", change_value1=format_time(row.get("Start Leerfahrt"), zeitzone),
        change_label2="Endzeit:",   change_value2=format_time(row.get("Start Baggern"), zeitzone)
    ), unsafe_allow_html=True)

    col2.markdown(panel_template.format(
        caption="Baggern",
        value=dauer_baggern_disp,
        change_label1="Startzeit:", change_value1=format_time(row.get("Start Baggern"), zeitzone),
        change_label2="Endzeit:",   change_value2=format_time(row.get("Start Vollfahrt"), zeitzone)
    ), unsafe_allow_html=True)

    col3.markdown(panel_template.format(
        caption="Vollfahrt",
        value=dauer_vollfahrt_disp,
        change_label1="Startzeit:", change_value1=format_time(row.get("Start Vollfahrt"), zeitzone),
        change_label2="Endzeit:",   change_value2=format_time(row.get("Start Verklappen/Pump/Rainbow"), zeitzone)
    ), unsafe_allow_html=True)

    col4.markdown(panel_template.format(
        caption="Verbringen",
        value=dauer_verbringen_disp,
        change_label1="Startzeit:", change_value1=format_time(row.get("Start Verklappen/Pump/Rainbow"), zeitzone),
        change_label2="Endzeit:",   change_value2=format_time(row.get("Ende"), zeitzone)
    ), unsafe_allow_html=True)

    col5.markdown(panel_template.format(
        caption="Umlaufdauer",
        value=dauer_umlauf_disp,
        change_label1="Startzeit:", change_value1=format_time(row.get("Start Leerfahrt"), zeitzone),
        change_label2="Endzeit:",   change_value2=format_time(row.get("Ende"), zeitzone)
    ), unsafe_allow_html=True)


# -------------------------------------------------------------------------------------------------
# 📦 Baggerwerte (Masse, Volumen, Feststoff, Dichte, Bodenvolumen)
# -------------------------------------------------------------------------------------------------

def zeige_baggerwerte_panels(kennzahlen, tds_werte, zeitzone, pw, pf, pb, panel_template, dichte_panel_template):
    """
    Zeigt fünf Panels für Baggerwerte an: Masse, Volumen, Feststoffmasse, Bodenvolumen, Dichte.

    Parameter:
    - kennzahlen: Dict mit Start/End-Werten und Differenzen
    - tds_werte: Dict mit TDS-Berechnungen
    - pw, pf, pb: Dichten Wasser, Feststoff, Boden
    - Templates für HTML
    """
    if not kennzahlen:
        return

    col6, col7, col8, col9, col10 = st.columns(5)

    col6.markdown(panel_template.format(
        caption="Ladungsmasse",
        value=format_de(kennzahlen.get("delta_verdraengung"), 0) + " t",
        change_label1="leer:", change_value1=format_de(kennzahlen.get("verdraengung_leer"), 0) + " t",
        change_label2="voll:", change_value2=format_de(kennzahlen.get("verdraengung_voll"), 0) + " t"
    ), unsafe_allow_html=True)

    col7.markdown(panel_template.format(
        caption="Ladungsvolumen",
        value=format_de(kennzahlen.get("delta_volumen"), 0) + " m³" if kennzahlen.get("delta_volumen") is not None else "-",
        change_label1="leer:", change_value1=format_de(kennzahlen.get("volumen_leer"), 0) + " m³" if kennzahlen.get("volumen_leer") is not None else "-",
        change_label2="voll:", change_value2=format_de(kennzahlen.get("volumen_voll"), 0) + " m³" if kennzahlen.get("volumen_voll") is not None else "-"
    ), unsafe_allow_html=True)

    col8.markdown(panel_template.format(
        caption="Feststoffmasse",
        value=format_de(tds_werte.get("feststoffmasse"), 0) + " t" if tds_werte.get("feststoffmasse") is not None else "-",
        change_label1="Volumen:", change_value1=format_de(tds_werte.get("feststoffvolumen"), 0) + " m³" if tds_werte.get("feststoffvolumen") is not None else "-",
        change_label2="Konzentration:", change_value2=f"{tds_werte.get('feststoffkonzentration'):.1%}".replace(".", ",") if tds_werte.get("feststoffkonzentration") is not None else "-"
    ), unsafe_allow_html=True)

    col9.markdown(panel_template.format(
        caption="Bodenvolumen",
        value=format_de(tds_werte.get("bodenvolumen"), 0) + " m³" if tds_werte.get("bodenvolumen") is not None else "-",
        change_label1="Bodendichte:", change_value1=f"{pb:.3f}".replace(".", ",") + " t/m³",
        change_label2="", change_value2=""
    ), unsafe_allow_html=True)

    ladungsdichte_disp = format_de(tds_werte.get("ladungsdichte"), 2) if tds_werte.get("ladungsdichte") is not None else "-"
    col10.markdown(dichte_panel_template.format(
        caption="Dichte",
        pw=f"{pw:.3f}".replace(".", ","), pf=f"{pf:.3f}".replace(".", ","), pl=ladungsdichte_disp
    ), unsafe_allow_html=True)


# -------------------------------------------------------------------------------------------------
# 🛤 Strecken- und Zeitangaben je Phase
# -------------------------------------------------------------------------------------------------

def zeige_strecken_panels(
    strecke_leer_disp, strecke_baggern_disp, strecke_vollfahrt_disp,
    strecke_verbringen_disp, strecke_gesamt_disp,
    dauer_leerfahrt_disp, dauer_baggern_disp, dauer_vollfahrt_disp,
    dauer_verbringen_disp, dauer_umlauf_disp,
    strecken_panel_template
):
    """
    Zeigt fünf Panels für Strecken und zugehörige Dauern.
    """

    col_st1, col_st2, col_st3, col_st4, col_st5 = st.columns(5)

    col_st1.markdown(strecken_panel_template.format(
        caption="Leerfahrt", value=f"{strecke_leer_disp} km", dauer=dauer_leerfahrt_disp
    ), unsafe_allow_html=True)

    col_st2.markdown(strecken_panel_template.format(
        caption="Baggern", value=f"{strecke_baggern_disp} km", dauer=dauer_baggern_disp
    ), unsafe_allow_html=True)

    col_st3.markdown(strecken_panel_template.format(
        caption="Vollfahrt", value=f"{strecke_vollfahrt_disp} km", dauer=dauer_vollfahrt_disp
    ), unsafe_allow_html=True)

    col_st4.markdown(strecken_panel_template.format(
        caption="Verbringen", value=f"{strecke_verbringen_disp} km", dauer=dauer_verbringen_disp
    ), unsafe_allow_html=True)

    col_st5.markdown(strecken_panel_template.format(
        caption="Gesamt", value=f"{strecke_gesamt_disp} km", dauer=dauer_umlauf_disp
    ), unsafe_allow_html=True)


# -------------------------------------------------------------------------------------------------
# 🗂 Anzeige der Polygon-Namen (Bagger- und Verbringfelder)
# -------------------------------------------------------------------------------------------------

def zeige_bagger_und_verbringfelder(bagger_namen, verbring_namen):
    """
    Zeigt Bagger- und Verbringfeldnamen nebeneinander als gelayoutete Blöcke.
    """
    col_feld1, col_feld2 = st.columns([1, 1])

    with col_feld1:
        st.markdown("**Baggerfelder**")
        if len(bagger_namen) > 0:
            for name in sorted(bagger_namen):
                st.markdown(f"""<div style='
                    background: #f4f8fc;
                    border-radius: 8px;
                    padding: 6px 10px;
                    margin-bottom: 6px;
                    font-size: 0.95rem;
                    color: #222;'>{name}</div>""", unsafe_allow_html=True)
        else:
            st.markdown("keine Polygone eingeladen")

    with col_feld2:
        st.markdown("**Verbringfelder**")
        if len(verbring_namen) > 0:
            for name in sorted(verbring_namen):
                st.markdown(f"""<div style='
                    background: #f4f8fc;
                    border-radius: 8px;
                    padding: 6px 10px;
                    margin-bottom: 6px;
                    font-size: 0.95rem;
                    color: #222;'>{name}</div>""", unsafe_allow_html=True)
        else:
            st.markdown(" ")
