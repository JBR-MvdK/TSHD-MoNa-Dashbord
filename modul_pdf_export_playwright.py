import pandas as pd
import base64
import os

from playwright.sync_api import sync_playwright  # Für PDF-Export mit Chromium
from modul_hilfsfunktionen import format_time, sichere_dauer, format_de, get_admin_value  # Hilfsfunktionen aus eigenem Modul
from modul_polygon_auswertung import berechne_punkte_und_zeit  # Funktion zur Zeitberechnung auf Basis von Polygonen



def encode_image_to_base64(pfad):
    with open(pfad, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


# Kartenbilder einbinden
def lade_base64_bild(pfad):
    if os.path.exists(pfad):
        with open(pfad, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""


def export_html_to_pdf_playwright(html_content: str, umlauf: str = "") -> bytes:

    """Wandelt HTML-Content in eine PDF-Datei um – plattformunabhängig über Headless Chromium."""
    
    footer_template = f"""
    <div style="width: 100%; font-size: 9px; color: #888; padding: 0 1cm; font-family: 'Open Sans', sans-serif;">
      <span style="float: left;">TSHD Report – Umlauf-Nr.: {umlauf}</span>
      <span style="float: right;">Seite <span class="pageNumber"></span> von <span class="totalPages"></span></span>
    </div>
    """


    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_content, wait_until="networkidle")
        pdf_bytes = page.pdf(
            format="A4", 
            margin={"top": "10mm", "bottom": "20mm", "left": "15mm", "right": "5mm"},
            print_background=True,
            display_header_footer=True,
            header_template="<div></div>",
            footer_template=footer_template
        )
        browser.close()
        return pdf_bytes



def dauer_min(row, start_key, end_key):
    """Berechnet die Dauer zwischen zwei Zeitpunkten in Minuten (als int). Gibt '-' zurück bei ungültigen Werten."""
    start = row.get(start_key)
    end = row.get(end_key)
    if pd.isna(start) or pd.isna(end):
        return "-"
    try:
        td = end - start
        return int(td.total_seconds() // 60)
    except:
        return "-"


def safe_fmt(value, digits=0, suffix=""):
    """Formatiert numerische Werte sicher mit Tausenderpunkt und optionalem Suffix (z.B. 't', 'm³')."""
    if value is None:
        return "-"
    try:
        if digits == 0:
            formatted = f"{value:,.0f}".replace(",", ".")  # z.B. 4.108
        else:
            formatted = (
                f"{value:,.{digits}f}"
                .replace(",", "X").replace(".", ",").replace("X", ".")  # z.B. 1,153
            )
        return f"{formatted} {suffix}".strip()
    except:
        return "-"


def generate_export_html(
    umlauf_row,
    kennzahlen,
    tds_werte,
    strecken,
    zeitzone,
    zeitformat,
    seite,
    pf,
    pw,
    pb,
    dichtewerte,
    abrechnung,
    amob_dauer=None,
    df_admin=None,
    bagger_namen=None,
    verbring_namen=None,
    df=None,
    baggerfelder=None
):
    # Daten holen
    auftragnehmer = get_admin_value(df_admin, "Auftragnehmer")
    kunde = get_admin_value(df_admin, "Kunde")
    auftrag = get_admin_value(df_admin, "Auftragsnummer")
    schiff = get_admin_value(df_admin, "Schiff")
    umlauf = get_admin_value(df_admin, "Umlauf")

    # Zeitdaten berechnen
    bagger_df = berechne_punkte_und_zeit(df, statuswert="Baggern", status_col="Status_neu")
    bagger_zeiten = bagger_df["Zeit_Minuten"].to_dict()

    verbring_df = berechne_punkte_und_zeit(df, statuswert="Verbringen", status_col="Status_neu")
    verbring_zeiten = verbring_df["Zeit_Minuten"].to_dict()

    # Solltiefen optional
    solltiefen = {feld["name"]: feld.get("solltiefe") for feld in baggerfelder} if baggerfelder else {}

    # Tabellenzeilen generieren
    bagger_html = ""
    for name in sorted(bagger_namen if bagger_namen is not None else []):
        if name == "außerhalb":
            continue
        min = bagger_zeiten.get(name, 0.0)
        soll = solltiefen.get(name)
        soll_text = f"Solltiefe: {soll:.2f} m | " if soll else ""
        bagger_html += f"<tr><td>{name}</td><td>{soll_text}{min:.1f} min</td></tr>"

    verbring_html = ""
    for name in sorted(verbring_namen if verbring_namen is not None else []):
        if name == "außerhalb":
            continue
        min = verbring_zeiten.get(name, 0.0)
        verbring_html += f"<tr><td>{name}</td><td>{min:.1f} min</td></tr>"


    # Bedingung: Nur anzeigen, wenn manuelle Eingaben vorhanden sind
    # 💡 HTML-Blöcke initialisieren
    manuelle_feststoff_html = ""
    zusatzinfo_html = ""
    
    # ✅ Block 1: Nur wenn manuelle Feststoffdaten vollständig vorhanden sind
    if all([
        tds_werte.get("feststoff_manuell") is not None,
        tds_werte.get("proz") is not None,
        tds_werte.get("voll_volumen") is not None,
        tds_werte.get("feststoff_gemisch") is not None,
        tds_werte.get("feststoff_gesamt") is not None,
    ]):
        manuelle_feststoff_html = f"""
        <!-- Manuelle Feststoffdaten -->
        <br>
        <h2 style="border-bottom: 1px solid #204060; padding-bottom: 4px; margin-bottom: 10px;">Manuelle Feststoffdaten</h2>
        <div style="display: flex; gap: 16px; margin-bottom: 1em;">
            <div style="flex: 1;">
                <div style="border-bottom: 1px solid #ccc; padding-bottom: 2px; margin-bottom: 6px; font-weight: 600;">Eingabewerte</div>
                <table style="width: 100%;">
                    <tr><td>Feststoff (m³):</td><td style="text-align: right;">{safe_fmt(tds_werte.get("feststoff_manuell"), 0, "m³")}</td></tr>
                    <tr><td>Zentrifuge (%):</td><td style="text-align: right;">{safe_fmt(tds_werte.get("proz"), 1, "%")}</td></tr>
                    <tr><td>Volumen (gesamt):</td><td style="text-align: right;">{safe_fmt(tds_werte.get("voll_volumen"), 0, "m³")}</td></tr>
                </table>
            </div>
            <div style="flex: 1;">&nbsp;</div>
            <div style="flex: 1;">
                <div style="border-bottom: 1px solid #ccc; padding-bottom: 2px; margin-bottom: 6px; font-weight: 600;">Berechnete Werte</div>
                <table style="width: 100%;">
                    <tr><td>Feststoff - Gemisch:</td><td style="text-align: right;">{safe_fmt(tds_werte.get("feststoff_gemisch"), 0, "m³")}</td></tr>
                    <tr>
                        <td style="border-bottom: 1px solid #ccc; padding-bottom: 2px;">Feststoff - Gesamt:</td>
                        <td style="text-align: right; border-bottom: 1px solid #ccc; padding-bottom: 2px;">
                            {safe_fmt(tds_werte.get("feststoff_gesamt"), 0, "m³")}
                        </td>
                    </tr>
                </table>
            </div>
        </div>
        """
    
    # ✅ Block 2: Ansonsten zeige allgemeine Zusatzinfos (AMOB + Dichte)
    else:
        zusatzinfo_html = f"""
        <!-- Zusätzliche Informationen -->
        <br>
        <h2 style="border-bottom: 1px solid #204060; padding-bottom: 4px; margin-bottom: 10px;">zusätzliche Informationen</h2>
        <div style="display: flex; gap: 16px; margin-bottom: 1em;">
            <!-- AMOB-Auswertung -->
            <div style="flex: 3;">
                <div style="border-bottom: 1px solid #ccc; padding-bottom: 2px; margin-bottom: 6px;">AMOB-Auswertung</div>
                <table>
                    <tr><td style="width: 130px;">AMOB-Dauer:</td><td style="text-align: right;">{format_de(amob_dauer / 60, 1) + " min" if amob_dauer else "-"}</td></tr>
                    <tr><td>Baggerzeit:</td><td style="text-align: right;">{dauer_min(umlauf_row, "Start Baggern", "Start Vollfahrt")} min</td></tr>
                    <tr><td style="border-bottom: 1px solid #ccc;">AMOB-Anteil:</td><td style="text-align: right; border-bottom: 1px solid #ccc;">
                        {(
                            f"<span style='color: #dc2626;'>{format_de(amob_dauer / ((umlauf_row.get('Start Vollfahrt') - umlauf_row.get('Start Baggern')).total_seconds()) * 100, 1)} %</span>"
                            if amob_dauer and umlauf_row.get("Start Vollfahrt") and umlauf_row.get("Start Baggern") and
                            (amob_dauer / ((umlauf_row.get("Start Vollfahrt") - umlauf_row.get("Start Baggern")).total_seconds()) * 100 > 10)
                            else format_de(amob_dauer / ((umlauf_row.get("Start Vollfahrt") - umlauf_row.get("Start Baggern")).total_seconds()) * 100, 1) + " %"
                        ) if amob_dauer and umlauf_row.get("Start Vollfahrt") and umlauf_row.get("Start Baggern") else "-"}
                    </td></tr>
                </table>
            </div>
            <div style="flex: 3;">&nbsp;</div>
            <!-- Referenzdichten -->
            <div style="flex: 4;">
                <div style="border-bottom: 1px solid #ccc; padding-bottom: 2px; margin-bottom: 6px;">Referenzdichten</div>
                <table>
                    <tr><td>Wasser:</td><td style="text-align: right;">{f"{pw:.3f}".replace(".", ",")} t/m³</td></tr>
                    <tr><td>Feststoff:</td><td style="text-align: right;">{f"{pf:.3f}".replace(".", ",")} t/m³</td></tr>
                    <tr><td>Ortsdichte:</td><td style="text-align: right;">{safe_fmt(dichtewerte.get("Ortsdichte"), 3, " t/m³")}</td></tr>
                    <tr><td>min. Baggerdichte:</td><td style="text-align: right;">{safe_fmt(dichtewerte.get("Mindichte"), 3, " t/m³")}</td></tr>
                    <tr><td>max. Baggerdichte:</td><td style="text-align: right;">{safe_fmt(dichtewerte.get("Maxdichte"), 3, " t/m³")}</td></tr>
                    <tr><td>Ladung:</td><td style="text-align: right;">{safe_fmt(tds_werte.get("feststoffkonzentration") * pf if tds_werte.get("feststoffkonzentration") else None, 3, " tTDS/m³")}</td></tr>
                    <tr><td>Ortsspezifisch:</td><td style="text-align: right;">{safe_fmt(dichtewerte.get("Ortsspezifisch"), 3, " tTDS/m³")}</td></tr>
                </table>
            </div>
        </div>
        """
    
    # 🔀 HTML kombinieren (je nach vorhandener Variante)
    zusatzblock_html = manuelle_feststoff_html if manuelle_feststoff_html else zusatzinfo_html


    
    grafik_html = ""
    if os.path.exists("prozessgrafik.png"):
        with open("prozessgrafik.png", "rb") as f:
            image_data = f.read()
            encoded = base64.b64encode(image_data).decode()
            grafik_html = f"""
            <h2 style="border-bottom: 1px solid #204060; padding-bottom: 4px; margin-bottom: 10px;">Prozessdaten</h2>
            <img src="data:image/png;base64,{encoded}" 
                 style="width:100%; margin-bottom: 2em; border: 1px solid #999; border-radius: 6px;" />
            """
            
    baggerkopf_html = ""
    if os.path.exists("baggerkopftiefe.png"):
        with open("baggerkopftiefe.png", "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
            baggerkopf_html = f"""
            <h2 style="border-bottom: 1px solid #204060; padding-bottom: 4px; margin-bottom: 10px;">Baggerkopftiefe</h2>
            <img src="data:image/png;base64,{encoded}" 
                 style="width:100%; margin-bottom: 2em; border: 1px solid #999; border-radius: 6px;" />
            """

    karte_baggern_base64 = lade_base64_bild("karte_baggern.png")
    karte_verbringen_base64 = lade_base64_bild("karte_verbringen.png")
    
    karten_html = f"""
    <h2 style="border-bottom: 1px solid #204060; padding-bottom: 4px; margin-bottom: 10px;">Kartenansicht – Baggern & Verbringen</h2>
    <div style="display: flex; gap: 20px;">
        <div style="flex: 1;">
            <div style="border-bottom: 1px solid #ccc; padding-bottom: 2px; margin-bottom: 12px; font-weight: 600;">Baggerfelder</div>
            <img src="data:image/png;base64,{karte_baggern_base64}" style="width: 100%; border: 1px solid #ccc;margin-bottom: 0px;" />
        </div>
        <div style="flex: 1;">
            <div style="border-bottom: 1px solid #ccc; padding-bottom: 2px; margin-bottom: 12px; font-weight: 600;">Verbringfelder</div>
            <img src="data:image/png;base64,{karte_verbringen_base64}" style="width: 100%; border: 1px solid #ccc;margin-bottom: 0px;" />

        </div>
    </div>
        <p style="font-size: 9px; text-align: left; color: #888;">
          Kartendaten: © <a href="https://www.openstreetmap.org/copyright" target="_blank" style="color: #888;">OpenStreetMap</a> contributors |
          Darstellung: <a href="https://www.mapbox.com/about/maps/" target="_blank" style="color: #888;">Mapbox</a>
        </p>

    <div style="display: flex; gap: 20px;">
        <div style="flex: 1;">
            <table style="width: 100%;">
                {bagger_html}     
            </table>  
        </div>
        <div style="flex: 1;">
            <table style="width: 100%;">
                {verbring_html}
            </table>
        </div>
    </div>    
    """
    
    
    
    
    """Erzeugt einfachen HTML-Report für einen Umlauf."""
    html = f"""
    <html><head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Open Sans', sans-serif; margin: 20px; }}
        h1 {{ color: #204060; font-weight: 600; font-size: 24px; }}
        h2 {{ color: #204060; font-weight: 400; font-size: 16px; }}
        div {{ color: #31333F; font-weight: 400; font-size: 14px; font-weight: 600; }}
        table {{ color: #31333F; font-weight: 400; font-size: 11px; width: 95%; line-height: 1.3;}}
        p {{ color: #31333F; font-weight: 400; font-size: 12px; }}
        .panel {{ background:#f7fafe; border-radius:12px; padding:12px; margin:12px 0; }}
        .label {{ font-weight:600; color:#555; }}
        table {{ border-collapse: collapse; }}
    </style>
    </head><body>

    
    <h1>TSHD Report – Umlauf-Auswertung</h1>

    <h2 style="border-bottom: 1px solid #204060; padding-bottom: 4px; margin-bottom: 10px;">Administrative Projektdaten</h2>
    <div style="display: flex; gap: 16px; margin-bottom: 1em;">
        <!-- Spalte 1 -->
        <div style="flex: 4;">
        <div style="border-bottom: 1px solid #ccc; padding-bottom: 2px; margin-bottom: 6px; font-weight: 600;">Projektinfo</div>
            <table style="width: 100%;">
                <tr><td>Auftragnehmer:</td><td style="text-align: right;">{auftragnehmer}</td></tr>
                <tr><td>Kunde:</td><td style="text-align: right;">{kunde}</td></tr>
                <tr><td>Auftragsnummer:</td><td style="text-align: right;">{auftrag}</td></tr>
                <tr><td>Schiff:</td><td style="text-align: right;">{schiff}</td></tr>
            </table>
        </div>
        
        <!-- Spalte 2 -->
        <div style="flex: 3;">
        <div style="border-bottom: 1px solid #ccc; padding-bottom: 2px; margin-bottom: 6px; font-weight: 600;">Umlauf & Zeitraum</div>
            <table style="width: 100%;">
                <tr><td>Umlauf-Nr.:</td><td style="text-align: right;">{umlauf}</td></tr>
                <tr><td>Beginn:</td><td style="text-align: right;">{format_time(umlauf_row.get("Start Leerfahrt"), zeitzone)}</td></tr>
                <tr><td>Ende:</td><td style="text-align: right;">{format_time(umlauf_row.get("Ende"), zeitzone)}</td></tr>
            </table>
        </div>
    </div>
    
    <br>
    {karten_html}
    <br>
    {baggerkopf_html}
    <div style="page-break-before: always;"></div>

    <h2 style="border-bottom: 1px solid #204060; padding-bottom: 4px; margin-bottom: 10px;">Statuszeiten & Strecken</h2>
    <div style="display: flex; gap: 16px; margin-bottom: 1em;">
      <!-- Zeiten -->
        <div style="flex: 40;">
            <div style="border-bottom: 1px solid #ccc; padding-bottom: 2px; margin-bottom: 6px;">
            Zeiten
            </div>
            <table style="">
                <tr><td>Umlaufbeginn:</td><td style="text-align: right;">{format_time(umlauf_row.get("Start Leerfahrt"), zeitzone)}</td></tr>
                <tr><td>Umlaufende:</td><td style="text-align: right;">{format_time(umlauf_row.get("Ende"), zeitzone)}</td></tr>
                <tr><td>Baggerbeginn:</td><td style="text-align: right;">{format_time(umlauf_row.get("Start Baggern"), zeitzone)}</td></tr>
                <tr><td>Baggerende:</td><td style="text-align: right;">{format_time(umlauf_row.get("Start Vollfahrt"), zeitzone)}</td></tr>
                <tr><td>Entladebeginn:</td><td style="text-align: right;">{format_time(umlauf_row.get("Start Verklappen/Pump/Rainbow"), zeitzone)}</td></tr>
                <tr><td>Entladeende:</td><td style="text-align: right;">{format_time(umlauf_row.get("Ende"), zeitzone)}</td></tr>
            </table>
        </div>
       <!-- Dauer -->
        <div style="flex: 30;">
            <div style="border-bottom: 1px solid #ccc; padding-bottom: 2px; margin-bottom: 6px;">
            Dauer
            </div>
            <table style="">
                <tr><td>Leerfahrt:</td><td style="text-align: right;">{dauer_min(umlauf_row, "Start Leerfahrt", "Start Baggern")} min</td></tr>
                <tr><td>Baggern:</td><td style="text-align: right;">{dauer_min(umlauf_row, "Start Baggern", "Start Vollfahrt")} min</td></tr>
                <tr><td>Vollfahrt:</td><td style="text-align: right;">{dauer_min(umlauf_row, "Start Vollfahrt", "Start Verklappen/Pump/Rainbow")} min</td></tr>
                <tr><td>Verbringen:</td><td style="text-align: right;">{dauer_min(umlauf_row, "Start Verklappen/Pump/Rainbow", "Ende")} min</td></tr>
                <tr>
                    <td style="border-bottom: 1px solid #ccc; padding-bottom: 2px;">Umlauf:</td>
                    <td style="text-align: right; border-bottom: 1px solid #ccc; padding-bottom: 2px;">
                    {dauer_min(umlauf_row, "Start Leerfahrt", "Ende")} min
                    </td>
                </tr>
            </table>
        </div>
        <!-- Strecken -->
        <div style="flex: 30;">
            <div style="border-bottom: 1px solid #ccc; padding-bottom: 2px; margin-bottom: 6px;">
            Strecken
            </div>
            <table style="">
                <tr><td style="width: 90px;">Leerfahrt:</td><td style="text-align: right;">{strecken.get("leerfahrt", "-")} km</td></tr>
                <tr><td>Baggern:</td><td style="text-align: right;">{strecken.get("baggern", "-")} km</td></tr>
                <tr><td>Vollfahrt:</td><td style="text-align: right;">{strecken.get("vollfahrt", "-")} km</td></tr>
                <tr><td>Verbringen:</td><td style="text-align: right;">{strecken.get("verbringen", "-")} km</td></tr>
                <tr>
                    <td style="border-bottom: 1px solid #ccc; padding-bottom: 2px;">Gesamt:</td>
                    <td style="text-align: right; border-bottom: 1px solid #ccc; padding-bottom: 2px;">
                    {strecken.get("gesamt", "-")} km
                    </td>
                </tr>
            </table>
        </div>
    
    </div>

    <br>
    {grafik_html}
    <br>
    
    <h2 style="border-bottom: 1px solid #204060; padding-bottom: 4px; margin-bottom: 10px;">Abrechnungergebnisse</h2>
    <div style="display: flex; gap: 16px; margin-bottom: 1em;">
        <!-- Block 1: Ladungsmasse -->
        <div style="flex: 3;">
            <div style="border-bottom: 1px solid #ccc; padding-bottom: 2px; margin-bottom: 6px;">
            Ladungsmasse
            </div>
            <table style="">
                <tr><td style="width: 90px;">leer:</td><td style="text-align:right;">{safe_fmt(kennzahlen.get("verdraengung_leer"), 0, " t")}</td></tr>
                <tr><td>voll:</td><td style="text-align:right;">{safe_fmt(kennzahlen.get("verdraengung_voll"), 0, " t")}</td></tr>
                <tr>
                    <td style="border-bottom: 1px solid #ccc; padding-bottom: 2px;">Gesamt:</td>
                    <td style="text-align:right; border-bottom: 1px solid #ccc; padding-bottom: 2px;">
                    {safe_fmt(kennzahlen.get("delta_verdraengung"), 0, " t")}
                    </td>
                </tr>
            </table>
        </div>
        <!-- Block 2: Ladungsvolumen -->
        <div style="flex: 3;">
            <div style="border-bottom: 1px solid #ccc; padding-bottom: 2px; margin-bottom: 6px;">
            Ladungsvolumen
            </div>
            <table style="">
                <tr><td style="width: 90px;">leer:</td><td style="text-align:right;">{safe_fmt(kennzahlen.get("volumen_leer"), 0, " m³")}</td></tr>
                <tr><td>voll:</td><td style="text-align:right;">{safe_fmt(kennzahlen.get("volumen_voll"), 0, " m³")}</td></tr>
                <tr>
                    <td style="border-bottom: 1px solid #ccc; padding-bottom: 2px;">Gesamt:</td>
                    <td style="text-align:right; border-bottom: 1px solid #ccc; padding-bottom: 2px;">
                    {safe_fmt(kennzahlen.get("delta_volumen"), 0, " m³")}
                    </td>
                </tr>
            </table>
        </div>
        <!-- Block: Abrechnungswerte -->
        <div style="flex: 4;">
            <div style="border-bottom: 1px solid #ccc; padding-bottom: 2px; margin-bottom: 6px;">
            Abrechnungswerte
            </div>
            <table style="">
                <tr><td>Dichte (Ladung):</td><td style="text-align:right;">{safe_fmt(tds_werte.get("ladungsdichte"), 3, " t/m³")}</td></tr>
                <tr><td>Feststoffmasse (TDS):</td><td style="text-align:right;">{safe_fmt(tds_werte.get("feststoffmasse"), 0, " t")}</td></tr>
                <tr><td>Bonusfaktor:</td><td style="text-align:right;">{safe_fmt(abrechnung.get("faktor"), 3)}</td></tr>
                <tr>
                    <td style="border-bottom: 1px solid #ccc; padding-bottom: 2px;">Abrechnungsvolumen:</td>
                    <td style="text-align: right; border-bottom: 1px solid #ccc; padding-bottom: 2px;">
                    {safe_fmt(abrechnung.get("volumen"), 0, " m³")}
                    </td>
                </tr>
            </table>
        </div>
    </div>

    {zusatzblock_html}
    



    </body></html>
    """
    return html


