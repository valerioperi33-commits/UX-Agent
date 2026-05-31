"""
agent.py — Orchestrazione: il "sistema nervoso" dell'agente.

Mette in fila i tre pezzi dell'agente per ogni screenshot:
  - il CERVELLO (modello vision) da' il giudizio qualitativo;
  - le MANI (i tool Python) calcolano i numeri esatti (colori, contrasto);
  - qui li coordiniamo e li uniamo in un unico risultato.

Regola d'oro rispettata alla lettera: il modello non produce MAI numeri di
contrasto ne' codici colore; quei dati nascono solo dai tool che leggono i pixel.
"""
import io
import json
import time
from pathlib import Path

import yaml
import ollama
from PIL import Image

import config
from registry import scopri_tool


def _leggi_prompt(chiave: str) -> str:
    """Legge un prompt (per chiave) dal file prompts.yaml."""
    with open(config.RADICE / "prompts.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)[chiave]


def carica_system_prompt() -> str:
    """System prompt per l'ANALISI di un singolo screenshot (la parte 'linguistica')."""
    return _leggi_prompt("system_prompt")


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


def _immagine_per_modello(percorso_immagine: Path) -> bytes:
    """
    Prepara l'immagine per il modello: la rimpicciolisce (se piu' grande del limite
    in config) e la restituisce come byte PNG. Meno pixel = il modello la elabora
    molto piu' in fretta, senza perdere le informazioni utili al giudizio.
    """
    immagine = Image.open(percorso_immagine).convert("RGB")
    if config.LATO_MAX_MODELLO:
        immagine.thumbnail((config.LATO_MAX_MODELLO, config.LATO_MAX_MODELLO))
    buffer = io.BytesIO()
    immagine.save(buffer, format="PNG")
    return buffer.getvalue()


def giudizio_qualitativo(percorso_immagine: Path) -> dict:
    """STADIO 1 — Il cervello: chiede al modello vision il giudizio qualitativo."""
    risposta = _client_ollama().chat(
        model=config.MODELLO_VISION,
        format="json",                       # chiediamo a Ollama una risposta JSON
        keep_alive=config.OLLAMA_KEEP_ALIVE,  # tiene il modello "caldo" in memoria
        options={
            "temperature": 0.2,              # poca "fantasia" = giudizio piu' stabile
            "num_predict": config.MAX_TOKEN_RISPOSTA,  # risposta corta = piu' veloce
        },
        messages=[
            {"role": "system", "content": carica_system_prompt()},
            {
                "role": "user",
                "content": (
                    "Analizza questo screenshot di interfaccia e compila il report "
                    "nel formato JSON richiesto. Ricorda: NON inventare numeri di "
                    "contrasto ne' codici colore."
                ),
                "images": [_immagine_per_modello(percorso_immagine)],
            },
        ],
    )
    return _carica_json_robusto(risposta["message"]["content"])


def _carica_json_robusto(testo: str) -> dict:
    """
    Converte in dizionario la risposta del modello. Se il JSON e' stato TRONCATO
    (perche' abbiamo messo un tetto ai token per restare veloci), prova a "ripararlo"
    chiudendo virgolette e parentesi rimaste aperte. Se proprio non ci riesce, non
    perde il contenuto: lo restituisce grezzo.
    """
    try:
        return json.loads(testo)
    except json.JSONDecodeError:
        pass

    riparato = testo
    if riparato.count('"') % 2 == 1:                 # virgoletta aperta -> chiudila
        riparato += '"'
    riparato += "]" * (riparato.count("[") - riparato.count("]"))   # chiudi le liste
    riparato += "}" * (riparato.count("{") - riparato.count("}"))   # chiudi gli oggetti
    try:
        return json.loads(riparato)
    except json.JSONDecodeError:
        return {"_grezzo": testo, "_errore": "Il modello non ha restituito JSON valido."}


def scalda_modello() -> None:
    """
    Carica il modello in memoria con una richiesta minima ("pre-riscaldamento"),
    cosi' la PRIMA analisi vera parte gia' calda. Utile per le dimostrazioni:
    si lancia all'avvio dell'interfaccia (vedi app.py).
    """
    try:
        # Riscaldiamo con una chiamata IDENTICA a quella vera (stesso prompt, immagine
        # della stessa dimensione, stesso formato): cosi' il costo una-tantum di
        # inizializzazione del percorso vision lo paghiamo ORA, non alla prima analisi.
        lato = config.LATO_MAX_MODELLO or 512
        buffer = io.BytesIO()
        Image.new("RGB", (lato, int(lato * 0.66)), "#808080").save(buffer, format="PNG")
        dati = buffer.getvalue()
        # Tre passate: la 1a carica il modello da disco, le altre portano la GPU
        # "a regime" (a freddo le prime analisi sarebbero piu' lente).
        for _ in range(3):
            _client_ollama().chat(
                model=config.MODELLO_VISION,
                format="json",
                keep_alive=config.OLLAMA_KEEP_ALIVE,
                options={"temperature": 0.2, "num_predict": 8},
                messages=[
                    {"role": "system", "content": carica_system_prompt()},
                    {"role": "user", "content": "Rispondi solo: {}", "images": [dati]},
                ],
            )
    except Exception:
        pass        # se il modello non c'e' ancora, lo dira' la verifica all'avvio


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

    t0 = time.perf_counter()
    qualitativo = giudizio_qualitativo(percorso_immagine)  # cervello (la parte lenta)
    t1 = time.perf_counter()
    oggettivo = misure_oggettive(percorso_immagine, tool)  # mani (veloci)
    t2 = time.perf_counter()

    return {
        "immagine": percorso_immagine.name,
        "qualitativo": qualitativo,
        "palette": oggettivo["palette"],
        "contrasto": oggettivo["contrasto"],
        "fonte_coppie": oggettivo["fonte_coppie"],
        "nota_ocr": oggettivo["nota_ocr"],
        "tempi": {
            "modello_s": round(t1 - t0, 1),
            "strumenti_s": round(t2 - t1, 1),
            "totale_s": round(t2 - t0, 1),
        },
    }


def confronta_progetti(slug_a: str, slug_b: str) -> dict:
    """
    Confronta due progetti gia' salvati.
      - CERVELLO: il modello guarda ENTRAMBE le immagini e le confronta a parole.
      - MANI: affianchiamo i dati di contrasto gia' calcolati (numeri dai tool, non dal modello).
    """
    import progetti                                  # qui dentro per evitare cicli all'avvio

    a = progetti.carica_progetto(slug_a)
    b = progetti.carica_progetto(slug_b)
    if not a or not b:
        raise ValueError("Uno dei due progetti da confrontare non esiste.")

    rc_a = progetti.riepilogo_contrasto(a["risultato"])
    rc_b = progetti.riepilogo_contrasto(b["risultato"])
    img_a = _immagine_per_modello(progetti.percorso_immagine(slug_a))
    img_b = _immagine_per_modello(progetti.percorso_immagine(slug_b))

    # Diamo al modello i numeri di contrasto GIA' calcolati dai tool: cosi' il giudizio
    # sull'accessibilita' e' ancorato ai fatti (il modello non li reinventa).
    contesto = (
        f'Confronta queste due interfacce reali. La PRIMA immagine e\' il Progetto A '
        f'("{a["nome"]}"), la SECONDA e\' il Progetto B ("{b["nome"]}"). '
        "Descrivi SOLO cio\' che vedi in QUESTE due immagini. "
        "Dati di contrasto gia\' misurati dai tool (usali, non ricalcolarli): "
        f'A = {rc_a["promosse_AA"]}/{rc_a["totale"]} testi superano AA, peggiore {rc_a["peggior_rapporto"]}:1; '
        f'B = {rc_b["promosse_AA"]}/{rc_b["totale"]} testi superano AA, peggiore {rc_b["peggior_rapporto"]}:1.'
    )

    t0 = time.perf_counter()
    risposta = _client_ollama().chat(
        model=config.MODELLO_VISION,
        format="json",
        keep_alive=config.OLLAMA_KEEP_ALIVE,
        options={"temperature": 0.2, "num_predict": config.MAX_TOKEN_RISPOSTA + 120},
        messages=[
            {"role": "system", "content": _leggi_prompt("confronto_prompt")},
            {"role": "user", "content": contesto, "images": [img_a, img_b]},
        ],
    )
    confronto = _carica_json_robusto(risposta["message"]["content"])

    return {
        "a": a,
        "b": b,
        "confronto": confronto,
        "contrasto_a": rc_a,
        "contrasto_b": rc_b,
        "tempo_s": round(time.perf_counter() - t0, 1),
    }
