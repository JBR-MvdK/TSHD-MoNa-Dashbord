import streamlit as st
from modul_hilfsfunktionen import format_time, sichere_dauer, format_de
from modul_polygon_auswertung import berechne_punkte_und_zeit

# =================================================================================================
# 📊 Anzeige-Funktionen für Tab5 (Panels mit Zeiten, Mengen, Strecken, Feldern etc.)
# =================================================================================================
# modul_ui_templates.py

# 💠 Allgemeines KPI-Panel – z. B. Umlaufdauer, Verdrängung, Volumen
panel_template = """
<div style="
    background:#f7fafe;
    border-radius: 16px;
    padding: 14px 16px 10px 16px;
    margin-bottom: 1.2rem;
    min-width: 210px;
    min-height: 85px;
    display: flex;
    flex-direction: column;
    justify-content: center;
">
    <div style="font-size:1rem; color:#555; margin-bottom:3px;">{caption}</div>
    <div style="font-size:2.1rem; font-weight:800; color:#222; line-height:1;">
        {value}
    </div>
    <div style="font-size:0.95rem; color:#4e6980; margin-top:3px;">
        <span style="font-weight:600;">{change_label1}</span> {change_value1}<br>
        <span style="font-weight:600;">{change_label2}</span> {change_value2}
    </div>
</div>
"""

# 💠 Strecken-Panel
strecken_panel_template = """
<div style="
    background:#f7fafe;
    border-radius: 16px;
    padding: 14px 16px 10px 16px;
    margin-bottom: 1.2rem;
    min-width: 140px;
    min-height: 65px;
    display: flex;
    flex-direction: column;
    justify-content: center;
">
    <div style="font-size:1rem; color:#555; margin-bottom:3px;">{caption}</div>
    <div style="font-size:2.1rem; font-weight:800; color:#222; line-height:1;">
        {value}
    </div>
    <div style="font-size:0.95rem; color:#4e6980; margin-top:3px;">
        <span style="font-weight:500;">Dauer:</span> {dauer}
    </div>
</div>
"""

# 💠 Dichte-Panel
dichte_panel_template = """
<div style="
    background:#f7fafe;
    border-radius: 16px;
    padding: 14px 16px;
    margin-bottom: 1.2rem;
    min-width: 200px;
    min-height: 100px;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
">
    <div style="font-size:1rem; color:#555; margin-bottom:6px;">{caption}</div>
    <div style="font-size:0.95rem; color:#333;">
        <strong>Wasser:</strong> {pw} t/m³<br>
        <strong>Feststoff:</strong> {pf} t/m³<br>
        <strong>Ladung:</strong> {pl} t/m³
    </div>
</div>
"""

# 💠 Feld-Panel
feld_panel_template = """
<div style="
    background:#f7fafe;
    border-radius: 16px;
    padding: 14px 16px 10px 16px;
    margin-bottom: 1.2rem;
    min-height: 80px;
    display: flex;
    flex-direction: column;
    justify-content: center;
">
    <div style="font-size:1rem; color:#555; margin-bottom:6px;">{caption}</div>
    <div style="font-size:1.05rem; color:#222; line-height:1.4;">
        {content}
    </div>
</div>
"""

