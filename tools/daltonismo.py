"""
daltonismo.py — Simula come appare un'immagine a chi ha un deficit di visione dei colori

Perche' serve all'accessibilita': il contrasto verifica testo/sfondo, ma NON dice se due
colori sono distinguibili da chi e' daltonico (pensa a un grafico rosso/verde, o a un
elemento che si capisce "solo dal colore"). Questo tool trasforma l'immagine per mostrare
come la vedrebbe una persona con i tre tipi piu' comuni di daltonismo, e segnala le coppie
di colori che rischiano di confondersi.

E' un calcolo DETERMINISTICO sui pixel (matrici scientifiche di Machado et al. 2009),
applicate ai canali RGB *linearizzati* (come per la formula del contrasto): nessuna stima
"a occhio", coerente con il principio del progetto.

Tipi simulati:
  - deuteranopia : assenza dei coni "verdi" (il piu' comune)
  - protanopia   : assenza dei coni "rossi"
  - tritanopia   : assenza dei coni "blu" (raro)
"""
import numpy as np
from PIL import Image

TOOL_DEFINITION = {
    "nome": "daltonismo",
    "descrizione": (
        "Simula come appare un'immagine a chi ha un deficit di visione dei colori "
        "(deuteranopia/protanopia/tritanopia) e segnala i colori che si confondono."
    ),
    "parametri": {
        "immagine": "Percorso del file immagine da simulare.",
        "tipo": "Tipo di daltonismo: 'deuteranopia' (default), 'protanopia' o 'tritanopia'.",
    },
}

# Matrici di simulazione (Machado et al. 2009, severita' massima), da applicare ai
# canali RGB linearizzati. Ogni riga dice come si "ricompone" un canale visto dall'occhio.
MATRICI = {
    "deuteranopia": np.array([[0.367322, 0.860646, -0.227968],
                              [0.280085, 0.672501,  0.047413],
                              [-0.011820, 0.042940, 0.968881]]),
    "protanopia":   np.array([[0.152286, 1.052583, -0.204868],
                              [0.114503, 0.786281,  0.099216],
                              [-0.003882, -0.048116, 1.051998]]),
    "tritanopia":   np.array([[1.255528, -0.076749, -0.178779],
                              [-0.078411, 0.930809,  0.147602],
                              [0.004733,  0.691367,  0.303900]]),
}


def _srgb_a_lineare(c):
    """Da sRGB (0-1) a luce 'lineare' (stessa linearizzazione della formula WCAG)."""
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _lineare_a_srgb(c):
    """Da luce lineare a sRGB (0-1). Prima taglia fuori i valori impossibili (<0 o >1)."""
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * (c ** (1 / 2.4)) - 0.055)


def simula(percorso: str, tipo: str = "deuteranopia", lato_max: int = 520) -> Image.Image:
    """Restituisce l'immagine trasformata come la vedrebbe chi ha quel daltonismo."""
    immagine = Image.open(percorso).convert("RGB")
    if lato_max:
        immagine.thumbnail((lato_max, lato_max))           # piu' piccola = piu' veloce
    arr = np.asarray(immagine, dtype=float) / 255.0
    lineare = _srgb_a_lineare(arr)
    simulato = lineare @ MATRICI[tipo].T                   # applica la matrice a ogni pixel
    uscita = _lineare_a_srgb(simulato)
    return Image.fromarray((uscita * 255).round().astype("uint8"), "RGB")


def _hex_a_rgb(colore: str):
    c = colore.lstrip("#")
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], dtype=float)


def _simula_colore(rgb, tipo: str):
    """Simula un singolo colore (per capire se due colori si confondono)."""
    lineare = _srgb_a_lineare(rgb / 255.0)
    return _lineare_a_srgb(MATRICI[tipo] @ lineare) * 255.0


def colori_confondibili(palette: list, tipo: str = "deuteranopia", n: int = 6) -> list:
    """
    Coppie di colori dominanti che, pur diversi all'origine, diventano molto simili per
    chi e' daltonico (quindi NON vanno usati come unico modo per distinguere le cose).
    """
    colori = [_hex_a_rgb(c["hex"]) for c in palette[:n]]
    confondibili = []
    for i in range(len(colori)):
        for j in range(i + 1, len(colori)):
            distanza_originale = np.linalg.norm(colori[i] - colori[j])
            distanza_simulata = np.linalg.norm(_simula_colore(colori[i], tipo) - _simula_colore(colori[j], tipo))
            if distanza_originale > 75 and distanza_simulata < 40:   # diversi -> diventano simili
                confondibili.append({"colore_1": palette[i]["hex"], "colore_2": palette[j]["hex"]})
    return confondibili


def run(args: dict) -> dict:
    """Punto d'ingresso standard del tool: restituisce l'immagine simulata come data-URI."""
    import base64
    import io
    tipo = args.get("tipo", "deuteranopia")
    immagine = simula(args["immagine"], tipo)
    buffer = io.BytesIO()
    immagine.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
    return {"tipo": tipo, "immagine_base64": "data:image/png;base64," + b64}
