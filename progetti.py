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
