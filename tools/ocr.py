"""
ocr.py — Individua il testo nello screenshot e ne campiona i colori reali

Perche' serve: la palette trova bene i grandi blocchi di colore, ma il testo
sottile (un sottotitolo grigio chiaro) occupa poca area e "sparisce". L'OCR
risolve il problema: trova DOVE sta il testo e, in quella zona, separa il colore
delle lettere da quello dello sfondo. Cosi' il controllo di contrasto lavora su
coppie testo/sfondo REALI, lette dai pixel.

Come parliamo con Tesseract: lo chiamiamo DIRETTAMENTE come programma da riga di
comando, passandogli il file dello screenshot, e leggiamo la sua tabella di
risultati in formato TSV (una riga per parola, con posizione e testo). E' il modo
piu' robusto e trasparente: niente file temporanei di mezzo.

Richiede il programma di sistema Tesseract:  brew install tesseract
(per l'italiano, opzionale ma consigliato:    brew install tesseract-lang)

Limite onesto: i colori sono "mediati" sui pixel della zona, quindi su testo
molto piccolo o molto sfumato (anti-aliasing) restano una stima ragionevole, non
una misura perfetta.
"""
import subprocess

import numpy as np
from PIL import Image

TOOL_DEFINITION = {
    "nome": "ocr",
    "descrizione": (
        "Individua il testo nello screenshot (OCR con Tesseract) e, per ogni "
        "regione di testo, campiona il colore del testo e dello sfondo: cosi' il "
        "controllo di contrasto usa coppie testo/sfondo REALI invece che stimate."
    ),
    "parametri": {
        "immagine": "Percorso del file immagine da analizzare.",
        "lingua": "Lingua del testo per Tesseract (es. 'ita+eng'). Default 'eng'.",
    },
}


# --------------------------------------------------------------------------
# 1) Colori: dato il riquadro di una parola, separiamo testo e sfondo
# --------------------------------------------------------------------------
def _rgb_a_hex(rgb) -> str:
    """Da un colore (r, g, b) anche con decimali a '#RRGGBB'."""
    r, g, b = (max(0, min(255, int(round(v)))) for v in rgb)
    return f"#{r:02X}{g:02X}{b:02X}"


def _colori_testo_sfondo(crop: Image.Image):
    """
    Dentro il riquadro di una parola separa i pixel in due gruppi per luminosita'
    (lettere vs sfondo) e restituisce (colore_testo, colore_sfondo).
    Usa un piccolo k-means a 2 cluster sulla luminanza. Se la zona e' quasi a
    tinta unita restituisce None (non c'e' una coppia sensata).
    """
    arr = np.asarray(crop.convert("RGB"), dtype=float).reshape(-1, 3)
    if len(arr) < 10:
        return None

    lum = 0.2126 * arr[:, 0] + 0.7152 * arr[:, 1] + 0.0722 * arr[:, 2]
    basso, alto = float(lum.min()), float(lum.max())
    if alto - basso < 15:                      # zona uniforme: niente testo/sfondo distinti
        return None

    # k-means 1D (2 centri) sulla luminanza: poche iterazioni bastano.
    for _ in range(12):
        chiari = lum > (basso + alto) / 2
        nuovo_basso = lum[~chiari].mean() if (~chiari).any() else basso
        nuovo_alto = lum[chiari].mean() if chiari.any() else alto
        if abs(nuovo_basso - basso) < 0.5 and abs(nuovo_alto - alto) < 0.5:
            basso, alto = nuovo_basso, nuovo_alto
            break
        basso, alto = nuovo_basso, nuovo_alto

    chiari = lum > (basso + alto) / 2
    if not chiari.any() or not (~chiari).any():
        return None

    colore_chiaro = arr[chiari].mean(axis=0)
    colore_scuro = arr[~chiari].mean(axis=0)

    # Il gruppo MENO numeroso e' quasi sempre il testo (i tratti sono sottili).
    if int(chiari.sum()) <= int((~chiari).sum()):
        return _rgb_a_hex(colore_chiaro), _rgb_a_hex(colore_scuro)   # testo chiaro su sfondo scuro
    return _rgb_a_hex(colore_scuro), _rgb_a_hex(colore_chiaro)       # testo scuro su sfondo chiaro


def _chiave_colore(hexcol: str, passo: int = 16) -> tuple:
    """Arrotonda un colore per raggruppare coppie quasi identiche (anti-doppioni)."""
    h = hexcol.lstrip("#")
    return tuple(min(255, round(int(h[i:i + 2], 16) / passo) * passo) for i in (0, 2, 4))


