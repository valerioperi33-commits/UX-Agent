# agente-ux — Valutazione UX e accessibilità da screenshot (in locale)

Agente AI che, dato lo **screenshot** di un'interfaccia, produce una **valutazione di
UX e accessibilità di prima passata** in italiano. Gira **interamente in locale**:
nessun dato esce dal computer.

Progetto del corso magistrale **LM91 (UX/UI Design) — LUMSA**, per le materie di
linguistica italiana, intelligenza artificiale e prompt design.

---

## L'idea: cervello + mani + sistema nervoso

L'agente è costruito sull'architettura studiata a lezione:

| Pezzo | Nel progetto | Ruolo |
|---|---|---|
| 🧠 **Cervello** | il modello *vision* (via Ollama) | dà il **giudizio qualitativo** sull'interfaccia |
| ✋ **Mani** | i *tool* Python in `tools/` | calcolano i **fatti esatti** (colori, contrasto WCAG) |
| 🕸️ **Sistema nervoso** | `agent.py` + `registry.py` | coordina cervello e mani e unisce i risultati |

### Regola d'oro (anti-allucinazione)
Il contrasto di colore WCAG è una **formula matematica esatta**: stimarlo "a occhio"
sarebbe un'allucinazione. Perciò:

> Il modello **non produce mai** numeri di contrasto né codici colore.
> Ogni dato numerico (rapporto di contrasto, esito AA/AAA, colori) **nasce solo dai
> tool Python** che leggono i pixel.

Il modello si limita a *ragionare sull'immagine* e a *segnalare a parole* le aree
sospette; poi gli strumenti misurano.

---

## Requisiti

