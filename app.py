"""
app.py — Interfaccia grafica (piccola app web locale) per l'agente.

IMPORTANTE: NON cambia l'analisi. Usa ESATTAMENTE la stessa logica del terminale,
cioe' la funzione `analizza_screenshot` di agent.py (stesso cervello + stesse mani
+ stesso sistema nervoso). Qui aggiungiamo solo una pagina con il drag-and-drop e
una visualizzazione grafica del report.

Gira in locale su 127.0.0.1: nessun dato esce dal computer.

Avvio:
  source venv/bin/activate
  python app.py
Poi si apre il browser su  http://127.0.0.1:5000
(per non aprirlo in automatico:  python app.py --no-browser)
"""
import sys
import threading
import webbrowser

from flask import Flask, render_template, request, send_from_directory

import config
from agent import analizza_screenshot, verifica_modello, scalda_modello

# Cartella dove salviamo le immagini caricate dal browser.
# La teniamo separata da screens/ (che resta la "casella" per l'uso da terminale).
CARTELLA_UPLOAD = config.RADICE / "uploads"
CARTELLA_UPLOAD.mkdir(exist_ok=True)

INDIRIZZO = f"http://127.0.0.1:{config.PORTA_INTERFACCIA}"

app = Flask(__name__)


@app.route("/")
def home():
    """Pagina iniziale: il riquadro per il drag-and-drop."""
    ok, messaggio = verifica_modello()      # avvisa subito se Ollama/modello non sono pronti
    return render_template("index.html", ambiente_ok=ok, messaggio_ambiente=messaggio)


@app.route("/analizza", methods=["POST"])
def analizza():
    """Riceve l'immagine, la analizza con lo STESSO agente e rende il report in HTML."""
    file = request.files.get("immagine")
    if not file or not file.filename:
        return "Nessun file ricevuto.", 400

    # Salviamo nella cartella del progetto (cosi' anche Tesseract la legge senza problemi).
    nome = _nome_sicuro(file.filename)
    file.save(CARTELLA_UPLOAD / nome)

    risultato = analizza_screenshot(CARTELLA_UPLOAD / nome)   # <- stessa identica analisi
    return render_template("risultato.html", r=risultato, nome=nome)


@app.route("/uploads/<path:nome>")
def immagine_caricata(nome):
    """Serve l'immagine caricata, per mostrarne l'anteprima nel report."""
    return send_from_directory(CARTELLA_UPLOAD, nome)


def _nome_sicuro(nome: str) -> str:
    """Ripulisce il nome del file (niente percorsi strani), mantenendo l'estensione."""
    nome = nome.replace("/", "_").replace("\\", "_").strip()
    return nome or "screenshot.png"


def _apri_browser():
    """Apre il browser sull'app, poco dopo l'avvio del server."""
    threading.Timer(1.2, lambda: webbrowser.open(INDIRIZZO)).start()


if __name__ == "__main__":
    print(f"· Interfaccia grafica avviata. Apri il browser su:  {INDIRIZZO}")
    print("  (premi CTRL+C in questo terminale per fermarla)")
    # Pre-riscaldamento: carica e "accende" il modello in background, cosi' la prima
    # analisi della demo parte gia' calda (e quindi veloce). Avvisa quando e' pronto.
    print("· Pre-riscaldo il modello… (attendi il messaggio 'Pronto' prima di trascinare)", flush=True)

    def _scalda_e_avvisa():
        scalda_modello()
        print("✅ Modello pronto: ora le analisi sono veloci. Trascina pure uno screenshot.", flush=True)

    threading.Thread(target=_scalda_e_avvisa, daemon=True).start()
    if "--no-browser" not in sys.argv:
        _apri_browser()
    # threaded=True: la pagina e le immagini si caricano anche mentre il modello lavora.
    app.run(host="127.0.0.1", port=config.PORTA_INTERFACCIA, debug=False, threaded=True)