status_panel_template_mit_strecke = """
<div style="
    background:#f4f8fc;
    border-radius: 16px;
    padding: 14px 16px 10px 16px;
    margin-bottom: 1.2rem;
    min-width: 210px;
    display: flex;
    flex-direction: column;
    justify-content: center;
">
    <div style="font-size:1rem; color:#555; margin-bottom:3px;">{caption}</div>
    <div style="font-size:2.1rem; font-weight:800; color:#222; line-height:1;">
        {dauer}
    </div>
    <div style="font-size:0.95rem; color:#4e6980; margin-top:3px;">
        <span style="font-weight:600;">Startzeit:</span> {startzeit}<br>
        <span style="font-weight:600;">Endzeit:</span> {endzeit}<br>
        <span style="font-weight:600;">Strecke:</span> {strecke} km
    </div>
</div>
"""



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
        caption="Ladungsdichte",
        value=format_de(tds_werte.get("ladungsdichte"), 3) + " t/m³" if tds_werte.get("ladungsdichte") is not None else "-",
        change_label1="Wasser:", change_value1=f"{pw:.3f}".replace(".", ",") + " t/m³",
        change_label2="Feststoff:", change_value2=f"{pf:.3f}".replace(".", ",") + " t/m³"
    ), unsafe_allow_html=True)

    
    col9.markdown(panel_template.format(
        caption="Feststoffmasse",
        value=format_de(tds_werte.get("feststoffmasse"), 0) + " t" if tds_werte.get("feststoffmasse") is not None else "-",
        change_label1="Volumen:", change_value1=format_de(tds_werte.get("feststoffvolumen"), 0) + " m³" if tds_werte.get("feststoffvolumen") is not None else "-",
        change_label2="Konzentration:", change_value2=f"{tds_werte.get('feststoffkonzentration'):.1%}".replace(".", ",") if tds_werte.get("feststoffkonzentration") is not None else "-"
    ), unsafe_allow_html=True)

    col10.markdown(panel_template.format(
        caption="Bodenvolumen",
        value=format_de(tds_werte.get("bodenvolumen"), 0) + " m³" if tds_werte.get("bodenvolumen") is not None else "-",
        change_label1="Bodendichte:", change_value1=f"{pb:.3f}".replace(".", ",") + " t/m³",
        change_label2="", change_value2=""
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
# ⏱ Statuszeiten + Strecken (Leerfahrt, Baggern, Vollfahrt, Verbringen, Umlaufdauer und Strecken)
# -------------------------------------------------------------------------------------------------

def zeige_statuszeiten_panels_mit_strecke(row, zeitzone, zeitformat, strecken, panel_template):
    """
    Zeigt fünf Status-Zeitpanels mit zusätzlicher Streckenangabe.
    
    Parameter:
    - row: Zeile aus der Umlauftabelle mit Zeitstempeln
    - zeitzone: z. B. "UTC" oder "Europe/Berlin"
    - zeitformat: Format der Daueranzeige (z. B. "hh:mm:ss")
    - strecken: dict mit Schlüsseln wie "leerfahrt", "baggern", "vollfahrt", "verbringen", "gesamt"
    - panel_template: HTML-Vorlage mit Platz für caption, dauer, startzeit, endzeit, strecke
    """

    # Zeitdauern berechnen
    dauer_leerfahrt_disp   = sichere_dauer(row.get("Start Leerfahrt"), row.get("Start Baggern"), zeitformat)
    dauer_baggern_disp     = sichere_dauer(row.get("Start Baggern"), row.get("Start Vollfahrt"), zeitformat)
    dauer_vollfahrt_disp   = sichere_dauer(row.get("Start Vollfahrt"), row.get("Start Verklappen/Pump/Rainbow"), zeitformat)
    dauer_verbringen_disp  = sichere_dauer(row.get("Start Verklappen/Pump/Rainbow"), row.get("Ende"), zeitformat)
    dauer_umlauf_disp      = sichere_dauer(row.get("Start Leerfahrt"), row.get("Ende"), zeitformat)

    # Darstellung in 5 Spalten
    col1, col2, col3, col4, col5 = st.columns(5)

    # Panel 1 – Leerfahrt
    col1.markdown(panel_template.format(
        caption="Leerfahrt",
        dauer=dauer_leerfahrt_disp,
        startzeit=format_time(row.get("Start Leerfahrt"), zeitzone),
        endzeit=format_time(row.get("Start Baggern"), zeitzone),
        strecke=strecken.get("leerfahrt", "-")
    ), unsafe_allow_html=True)

    # Panel 2 – Baggern
    col2.markdown(panel_template.format(
        caption="Baggern",
        dauer=dauer_baggern_disp,
        startzeit=format_time(row.get("Start Baggern"), zeitzone),
        endzeit=format_time(row.get("Start Vollfahrt"), zeitzone),
        strecke=strecken.get("baggern", "-")
    ), unsafe_allow_html=True)

    # Panel 3 – Vollfahrt
    col3.markdown(panel_template.format(
        caption="Vollfahrt",
        dauer=dauer_vollfahrt_disp,
        startzeit=format_time(row.get("Start Vollfahrt"), zeitzone),
        endzeit=format_time(row.get("Start Verklappen/Pump/Rainbow"), zeitzone),
        strecke=strecken.get("vollfahrt", "-")
    ), unsafe_allow_html=True)

    # Panel 4 – Verbringen
    col4.markdown(panel_template.format(
        caption="Verbringen",
        dauer=dauer_verbringen_disp,
        startzeit=format_time(row.get("Start Verklappen/Pump/Rainbow"), zeitzone),
        endzeit=format_time(row.get("Ende"), zeitzone),
        strecke=strecken.get("verbringen", "-")
    ), unsafe_allow_html=True)

    # Panel 5 – Umlaufdauer
    col5.markdown(panel_template.format(
        caption="Umlaufdauer",
        dauer=dauer_umlauf_disp,
        startzeit=format_time(row.get("Start Leerfahrt"), zeitzone),
        endzeit=format_time(row.get("Ende"), zeitzone),
        strecke=strecken.get("gesamt", "-")
    ), unsafe_allow_html=True)



# -------------------------------------------------------------------------------------------------
# 🗂 Anzeige der Polygon-Namen (Bagger- und Verbringfelder)
# -------------------------------------------------------------------------------------------------

def zeige_bagger_und_verbringfelder(bagger_namen, verbring_namen, df, baggerfelder=None):
    """
    Zeigt Bagger- und Verbringfeldnamen mit Solltiefe (falls vorhanden) und Verweilzeit in Minuten.
    """
    col_feld1, col_feld2 = st.columns([1, 1])

    # Mapping: Baggerfeldname → Solltiefe
    solltiefen_dict = {}
    if baggerfelder:
        solltiefen_dict = {feld["name"]: feld.get("solltiefe") for feld in baggerfelder}

    # 🕒 Zeiten berechnen – auf Basis von Polygon-Auswertung (nun über Status_neu)
    bagger_df = berechne_punkte_und_zeit(df, statuswert="Baggern", status_col="Status_neu")
    bagger_zeiten = bagger_df["Zeit_Minuten"].to_dict()
    
    verbring_df = berechne_punkte_und_zeit(df, statuswert="Verbringen", status_col="Status_neu")
    verbring_zeiten = verbring_df["Zeit_Minuten"].to_dict()
    

    # --------------------------------------------------------------------------------------------------
    # 🟦 Baggerfelder anzeigen
    # --------------------------------------------------------------------------------------------------
    with col_feld1:
        st.markdown("#### Baggerstelle")
        if bagger_zeiten:
            for name in sorted(bagger_namen):
                if name == "außerhalb":
                    continue
                minutes = bagger_zeiten.get(name, 0.0)
                soll = solltiefen_dict.get(name)
                soll_text = f"<strong>Solltiefe:</strong> {soll:.2f} m | " if soll else ""
                st.markdown(f"""<div style='
                    background: #f7fafe;
                    border-radius: 8px;
                    padding: 6px 10px;
                    margin-bottom: 6px;
                    font-size: 0.95rem;
                    color: #4e6980;'>
                    <strong>{name}</strong> – {soll_text}{minutes} min
                </div>""", unsafe_allow_html=True)

            ausserhalb_min = bagger_zeiten.get("außerhalb", 0.0)
            if ausserhalb_min > 0:
                st.markdown(f"""<div style='
                    background: #fff4f4;
                    border-radius: 8px;
                    padding: 6px 10px;
                    margin-bottom: 6px;
                    font-size: 0.95rem;
                    color: #aa0000;'>
                    <strong>außerhalb</strong> – {ausserhalb_min} min
                </div>""", unsafe_allow_html=True)


    # --------------------------------------------------------------------------------------------------
    # 🟩 Verbringfelder anzeigen
    # --------------------------------------------------------------------------------------------------
    with col_feld2:
        st.markdown("#### Verbringstelle")
        if verbring_zeiten:
            for name in sorted(verbring_namen):
                if name == "außerhalb":
                    continue
                minutes = verbring_zeiten.get(name, 0.0)
                st.markdown(f"""<div style='
                    background: #f7fafe;
                    border-radius: 8px;
                    padding: 6px 10px;
                    margin-bottom: 6px;
                    font-size: 0.95rem;
                    color: #4e6980;'>
                    <strong>{name}</strong> – {minutes} min
                </div>""", unsafe_allow_html=True)

            ausserhalb_min = verbring_zeiten.get("außerhalb", 0.0)
            if ausserhalb_min > 0:
                st.markdown(f"""<div style='
                    background: #fff4f4;
                    border-radius: 8px;
                    padding: 6px 10px;
                    margin-bottom: 6px;
                    font-size: 0.95rem;
                    color: #aa0000;'>
                    <strong>außerhalb</strong> – {ausserhalb_min} min
                </div>""", unsafe_allow_html=True)