# --------------------------------------------------------------------------
# 2) Dialogo con il programma Tesseract (via riga di comando)
# --------------------------------------------------------------------------
def _verifica_tesseract() -> None:
    """Controlla che Tesseract sia installato; altrimenti spiega come fare."""
    try:
        subprocess.run(["tesseract", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        raise RuntimeError("Tesseract non installato. Installalo con:  brew install tesseract")


def _lingue_installate() -> set:
    """Elenco delle lingue disponibili in Tesseract (es. {'eng', 'ita', ...})."""
    out = subprocess.run(["tesseract", "--list-langs"], capture_output=True)
    testo = out.stdout.decode("utf-8", "replace") + out.stderr.decode("utf-8", "replace")
    # I codici lingua sono parole senza spazi; scartiamo le righe di intestazione.
    return {r.strip() for r in testo.splitlines() if r.strip() and " " not in r.strip()}


def _lingua_da_usare(richiesta: str):
    """Tiene solo le lingue richieste che sono davvero installate (con eventuale nota)."""
    installate = _lingue_installate()
    presenti = [l for l in richiesta.split("+") if l in installate]
    mancanti = [l for l in richiesta.split("+") if l not in installate]

    if presenti:
        usata = "+".join(presenti)
        nota = None
        if mancanti:
            nota = (f"Lingua/e {mancanti} non installate in Tesseract: uso '{usata}'. "
                    "Per l'italiano:  brew install tesseract-lang")
        return usata, nota

    usata = "eng" if "eng" in installate else (sorted(installate)[0] if installate else "eng")
    nota = (f"Nessuna delle lingue richieste e' installata: uso '{usata}'. "
            "Per l'italiano:  brew install tesseract-lang")
    return usata, nota


def _leggi_parole(percorso_immagine: str, lingua: str):
    """
    Esegue Tesseract sul file e restituisce la lista delle parole trovate, come
    dizionari con posizione/affidabilita'/testo. Usiamo l'uscita 'tsv' (tabella).
    """
    out = subprocess.run(
        ["tesseract", str(percorso_immagine), "stdout", "-l", lingua, "tsv"],
        capture_output=True,
    )
    if out.returncode != 0:
        raise RuntimeError(out.stderr.decode("utf-8", "replace").strip() or "errore di Tesseract")

    righe = out.stdout.decode("utf-8", "replace").splitlines()
    if not righe:
        return []
    intestazione = righe[0].split("\t")
    indice = {nome: i for i, nome in enumerate(intestazione)}
    parole = []
    for riga in righe[1:]:
        campi = riga.split("\t")
        if len(campi) == len(intestazione):
            parole.append({nome: campi[i] for nome, i in indice.items()})
    return parole


# --------------------------------------------------------------------------
# 3) Punto d'ingresso standard del tool
# --------------------------------------------------------------------------
def run(args: dict) -> dict:
    _verifica_tesseract()
    percorso = args["immagine"]
    lingua_richiesta = args.get("lingua", "eng")
    lingua, nota = _lingua_da_usare(lingua_richiesta)

    immagine = Image.open(percorso).convert("RGB")
    parole = _leggi_parole(percorso, lingua)

    regioni, coppie, visti = [], [], set()
    for parola in parole:
        testo = (parola.get("text") or "").strip()
        try:
            conf = float(parola.get("conf", -1))
        except (ValueError, TypeError):
            conf = -1
        if not testo or conf < 50:             # scarta testo vuoto o poco affidabile
            continue

        l, t = int(parola["left"]), int(parola["top"])
        w, h = int(parola["width"]), int(parola["height"])
        if w < 4 or h < 6:                      # riquadri troppo piccoli: poco affidabili
            continue

        colori = _colori_testo_sfondo(immagine.crop((l, t, l + w, t + h)))
        if not colori:
            continue
        colore_testo, colore_sfondo = colori

        regioni.append({
            "testo": testo,
            "riquadro": [l, t, w, h],
            "colore_testo": colore_testo,
            "colore_sfondo": colore_sfondo,
        })

        chiave = (_chiave_colore(colore_testo), _chiave_colore(colore_sfondo))
        if chiave not in visti:                 # niente coppie quasi-identiche ripetute
            visti.add(chiave)
            coppie.append({
                "testo": colore_testo,
                "sfondo": colore_sfondo,
                "etichetta": f'"{testo}"  {colore_testo} su {colore_sfondo}',
            })

    return {
        "immagine": str(percorso),
        "lingua_usata": lingua,
        "regioni": regioni,
        "coppie": coppie[:15],                  # teniamo la tabella leggibile
        "nota": nota,
    }
