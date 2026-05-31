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
modello **veloce** (predefinito, ottimo per la dimostrazione):

```bash
ollama pull qwen2.5vl:3b
```

> Il primo download è di alcuni GB e si fa **una volta sola**. Assicurati che Ollama
> sia in esecuzione (apri l'app Ollama, oppure lancia `ollama serve` in un terminale).
> Se in futuro vuoi un'analisi più ricca (ma più lenta): `ollama pull qwen2.5vl:7b`.

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
Apri `.env` e, se serve, cambia il modello (vedi la sezione "Velocità" qui sotto). Il
file `.env` **non** va su GitHub: così ogni Mac tiene le sue impostazioni.

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

Il browser si apre da solo su <http://127.0.0.1:5001>: **trascina uno screenshot** nel
riquadro e in circa **6–8 secondi** compare il report con anteprima dell'immagine,
giudizio qualitativo, palette a colori e tabella dei contrasti con esiti AA/AAA.

> 💡 **Per la dimostrazione:** all'avvio l'app "pre-riscalda" il modello. Aspetta che nel
> Terminale compaia **"✅ Modello pronto"** (qualche decina di secondi) prima di trascinare
> il primo screenshot: da quel momento ogni analisi è veloce.

Anche l'interfaccia gira **solo in locale**: nessun dato esce dal computer. Per fermarla,
premi `CTRL+C` nella finestra del Terminale. (La porta è la **5001**, non la 5000: su
macOS la 5000 è occupata dal "Ricevitore AirPlay". Si può cambiare con `PORTA` in `.env`.)

---

## Le tre schede: analisi, progetti, confronto

L'interfaccia è organizzata in tre schede:

1. **Nuova analisi** — scrivi un **nome progetto**, poi trascina lo screenshot. Al
   termine il progetto viene **salvato** in `progetti/<nome>/` (immagine + `analisi.json`).
2. **Progetti fatti** — la galleria delle analisi salvate: si **aggiorna da sola** a ogni
   nuova analisi. Clicca una scheda per rivedere il report completo.
3. **Confronta** — scegli **due** progetti già fatti e l'agente li mette a confronto:
   giudizio aspetto per aspetto (gerarchia, leggibilità, CTA, accessibilità) con un
   "vincitore", più il confronto dei numeri di contrasto.

Vale sempre la regola d'oro: il modello **confronta a parole**, i **numeri di contrasto**
restano quelli calcolati dai tool.

---

## Velocità e scelta del modello

Tutto si imposta nel file `.env` (nessuna modifica al codice). Il progetto è già
configurato per essere **veloce**: con il modello caldo, un'analisi richiede circa
**6–8 secondi**.

| Obiettivo | `MODELLO_VISION` | Tempo indicativo* |
|---|---|---|
| **Veloce (demo)** — predefinito | `qwen2.5vl:3b` | ~6–8 s |
| **Più qualità, più lento** | `qwen2.5vl:7b` | ~15–25 s |
| **8 GB di RAM** | `qwen2.5vl:3b` (consigliato) | un po' più lento |

*Misurato su MacBook Air M3 (16 GB), modello già "caldo".

Le altre "manopole" di velocità nel `.env`:
- `LATO_MAX_MODELLO` — rimpicciolisce l'immagine **data al modello** (meno pixel = più
  veloce). I tool WCAG usano comunque sempre l'immagine a piena risoluzione.
- `MAX_TOKEN_RISPOSTA` — tetto alla lunghezza della risposta del modello.
- `OLLAMA_KEEP_ALIVE` — quanto tiene il modello in memoria tra un'analisi e l'altra.

Come funziona la velocità (in breve): immagine ridotta + risposta sintetica (con un
esempio nel prompt) + modello "tenuto caldo" e pre-riscaldato all'avvio dell'interfaccia.

Per cambiare modello: `ollama pull <nome>` e poi aggiorna `MODELLO_VISION` in `.env`.

---

## Struttura del progetto

```
.
├── main.py            # avvio DA TERMINALE: trova gli screenshot e lancia l'analisi
├── app.py             # avvio INTERFACCIA GRAFICA (app web locale): stessa analisi
├── avvia_interfaccia.command  # doppio click per avviare l'interfaccia senza terminale
├── agent.py           # orchestrazione: analisi e confronto (parla col modello e usa i tool)
├── progetti.py        # salva/rilegge i "progetti" (immagine + report) nella cartella progetti/
├── config.py          # legge le impostazioni da .env
├── registry.py        # scopre automaticamente i tool nella cartella tools/
├── report.py          # impagina il risultato per il terminale (report.md/.json)
├── prompts.yaml       # system prompt + prompt di confronto (la parte linguistica)
├── requirements.txt   # dipendenze per ricreare l'ambiente sul secondo Mac
├── .env.example       # esempio di configurazione (da copiare in .env)
├── templates/         # pagine HTML dell'interfaccia grafica
│   ├── index.html             # pagina a schede (nuova analisi / progetti / confronta)
│   ├── risultato.html         # report di un'analisi
│   └── confronto.html         # risultato di un confronto
├── tools/
│   ├── contrast.py            # rapporto di contrasto WCAG tra due colori
│   ├── extract_palette.py     # colori dominanti di un'immagine
│   ├── check_contrast_pairs.py# controlla più coppie testo/sfondo insieme
│   └── ocr.py                 # trova il testo e ne campiona i colori reali
├── screens/           # screenshot per l'uso da terminale
├── uploads/           # file temporaneo dell'immagine caricata (creato in automatico)
└── progetti/          # un sottocartella per progetto: immagine + analisi.json
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
