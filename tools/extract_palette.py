"""
extract_palette.py — Estrae i colori dominanti di un'immagine

Legge i PIXEL VERI dello screenshot e restituisce i colori piu' presenti, con il
loro codice esadecimale e la percentuale di area occupata. Questi colori servono
poi ad alimentare il controllo di contrasto: e' il modo in cui i "fatti" (i colori)
nascono dai pixel e non dal modello.

Come funziona, in breve:
  1. apriamo l'immagine e la rimpiccioliamo (i colori dominanti non cambiano,
     ma il calcolo diventa molto piu' veloce);
  2. la "quantizziamo", cioe' la riduciamo a pochi colori rappresentativi;
  3. contiamo quanti pixel cadono in ciascun colore e li ordiniamo dal piu' diffuso.
"""
from PIL import Image

TOOL_DEFINITION = {
    "nome": "extract_palette",
    "descrizione": (
        "Estrae i colori dominanti di un'immagine (codice hex + percentuale di "
        "area), leggendo i pixel reali. Utile per alimentare il controllo di contrasto."
    ),
    "parametri": {
        "immagine": "Percorso del file immagine da analizzare.",
        "n_colori": "Quanti colori dominanti estrarre (default 6).",
    },
}


def estrai_palette(percorso: str, n_colori: int = 6, lato_max: int = 200) -> list:
    """Restituisce una lista di colori dominanti ordinati dal piu' diffuso."""
    immagine = Image.open(percorso).convert("RGB")

    # Rimpicciolisce mantenendo le proporzioni: piu' veloce, stessi colori dominanti.
    immagine.thumbnail((lato_max, lato_max))

    # Quantizzazione: riduce l'immagine a 'n_colori' colori rappresentativi.
    quantizzata = immagine.quantize(colors=n_colori, method=Image.Quantize.MEDIANCUT)
    tavolozza = quantizzata.getpalette()                 # [r, g, b, r, g, b, ...]
    conteggi = quantizzata.getcolors() or []             # [(n_pixel, indice), ...]

    totale = sum(n for n, _ in conteggi) or 1            # evita la divisione per zero
    palette = []
    for n_pixel, indice in sorted(conteggi, reverse=True):
        r, g, b = tavolozza[indice * 3: indice * 3 + 3]
        palette.append({
            "hex": f"#{r:02X}{g:02X}{b:02X}",
            "rgb": [r, g, b],
            "percentuale": round(100 * n_pixel / totale, 1),
        })
    return palette


def run(args: dict) -> dict:
    """Punto d'ingresso standard del tool."""
    percorso = args["immagine"]
    n_colori = int(args.get("n_colori", 6))
    palette = estrai_palette(percorso, n_colori=n_colori)
    return {"immagine": str(percorso), "palette": palette}
