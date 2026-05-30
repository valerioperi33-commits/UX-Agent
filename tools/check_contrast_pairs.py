"""
check_contrast_pairs.py — Controlla piu' coppie testo/sfondo in un colpo solo

Date alcune coppie (testo, sfondo) — passate a mano oppure derivate dalla palette
o dall'OCR — esegue su ciascuna il calcolo del contrasto (riusando il tool
'contrast') e produce un riepilogo comodo per il report.

Nota tecnica: il registry carica i tool "per percorso di file", quindi non sono un
pacchetto Python importabile con il solito 'import'. Per riusare 'contrast' lo
carichiamo qui dal file accanto a questo. Cosi' la formula del contrasto resta
scritta UNA volta sola (in contrast.py) e non la duplichiamo.
"""
import importlib.util
from pathlib import Path

# Carica il modulo contrast.py che sta nella stessa cartella 'tools/'.
_percorso_contrast = Path(__file__).parent / "contrast.py"
_spec = importlib.util.spec_from_file_location("contrast", _percorso_contrast)
_contrast = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_contrast)


TOOL_DEFINITION = {
    "nome": "check_contrast_pairs",
    "descrizione": (
        "Controlla una lista di coppie testo/sfondo: calcola il contrasto WCAG di "
        "ognuna e restituisce il dettaglio piu' un riepilogo (quante superano l'AA)."
    ),
    "parametri": {
        "coppie": (
            "Lista di coppie, ognuna {'testo': '#...', 'sfondo': '#...', "
            "'etichetta': 'descrizione facoltativa'}."
        ),
    },
}


def run(args: dict) -> dict:
    """Punto d'ingresso standard del tool."""
    coppie = args.get("coppie", [])
    dettaglio = []
    for coppia in coppie:
        esito = _contrast.run({
            "colore_1": coppia["testo"],
            "colore_2": coppia["sfondo"],
        })
        esito["etichetta"] = coppia.get("etichetta", "")
        dettaglio.append(esito)

    promosse_aa = sum(1 for r in dettaglio if r["esiti"]["AA_testo_normale"])
    return {
        "totale_coppie": len(dettaglio),
        "coppie_promosse_AA_testo_normale": promosse_aa,
        "dettaglio": dettaglio,
    }
