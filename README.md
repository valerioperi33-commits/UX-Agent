# UX Agent — Valutazione UX e accessibilità da screenshot (in locale)

**UX Agent** è un agente AI che, dato lo **screenshot** di un'interfaccia, produce una
**valutazione di UX e accessibilità di prima passata** in italiano. Gira **interamente
in locale**: nessun dato esce dal computer. Interfaccia in **Material Design 3**.

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

### Versione "app desktop" (finestra nativa)

Se preferisci una **vera finestra dell'app** invece di una scheda del browser:

- **Da Finder:** doppio click su `avvia_app_desktop.command`.
- **Da terminale:** `python desktop.py`.

Fa esattamente le stesse cose (è la stessa interfaccia), ma dentro una finestra del sistema.
Usa la libreria `pywebview` (già in `requirements.txt`). Se su un Mac non partisse, la
versione nel browser (`python app.py`) resta sempre disponibile come alternativa.

Anche l'interfaccia gira **solo in locale**: nessun dato esce dal computer. Per fermarla,
premi `CTRL+C` nella finestra del Terminale. (La porta è la **5001**, non la 5000: su
macOS la 5000 è occupata dal "Ricevitore AirPlay". Si può cambiare con `PORTA` in `.env`.)

---

## Le tre schede: analisi, progetti, confronto

L'interfaccia è organizzata in tre schede:

1. **Nuova analisi** — scrivi un **nome progetto**, poi trascina lo screenshot. Al
   termine il progetto viene **salvato** in `progetti/<nome>/` (immagine + `analisi.json`).
2. **Progetti fatti** — la galleria delle analisi salvate: si **aggiorna da sola** a ogni
   nuova analisi. Clicca una scheda per rivedere il report; la **×** in alto a destra di
   una scheda **elimina** il progetto (e la sua cartella).
3. **Confronta** — scegli **due** progetti già fatti e l'agente li mette a confronto:
   giudizio aspetto per aspetto con un "vincitore", più il confronto dei numeri di
   contrasto. Ogni confronto viene **salvato** in `confronti/<slug>/` e compare nella lista
   "Confronti salvati" (cliccabile per rivederlo).

Vale sempre la regola d'oro: il modello **confronta a parole**, i **numeri di contrasto**
restano quelli dei tool. Per essere veloce, il confronto **non rianalizza le immagini**:
mette a confronto le due schede già prodotte (operazione di solo testo, ~5–8 s). Inoltre
"chi è più accessibile" lo decidono i **numeri** (più testi che superano l'AA), non il modello.

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
├── app.py             # avvio INTERFACCIA GRAFICA nel browser (app web locale)
├── desktop.py         # avvio come APP DESKTOP: stessa interfaccia in una finestra nativa
├── crea_app.py        # mette "Avvia UX Agent" (launcher con icona) sulla Scrivania
├── icona.jpg          # logo di UX Agent (diventa l'icona del launcher)
├── avvia_interfaccia.command   # doppio click → interfaccia nel browser
├── avvia_app_desktop.command   # doppio click → app in finestra nativa
├── installa_app.command        # doppio click → crea l'app sulla Scrivania
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
│   ├── ocr.py                 # trova il testo e ne campiona i colori reali
│   └── daltonismo.py          # simula i deficit di visione dei colori (e li segnala)
├── screens/           # screenshot per l'uso da terminale
├── uploads/           # file temporaneo dell'immagine caricata (creato in automatico)
├── progetti/          # una sottocartella per progetto: immagine + analisi.json
└── confronti/         # una sottocartella per confronto: due immagini + confronto.json
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

Per ogni screenshot il report unisce tre parti:

1. **Valutazione qualitativa** (dal modello): gerarchia visiva, leggibilità, chiarezza
   della CTA, criticità di accessibilità, aree da verificare, note.
2. **Misure oggettive di contrasto** (dai tool): palette dei colori dominanti e una
   tabella con il rapporto WCAG di ogni coppia testo/sfondo e gli esiti AA/AAA.
3. **Daltonismo** (dal tool `daltonismo.py`): lo screenshot mostrato come lo vedrebbe chi
   ha un deficit di visione dei colori (deuteranopia/protanopia/tritanopia), più l'elenco
   dei colori dominanti che rischiano di confondersi. Verifica "l'uso del colore", che il
   solo contrasto non copre.

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

## Avvio da terminale (utile per l'esame)

Se vi chiedono di avviarlo **solo da terminale**, senza app né browser:

```bash
cd ~/Desktop/"Progetto Benedetti LM91"   # entra nella cartella del progetto
source venv/bin/activate         # attiva l'ambiente (compare (venv) nel prompt)
# assicurati che Ollama sia attivo: apri l'app Ollama, oppure:  ollama serve
python main.py                   # analizza TUTTE le immagini in screens/, stampa e salva il report
```

Per analizzare **una sola** immagine:

```bash
python main.py screens/esempio_landing.png
```

`main.py` stampa il report a video e lo salva in `report.md` e `report.json`. È la modalità
"pura da terminale". (In alternativa: `python app.py` apre l'interfaccia nel browser,
`python desktop.py` la apre in finestra nativa.)

---

## Icona sulla Scrivania ("Avvia UX Agent")

Per avere un avvio comodo con icona sulla Scrivania:

```bash
source venv/bin/activate
python crea_app.py        # oppure doppio click su  installa_app.command
```

Mette sulla Scrivania **"Avvia UX Agent"** con l'icona del logo: doppio click → si apre la
**finestra nativa** dell'app (compare anche una finestrella di Terminale dietro: è normale,
si chiude quando chiudi l'app). **Va rifatto su ogni Mac** (il percorso del progetto viene
"incollato" dentro il launcher).

