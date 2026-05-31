"""
progetti.py — Salvataggio e gestione dei "progetti" (la memoria dell'app).

Ogni analisi viene salvata in una cartella dedicata dentro 'progetti/', che prende
il nome dato dall'utente. Dentro ci finiscono:
  - l'immagine inviata,
  - il file analisi.json (giudizio del modello + contrasto dei tool + info progetto).

Cosi' la sezione "Progetti fatti" puo' rileggerli e la funzione "Confronta" puo'
mettere a confronto due analisi gia' fatte.
"""
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

import config

CARTELLA_PROGETTI = config.RADICE / "progetti"


def _slug(nome: str) -> str:
    """Trasforma un nome ('La mia Landing!') in un nome-cartella sicuro ('la-mia-landing')."""
    s = re.sub(r"[^a-z0-9]+", "-", nome.strip().lower()).strip("-")
    return s or "progetto"


def _slug_libero(nome: str) -> str:
    """Slug non ancora usato: se esiste gia', aggiunge -2, -3, ... (non sovrascrive)."""
    base = _slug(nome)
    slug, n = base, 2
    while (CARTELLA_PROGETTI / slug).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug


def percorso_immagine(slug: str) -> Path:
    """Percorso del file immagine salvato per un progetto."""
    progetto = carica_progetto(slug)
    return CARTELLA_PROGETTI / slug / progetto["immagine"]


def salva_progetto(nome: str, percorso_immagine_origine: Path, risultato: dict) -> dict:
    """Crea progetti/<slug>/ con l'immagine e analisi.json. Restituisce i dati del progetto."""
    CARTELLA_PROGETTI.mkdir(exist_ok=True)
    slug = _slug_libero(nome)
    cartella = CARTELLA_PROGETTI / slug
    cartella.mkdir()

    # Copia l'immagine dentro la cartella del progetto, mantenendo l'estensione.
    estensione = Path(percorso_immagine_origine).suffix.lower() or ".png"
    nome_file = "immagine" + estensione
    shutil.copy(percorso_immagine_origine, cartella / nome_file)

    progetto = {
        "nome": nome.strip() or slug,
        "slug": slug,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "immagine": nome_file,
        "risultato": risultato,
    }
    (cartella / "analisi.json").write_text(
        json.dumps(progetto, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return progetto


def carica_progetto(slug: str):
    """Rilegge un progetto salvato dato il suo slug (None se non esiste)."""
    percorso = CARTELLA_PROGETTI / slug / "analisi.json"
    if not percorso.exists():
        return None
    return json.loads(percorso.read_text(encoding="utf-8"))


def elenco_progetti() -> list:
    """Tutti i progetti salvati, dal piu' recente. Per la sezione 'Progetti fatti'."""
    if not CARTELLA_PROGETTI.exists():
        return []
    progetti = [carica_progetto(c.name) for c in CARTELLA_PROGETTI.iterdir() if c.is_dir()]
    progetti = [p for p in progetti if p]
    progetti.sort(key=lambda p: (CARTELLA_PROGETTI / p["slug"]).stat().st_mtime, reverse=True)
    return progetti


def riepilogo_contrasto(risultato: dict) -> dict:
    """Sintesi numerica del contrasto (per le schede progetto e per il confronto)."""
    dettaglio = risultato.get("contrasto", {}).get("dettaglio", [])
    promosse = sum(1 for d in dettaglio if d.get("esiti", {}).get("AA_testo_normale"))
    peggiore = min((d.get("rapporto_contrasto", 0) for d in dettaglio), default=0)
    return {
        "totale": len(dettaglio),
        "promosse_AA": promosse,
        "peggior_rapporto": round(peggiore, 2),
    }


def elimina_progetto(slug: str) -> bool:
    """Cancella del tutto la cartella di un progetto (immagine + analisi)."""
    cartella = CARTELLA_PROGETTI / slug
    if cartella.exists():
        shutil.rmtree(cartella)
        return True
    return False


# ===================== Confronti salvati (cartella confronti/) =====================
CARTELLA_CONFRONTI = config.RADICE / "confronti"


def salva_confronto(risultato: dict) -> dict:
    """
    Salva un confronto in confronti/<slug>/: confronto.json + COPIE delle due immagini.
    Copiando le immagini, il confronto resta consultabile anche se in futuro i progetti
    originali vengono eliminati. 'risultato' e' quello prodotto da agent.confronta_progetti.
    """
    CARTELLA_CONFRONTI.mkdir(exist_ok=True)
    a, b = risultato["a"], risultato["b"]
    base, n = f'{a["slug"]}-vs-{b["slug"]}', 2
    slug = base
    while (CARTELLA_CONFRONTI / slug).exists():
        slug = f"{base}-{n}"; n += 1
    cartella = CARTELLA_CONFRONTI / slug
    cartella.mkdir()

    suff_a = Path(a["immagine"]).suffix or ".png"
    suff_b = Path(b["immagine"]).suffix or ".png"
    shutil.copy(percorso_immagine(a["slug"]), cartella / ("a" + suff_a))
    shutil.copy(percorso_immagine(b["slug"]), cartella / ("b" + suff_b))

    dati = {
        "slug": slug,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "nome_a": a["nome"], "nome_b": b["nome"],
        "img_a": "a" + suff_a, "img_b": "b" + suff_b,
        "confronto": risultato["confronto"],
        "contrasto_a": risultato["contrasto_a"],
        "contrasto_b": risultato["contrasto_b"],
        "tempo_s": risultato["tempo_s"],
    }
    (cartella / "confronto.json").write_text(
        json.dumps(dati, indent=2, ensure_ascii=False), encoding="utf-8")
    return dati


def carica_confronto(slug: str):
    """Rilegge un confronto salvato (None se non esiste)."""
    percorso = CARTELLA_CONFRONTI / slug / "confronto.json"
    return json.loads(percorso.read_text(encoding="utf-8")) if percorso.exists() else None


def elenco_confronti() -> list:
    """Tutti i confronti salvati, dal piu' recente."""
    if not CARTELLA_CONFRONTI.exists():
        return []
    confronti = [carica_confronto(c.name) for c in CARTELLA_CONFRONTI.iterdir() if c.is_dir()]
    confronti = [c for c in confronti if c]
    confronti.sort(key=lambda c: (CARTELLA_CONFRONTI / c["slug"]).stat().st_mtime, reverse=True)
    return confronti


def percorso_immagine_confronto(slug: str, quale: str) -> Path:
    """Percorso di una delle due immagini salvate per un confronto ('a' oppure 'b')."""
    con = carica_confronto(slug)
    nome = con["img_a"] if quale == "a" else con["img_b"]
    return CARTELLA_CONFRONTI / slug / nome
