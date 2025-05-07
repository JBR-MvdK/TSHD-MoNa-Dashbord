# modul_umlauftabelle.py

import pandas as pd

from modul_hilfsfunktionen import to_hhmmss, to_dezimalstunden, to_dezimalminuten, format_de
from modul_umlauf_kennzahl import berechne_umlauf_kennzahlen
from modul_berechnungen import berechne_tds_aus_werte, berechne_umlauf_auswertung




def show_gesamtzeiten_dynamisch(
    summe_leerfahrt, summe_baggern, summe_vollfahrt, summe_verklapp, summe_umlauf, 
    zeitformat="hh:mm:ss", title="Gesamtzeiten"
):
    """
    Zeigt die Gesamtzeiten-Tabelle: 
    - Erste Zeile im gewählten Zeitformat 
    - Zweite Zeile immer in Dezimalstunden
    """
    format_mapper = {
        "hh:mm:ss": to_hhmmss,
        "dezimalminuten": to_dezimalminuten,
        "dezimalstunden": to_dezimalstunden,
    }

    formatter = format_mapper.get(zeitformat, to_hhmmss)

    summen_format1 = [
        formatter(summe_leerfahrt),
        formatter(summe_baggern),
        formatter(summe_vollfahrt),
        formatter(summe_verklapp),
        formatter(summe_umlauf)
    ]

    summen_stunden = [
        to_dezimalstunden(summe_leerfahrt),
        to_dezimalstunden(summe_baggern),
        to_dezimalstunden(summe_vollfahrt),
        to_dezimalstunden(summe_verklapp),
        to_dezimalstunden(summe_umlauf)
    ]

    columns = ["Leerfahrt", "Baggern", "Vollfahrt", "Verklappen", "Umlauf"]
    gesamtzeiten_df = pd.DataFrame([summen_format1, summen_stunden], columns=columns)
    gesamtzeiten_df.index = ["", ""]
    return gesamtzeiten_df


def erstelle_umlauftabelle(umlauf_info_df, zeitzone, zeitformat):
    """
    Baut die Tabellenstruktur für alle Umläufe auf, inklusive Zeitspalten und Dauern.
    Gibt zurück:
    - df_alle_umlaeufe (MultiIndex-Spalten)
    - Summen-Dauern je Phase
    """

    import pandas as pd
    from modul_hilfsfunktionen import convert_timestamp, format_dauer, to_dezimalstunden

    columns = pd.MultiIndex.from_tuples([
        ("Umlauf", "Nr."),
        ("Datum", ""),
        ("Leerfahrt", "Beginn"), ("Leerfahrt", "Dauer"),
        ("Baggern", "Beginn"), ("Baggern", "Dauer"),
        ("Vollfahrt", "Beginn"), ("Vollfahrt", "Dauer"),
        ("Verklappen", "Beginn"), ("Verklappen", "Dauer"),
        ("Umlauf", "Ende"), ("Umlauf", "Dauer")
    ])

    rows = []
    dauer_leerfahrt_list = []
    dauer_baggern_list = []
    dauer_vollfahrt_list = []
    dauer_verklapp_list = []
    dauer_umlauf_list = []

    for _, row in umlauf_info_df.iterrows():
        def safe_ts(key):
            t = row.get(key, None)
            return convert_timestamp(pd.Timestamp(t) if pd.notnull(t) and t is not None else None, zeitzone) if t is not None else None

        anzeige_start_leerfahrt = safe_ts("Start Leerfahrt")
        anzeige_start_baggern = safe_ts("Start Baggern")
        anzeige_start_vollfahrt = safe_ts("Start Vollfahrt")
        anzeige_start_verklapp = safe_ts("Start Verklappen/Pump/Rainbow")
        anzeige_ende_umlauf = safe_ts("Ende")

        dauer_leerfahrt = (anzeige_start_baggern - anzeige_start_leerfahrt) if anzeige_start_baggern and anzeige_start_leerfahrt else None
        dauer_baggern = (anzeige_start_vollfahrt - anzeige_start_baggern) if anzeige_start_vollfahrt and anzeige_start_baggern else None
        dauer_vollfahrt = (anzeige_start_verklapp - anzeige_start_vollfahrt) if anzeige_start_verklapp and anzeige_start_vollfahrt else None
        dauer_verklapp = (anzeige_ende_umlauf - anzeige_start_verklapp) if anzeige_ende_umlauf and anzeige_start_verklapp else None
        dauer_umlauf = (anzeige_ende_umlauf - anzeige_start_leerfahrt) if anzeige_ende_umlauf and anzeige_start_leerfahrt else None

        if dauer_leerfahrt is not None: dauer_leerfahrt_list.append(dauer_leerfahrt)
        if dauer_baggern is not None: dauer_baggern_list.append(dauer_baggern)
        if dauer_vollfahrt is not None: dauer_vollfahrt_list.append(dauer_vollfahrt)
        if dauer_verklapp is not None: dauer_verklapp_list.append(dauer_verklapp)
        if dauer_umlauf is not None: dauer_umlauf_list.append(dauer_umlauf)

        rows.append([
            row.get("Umlauf", "-"),
            anzeige_start_leerfahrt.strftime("%d.%m.%Y") if anzeige_start_leerfahrt else "-",
            anzeige_start_leerfahrt.strftime("%H:%M:%S") if anzeige_start_leerfahrt else "-",
            format_dauer(dauer_leerfahrt, zeitformat),
            anzeige_start_baggern.strftime("%H:%M:%S") if anzeige_start_baggern else "-",
            format_dauer(dauer_baggern, zeitformat),
            anzeige_start_vollfahrt.strftime("%H:%M:%S") if anzeige_start_vollfahrt else "-",
            format_dauer(dauer_vollfahrt, zeitformat),
            anzeige_start_verklapp.strftime("%H:%M:%S") if anzeige_start_verklapp else "-",
            format_dauer(dauer_verklapp, zeitformat),
            anzeige_ende_umlauf.strftime("%H:%M:%S") if anzeige_ende_umlauf else "-",
            format_dauer(dauer_umlauf, zeitformat)
        ])

    df_alle_umlaeufe = pd.DataFrame(rows, columns=columns)

    return df_alle_umlaeufe, dauer_leerfahrt_list, dauer_baggern_list, dauer_vollfahrt_list, dauer_verklapp_list, dauer_umlauf_list