- **Mac con Apple Silicon** (M1/M2/M3…) — il progetto è pensato per macOS.
- **Python 3** (testato con 3.14).
- **[Ollama](https://ollama.com)** — il runtime che fa girare il modello in locale.
- **Tesseract** — solo per l'OCR (opzionale ma incluso); si installa con Homebrew.

---

## Installazione passo-passo

Queste istruzioni servono anche per far girare il progetto **sul secondo Mac da zero**.

### 1) Ollama e il modello vision
Installa Ollama da <https://ollama.com> (oppure `brew install ollama`), poi scarica il
modello:

```bash
ollama pull qwen2.5vl:7b
```

> Il primo download è di alcuni GB e si fa **una volta sola**. Assicurati che Ollama
> sia in esecuzione (apri l'app Ollama, oppure lancia `ollama serve` in un terminale).

### 2) Tesseract (per l'OCR)
```bash
brew install tesseract          # motore OCR + lingua inglese
brew install tesseract-lang     # OPZIONALE: aggiunge l'italiano e altre lingue
```
Senza `tesseract-lang` l'agente funziona lo stesso: usa l'inglese per leggere il testo
(per i nostri scopi conta soprattutto *dove* sta il testo e di che *colore* è).

### 3) Ambiente Python (venv)
Dalla cartella del progetto:

```bash
python3 -m venv venv            # crea l'ambiente isolato
source venv/bin/activate        # lo attiva (lo vedi dal prefisso (venv) nel terminale)
pip install -r requirements.txt # installa le librerie elencate
```

### 4) Configurazione locale
```bash
cp .env.example .env
```
Apri `.env` e, se serve, cambia il modello (vedi la tabella RAM qui sotto). Il file
`.env` **non** va su GitHub: così ogni Mac tiene le sue impostazioni.

### 5) Avvio
Metti uno o più screenshot (`.png`, `.jpg`) nella cartella `screens/`, poi:

```bash
python main.py                      # analizza tutte le immagini in screens/
python main.py percorso/immagine.png   # oppure una singola immagine
```

Il report viene **stampato a terminale** e **salvato** in `report.md` e `report.json`.

---

## Interfaccia grafica (drag-and-drop)

Oltre al terminale c'è una piccola **app web locale** che fa la **stessa identica analisi**
(chiama la funzione `analizza_screenshot`): cambia solo la presentazione.

Due modi per avviarla:

- **Da Finder:** doppio click su `avvia_interfaccia.command` (si apre il Terminale e poi il browser).
- **Da terminale:**
  ```bash
  source venv/bin/activate
  python app.py
  ```

Il browser si apre da solo su <http://127.0.0.1:5000>: **trascina uno screenshot** nel
riquadro e, dopo qualche decina di secondi, compare il report con anteprima dell'immagine,
giudizio qualitativo, palette a colori e tabella dei contrasti con esiti AA/AAA.

Anche l'interfaccia gira **solo in locale**: nessun dato esce dal computer. Per fermarla,
premi `CTRL+C` nella finestra del Terminale.

---

## Scegliere il modello in base alla RAM

Il modello si imposta **solo** nel file `.env` (variabile `MODELLO_VISION`): nessuna
modifica al codice.

| RAM del Mac | Modello consigliato | Note |
|---|---|---|
| **16 GB o più** | `qwen2.5vl:7b` | scelta consigliata, ottimo sulle UI |
| **8 GB** | `qwen2.5vl:7b` | funziona ma **lento**: chiudi le altre app |
| **8 GB** (alternative più leggere) | `llava:7b` oppure `qwen2.5vl:3b` | meno preciso ma più veloce/leggero |

Per cambiare modello: `ollama pull <nome-modello>` e poi aggiorna `MODELLO_VISION` in `.env`.

---

## Struttura del progetto

```
.
├── main.py            # avvio DA TERMINALE: trova gli screenshot e lancia l'analisi
├── app.py             # avvio INTERFACCIA GRAFICA (app web locale): stessa analisi
├── avvia_interfaccia.command  # doppio click per avviare l'interfaccia senza terminale
├── agent.py           # orchestrazione: parla col modello e usa i tool
├── config.py          # legge le impostazioni da .env
├── registry.py        # scopre automaticamente i tool nella cartella tools/
├── report.py          # impagina il risultato per il terminale (report.md/.json)
├── prompts.yaml       # system prompt (la parte linguistica del progetto)
├── requirements.txt   # dipendenze per ricreare l'ambiente sul secondo Mac
├── .env.example       # esempio di configurazione (da copiare in .env)
├── templates/         # pagine HTML dell'interfaccia grafica
│   ├── index.html             # pagina col drag-and-drop
│   └── risultato.html         # report mostrato graficamente
├── tools/
│   ├── contrast.py            # rapporto di contrasto WCAG tra due colori
│   ├── extract_palette.py     # colori dominanti di un'immagine
│   ├── check_contrast_pairs.py# controlla più coppie testo/sfondo insieme
│   └── ocr.py                 # trova il testo e ne campiona i colori reali
├── screens/           # screenshot per l'uso da terminale
└── uploads/           # immagini caricate dall'interfaccia (create in automatico)
```

---

## Come aggiungere un nuovo strumento (tool)

Il `registry` scopre i tool **da solo**: per aggiungerne uno basta creare un file in
`tools/` che rispetti il "patto":

```python
# tools/mio_tool.py
TOOL_DEFINITION = {
    "nome": "mio_tool",
    "descrizione": "Spiega in una riga cosa fa.",
    "parametri": {"esempio": "a cosa serve questo parametro"},
}

def run(args: dict) -> dict:
    # ... la logica ...
    return {"risultato": "..."}
```

Non serve modificare nessun altro file: al prossimo avvio il tool è disponibile.

---

## L'output: il report

Per ogni screenshot il report unisce due parti:

1. **Valutazione qualitativa** (dal modello): gerarchia visiva, leggibilità, chiarezza
   della CTA, coerenza e layout, criticità di accessibilità, note.
2. **Misure oggettive di contrasto** (dai tool): palette dei colori dominanti e una
   tabella con il rapporto WCAG di ogni coppia testo/sfondo e gli esiti AA/AAA.

Le coppie testo/sfondo arrivano dall'**OCR** (colori reali del testo) quando Tesseract
è disponibile; altrimenti si ripiega su una stima dalla palette (indicato nel report).

---

## Limiti (onestà metodologica)

Da dichiarare con chiarezza, perché fa parte del rigore del progetto:

- L'analisi parte da uno **screenshot**: i colori sono **stimati dai pixel**. È
  affidabile su **aree ampie**, meno preciso su **testo piccolo o sfumato**
  (anti-aliasing). Se un testo ha un contrasto bassissimo, persino l'OCR può non
  vederlo (in quel caso resta la segnalazione "a parole" del modello).
- Strumenti come **Lighthouse** o **axe** analizzano la **pagina viva** (HTML/CSS) e
  sono più precisi: leggono i colori dichiarati, non stimati.
- Questo agente è una **valutazione UX di prima passata**, utile per accorgersi presto
  dei problemi: **non è una certificazione WCAG legale**.

---

## Pubblicare su GitHub

Il repository è già inizializzato con un primo commit. Per pubblicarlo:

```bash
# 1) crea un repository vuoto su github.com (senza README), poi collega e invia:
git remote add origin https://github.com/<tuo-utente>/agente-ux.git
git branch -M main
git push -u origin main
```

In alternativa, con la CLI di GitHub (`gh`):

```bash
gh repo create agente-ux --public --source=. --remote=origin --push
```

Il `.gitignore` esclude già `venv/`, `.env`, gli screenshot e i report generati.

---

## Crediti
Progetto LM91 (UX/UI Design) — LUMSA. Agente locale costruito con Python, Ollama e Tesseract.
