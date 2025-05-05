# modul_umlauftabelle.py

import pandas as pd
from modul_hilfsfunktionen import to_hhmmss, to_dezimalstunden, to_dezimalminuten

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
