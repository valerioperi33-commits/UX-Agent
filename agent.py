"""
agent.py — Orchestrazione: il "sistema nervoso" dell'agente.

Mette in fila i tre pezzi dell'agente per ogni screenshot:
  - il CERVELLO (modello vision) da' il giudizio qualitativo;
  - le MANI (i tool Python) calcolano i numeri esatti (colori, contrasto);
  - qui li coordiniamo e li uniamo in un unico risultato.

Regola d'oro rispettata alla lettera: il modello non produce MAI numeri di
contrasto ne' codici colore; quei dati nascono solo dai tool che leggono i pixel.
"""
import json
from pathlib import Path

import yaml
import ollama

import config
from registry import scopri_tool


def carica_system_prompt() -> str:
    """Legge il system prompt dal file prompts.yaml (la parte 'linguistica')."""
    with open(config.RADICE / "prompts.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["system_prompt"]


def _client_ollama():
    """Crea il client Ollama (verso l'host indicato in .env, o quello locale)."""
    return ollama.Client(host=config.OLLAMA_HOST) if config.OLLAMA_HOST else ollama.Client()


def verifica_modello() -> tuple:
    """
    Controllo "pre-volo": Ollama e' raggiungibile? Il modello e' scaricato?
    Restituisce (ok: bool, messaggio: str) con istruzioni utili in caso di errore.
    """
    try:
        elenco = _client_ollama().list()
    except Exception as errore:
        return False, (
            "Non riesco a contattare Ollama. Assicurati che sia in esecuzione "
            "(apri l'app Ollama, oppure lancia `ollama serve` in un terminale).\n"
            f"   Dettaglio tecnico: {errore}"
        )

    nomi = [m["model"] for m in elenco["models"]]
    if config.MODELLO_VISION not in nomi:
        return False, (
            f"Il modello '{config.MODELLO_VISION}' non risulta scaricato.\n"
            f"   Scaricalo con:  ollama pull {config.MODELLO_VISION}\n"
            f"   Modelli presenti: {', '.join(nomi) if nomi else 'nessuno'}"
        )
    return True, f"Ollama ok, modello '{config.MODELLO_VISION}' pronto."


def giudizio_qualitativo(percorso_immagine: Path) -> dict:
    """STADIO 1 — Il cervello: chiede al modello vision il giudizio qualitativo."""
    risposta = _client_ollama().chat(
        model=config.MODELLO_VISION,
        format="json",                       # chiediamo a Ollama una risposta JSON
        options={"temperature": 0.2},        # poca "fantasia" = giudizio piu' stabile
        messages=[
            {"role": "system", "content": carica_system_prompt()},
            {
                "role": "user",
                "content": (
                    "Analizza questo screenshot di interfaccia e compila il report "
                    "nel formato JSON richiesto. Ricorda: NON inventare numeri di "
                    "contrasto ne' codici colore."
                ),
                # Passiamo i byte dell'immagine: nessuna ambiguita' sui percorsi.
                "images": [Path(percorso_immagine).read_bytes()],
            },
        ],
    )
    testo = risposta["message"]["content"]
    try:
        return json.loads(testo)
    except json.JSONDecodeError:
        # Se per qualche motivo non fosse JSON valido, non perdiamo il contenuto.
        return {"_grezzo": testo, "_errore": "Il modello non ha restituito JSON valido."}


def _coppie_candidate(palette: list) -> list:
    """
    Euristica semplice per l'MVP: il colore piu' diffuso e' probabilmente lo
    SFONDO; lo confrontiamo con gli altri colori della palette (possibili testi
    o elementi). Onesti sul limite: senza OCR non sappiamo QUALE sia il testo.
    Con la Fase OCR queste coppie diventeranno testo/sfondo reali, per regione.
    """
    if not palette:
        return []
    sfondo = palette[0]["hex"]
    coppie = []
    for colore in palette[1:]:
        coppie.append({
            "testo": colore["hex"],
            "sfondo": sfondo,
            "etichetta": f"{colore['hex']} su sfondo {sfondo}  (coppia candidata dalla palette)",
        })
    return coppie


def misure_oggettive(percorso_immagine: Path, tool: dict) -> dict:
    """
    STADIO 2 — Le mani: i tool leggono i pixel e calcolano i fatti.
      1. estrae la palette dei colori dominanti;
      2. ricava le coppie testo/sfondo da controllare:
           - PRIMA scelta: dall'OCR (colori del testo reali, per regione);
           - RIPIEGO: dalla palette (euristica) se l'OCR non e' disponibile;
      3. calcola il contrasto WCAG di ogni coppia.
    """
    palette = tool["extract_palette"]["esegui"]({"immagine": str(percorso_immagine)})["palette"]

    coppie, fonte_coppie, nota_ocr = [], "OCR (testo reale)", None
    if "ocr" in tool:
        try:
            ocr = tool["ocr"]["esegui"]({
                "immagine": str(percorso_immagine),
                "lingua": config.OCR_LINGUA,
            })
            coppie = ocr.get("coppie", [])
            nota_ocr = ocr.get("nota")
        except Exception as errore:                 # Tesseract assente o altro problema
            nota_ocr = f"OCR non disponibile: {errore}"

    if not coppie:                                  # nessun testo trovato -> ripiego sulla palette
        coppie = _coppie_candidate(palette)
        fonte_coppie = "palette (euristica, senza OCR)"

    contrasto = tool["check_contrast_pairs"]["esegui"]({"coppie": coppie})
    return {
        "palette": palette,
        "contrasto": contrasto,
        "fonte_coppie": fonte_coppie,
        "nota_ocr": nota_ocr,
    }


def analizza_screenshot(percorso_immagine: Path) -> dict:
    """Analisi completa di un singolo screenshot: unisce Stadio 1 e Stadio 2."""
    percorso_immagine = Path(percorso_immagine)
    tool = scopri_tool()                                  # le "mani" disponibili
    qualitativo = giudizio_qualitativo(percorso_immagine)  # cervello
    oggettivo = misure_oggettive(percorso_immagine, tool)  # mani
    return {
        "immagine": percorso_immagine.name,
        "qualitativo": qualitativo,
        "palette": oggettivo["palette"],
        "contrasto": oggettivo["contrasto"],
        "fonte_coppie": oggettivo["fonte_coppie"],
        "nota_ocr": oggettivo["nota_ocr"],
    }