def berechne_gesamtzeiten(
    dauer_leerfahrt_list,
    dauer_baggern_list,
    dauer_vollfahrt_list,
    dauer_verklapp_list,
    dauer_umlauf_list
):
    return {
        "leerfahrt": sum(dauer_leerfahrt_list, pd.Timedelta(0)),
        "baggern":   sum(dauer_baggern_list, pd.Timedelta(0)),
        "vollfahrt": sum(dauer_vollfahrt_list, pd.Timedelta(0)),
        "verklapp":  sum(dauer_verklapp_list, pd.Timedelta(0)),
        "umlauf":    sum(dauer_umlauf_list, pd.Timedelta(0))
    }


def erzeuge_tds_tabelle(df, umlauf_info_df, schiffsparameter, strategie, pf, pw, pb, zeitformat, epsg_code):
    import pandas as pd

    daten = []

    for _, row in umlauf_info_df.iterrows():
        try:
            t_start = pd.to_datetime(row["Start Leerfahrt"], utc=True) - pd.Timedelta(minutes=15)
            t_ende = pd.to_datetime(row["Ende"], utc=True) + pd.Timedelta(minutes=15)
            df_context = df[(df["timestamp"] >= t_start) & (df["timestamp"] <= t_ende)].copy()

            tds, werte, kennzahlen, *_ = berechne_umlauf_auswertung(
                df_context, row, schiffsparameter, strategie, pf, pw, pb, zeitformat, epsg_code
            )

            leer_masse = werte.get("Verdraengung Start")
            voll_masse = werte.get("Verdraengung Ende")
            diff_masse = voll_masse - leer_masse if None not in [leer_masse, voll_masse] else None

            leer_vol = werte.get("Ladungsvolumen Start")
            voll_vol = werte.get("Ladungsvolumen Ende")
            diff_vol = voll_vol - leer_vol if None not in [leer_vol, voll_vol] else None

            zeile = [
                row["Umlauf"],
                format_de(leer_masse, 0) + " t",
                format_de(voll_masse, 0) + " t",
                format_de(diff_masse, 0) + " t",
                format_de(leer_vol, 0) + " m³",
                format_de(voll_vol, 0) + " m³",
                format_de(diff_vol, 0) + " m³",
                format_de(tds.get("ladungsvolumen"), 0) + " m³",  # wird später überschrieben
                format_de(tds.get("ladungsdichte"), 3) + " t/m³",
                format_de(tds.get("feststoffmasse"), 0) + " t"
            ]
        except Exception:
            zeile = [row["Umlauf"]] + ["-"] * 9

        daten.append(zeile)

    # MultiIndex-Spalten ohne Einheiten
    spalten = pd.MultiIndex.from_tuples([
        ("", "Umlauf"),
        ("Ladungsmasse", "leer"),
        ("Ladungsmasse", "voll"),
        ("Ladungsmasse", "Differenz"),
        ("Ladungsvolumen", "leer"),
        ("Ladungsvolumen", "voll"),
        ("Ladungsvolumen", "Differenz"),
        ("Ladungsvolumen", "kumuliert"),
        ("Ladungsdichte", ""),
        ("Feststoffmasse", ""),
    ])


    df_tabelle = pd.DataFrame(daten, columns=spalten)


    # Kumuliert berechnen
    def parse_number(val):
        try:
            return float(val.replace(".", "").replace(",", ".").split()[0])
        except:
            return None
    
    roh_vol = df_tabelle[("Ladungsvolumen", "Differenz")].map(parse_number)
    df_tabelle[("Ladungsvolumen", "kumuliert")] = roh_vol.cumsum().map(lambda x: format_de(x, 0) + " m³" if x else "-")



    return df_tabelle


def style_tds_tabelle(df):
    # 🎨 Sehr blasse Farben
    def farbe_masse(val): return "background-color: rgba(200,200,200,0.05)"     # ganz blasses grau
    def farbe_volumen(val): return "background-color: rgba(0,180,255,0.04)"   # ganz blasses blau
    def farbe_dichte(val): return "background-color: rgba(200,200,200,0.05)"   # fast weiß, leicht gelblich
    def farbe_feststoff(val): return "background-color: rgba(0,255,80,0.05)" # ganz blasses Rosé

    styler = df.style
    styler = styler.set_properties(**{"text-align": "right"})
    styler = styler.set_table_styles([{"selector": "th", "props": [("text-align", "center")]}])

    styler = styler.applymap(farbe_masse, subset=pd.IndexSlice[:, ("Ladungsmasse", slice(None))])
    styler = styler.applymap(farbe_volumen, subset=pd.IndexSlice[:, ("Ladungsvolumen", slice(None))])
    styler = styler.applymap(farbe_dichte, subset=pd.IndexSlice[:, ("Ladungsdichte", slice(None))])
    styler = styler.applymap(farbe_feststoff, subset=pd.IndexSlice[:, ("Feststoffmasse", slice(None))])

    return styler