> ℹ️ **Perché un launcher `.command` e non un vero `.app`?** Un `.app` non firmato **non**
> riesce ad aprirsi se il progetto sta sulla **Scrivania** (o in Documenti/Download): macOS
> protegge quelle cartelle e non lascia leggere i file all'app — e nemmeno l'"Accesso completo
> al disco" basta (il permesso finisce sul Python interno, non sull'app). Il `.command` invece
> passa dal **Terminale**, che quel permesso ce l'ha già → funziona. Stessa app, solo un avvio
> diverso. Restano sempre validi anche `python app.py` (browser) e `python main.py` (terminale).

---

## Trasferire tutto sull'altro Mac (via GitHub)

### A) Da questo Mac — pubblica su GitHub (una volta sola)
1. Su <https://github.com> crea un repository **vuoto** (senza README), es. `ux-agent`.
2. Dalla cartella del progetto:
   ```bash
   git remote add origin https://github.com/<tuo-utente>/ux-agent.git
   git branch -M main
   git push -u origin main
   ```
   Al primo `push` GitHub chiede di autenticarti: usa il tuo utente e, come password, un
   **token** (GitHub → *Settings* → *Developer settings* → *Personal access tokens*).
3. In seguito basta `git push` dopo ogni modifica.

### B) Sull'altro Mac — installa da zero
1. **Prerequisiti** (una volta):
   ```bash
   brew install ollama tesseract       # motore del modello + OCR
   ollama pull qwen2.5vl:3b            # il modello (alcuni GB, una volta sola)
   ```
   (In alternativa Ollama da ollama.com. Per l'italiano nell'OCR: `brew install tesseract-lang`.)
2. **Scarica il progetto e prepara l'ambiente** (se vuoi l'app col doppio click, vedi la nota sopra: tienilo fuori dalle cartelle protette o concedi l'Accesso completo al disco):
   ```bash
   git clone https://github.com/<tuo-utente>/ux-agent.git
   cd ux-agent
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   ```
3. **Prova:** `python main.py` (terminale) oppure `python app.py` (browser).
4. (Facoltativo) `python crea_app.py` per avere l'icona di UX Agent sulla Scrivania anche lì.

> Cosa **non** viaggia su GitHub (è nel `.gitignore`, va ricreato sul nuovo Mac): l'ambiente
> `venv/`, il file `.env` (lo copi da `.env.example`) e le cartelle dati `progetti/`,
> `confronti/`, `uploads/`, `screens/`. Codice, prompt, logo e istruzioni invece sì.

---

## Crediti
**UX Agent** — Progetto LM91 (UX/UI Design), LUMSA. Costruito con Python, Ollama, Tesseract,
Flask e PyWebView; interfaccia in **Material Design 3**.
