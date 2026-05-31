"""
app.py — Interfaccia grafica (piccola app web locale) per l'agente.

NON cambia l'analisi: usa le stesse funzioni del terminale (analizza_screenshot,
confronta_progetti). Aggiunge solo le pagine e organizza tutto in tre schede:
  - Nuova analisi  (drag-and-drop + nome progetto)
  - Progetti fatti (si aggiorna a ogni analisi; ogni progetto è salvato in progetti/)
  - Confronta      (sceglie due progetti e li mette a confronto)

Gira in locale su 127.0.0.1: nessun dato esce dal computer.

Avvio:  python app.py     (poi si apre il browser; per non aprirlo: --no-browser)
"""
import sys
import threading
import webbrowser

from flask import Flask, render_template, request, send_from_directory, jsonify, abort

import config
import progetti
from agent import analizza_screenshot, verifica_modello, scalda_modello, confronta_progetti

# Cartella temporanea per il file appena caricato (poi viene copiato nel progetto).
CARTELLA_UPLOAD = config.RADICE / "uploads"
CARTELLA_UPLOAD.mkdir(exist_ok=True)

INDIRIZZO = f"http://127.0.0.1:{config.PORTA_INTERFACCIA}"

app = Flask(__name__)


@app.route("/")
def home():
    """Pagina con le tre schede."""
    ok, messaggio = verifica_modello()        # avvisa se Ollama/modello non sono pronti
    return render_template("index.html", ambiente_ok=ok, messaggio_ambiente=messaggio)


@app.route("/analizza", methods=["POST"])
def analizza():
    """Riceve immagine + nome progetto, analizza (stessa logica del terminale) e salva."""
    file = request.files.get("immagine")
    nome = (request.form.get("nome_progetto") or "").strip()
    if not nome:
        return "Dai un nome al progetto prima di analizzare.", 400
    if not file or not file.filename:
        return "Nessun file ricevuto.", 400

    temp = CARTELLA_UPLOAD / _nome_sicuro(file.filename)
    file.save(temp)
    try:
        risultato = analizza_screenshot(temp)            # <- stessa identica analisi
        progetto = progetti.salva_progetto(nome, temp, risultato)
    finally:
        temp.unlink(missing_ok=True)                     # ripulisce il file temporaneo

    return render_template("risultato.html", r=risultato, nome=progetto["nome"],
                           data=progetto["data"], img_url=f"/immagine/{progetto['slug']}")


@app.route("/api/progetti")
def api_progetti():
    """Elenco dei progetti salvati (per le schede 'Progetti fatti' e 'Confronta')."""
    elenco = [{
        "slug": p["slug"], "nome": p["nome"], "data": p["data"],
        "img_url": f"/immagine/{p['slug']}",
        "contrasto": progetti.riepilogo_contrasto(p["risultato"]),
    } for p in progetti.elenco_progetti()]
    return jsonify(elenco)


@app.route("/progetto/<slug>")
def vedi_progetto(slug):
    """Rivede il report di un progetto salvato."""
    p = progetti.carica_progetto(slug)
    if not p:
        abort(404)
    return render_template("risultato.html", r=p["risultato"], nome=p["nome"],
                           data=p["data"], img_url=f"/immagine/{slug}")


@app.route("/confronta", methods=["POST"])
def confronta():
    """Confronta due progetti scelti dall'utente."""
    a, b = request.form.get("a"), request.form.get("b")
    if not a or not b or a == b:
        return "Scegli due progetti diversi.", 400
    try:
        risultato = confronta_progetti(a, b)
    except Exception as errore:
        return f"Non riesco a confrontare: {errore}", 400
    return render_template("confronto.html", c=risultato)


@app.route("/immagine/<slug>")
def immagine(slug):
    """Serve l'immagine salvata di un progetto (per anteprime e report)."""
    p = progetti.carica_progetto(slug)
    if not p:
        abort(404)
    return send_from_directory(progetti.CARTELLA_PROGETTI / slug, p["immagine"])


def _nome_sicuro(nome: str) -> str:
    """Ripulisce il nome del file (niente percorsi strani), mantenendo l'estensione."""
    return (nome.replace("/", "_").replace("\\", "_").strip()) or "screenshot.png"


def _apri_browser():
    """Apre il browser sull'app, poco dopo l'avvio del server."""
    threading.Timer(1.2, lambda: webbrowser.open(INDIRIZZO)).start()


if __name__ == "__main__":
    print(f"· Interfaccia grafica avviata. Apri il browser su:  {INDIRIZZO}", flush=True)
    print("  (premi CTRL+C in questo terminale per fermarla)", flush=True)
    # Pre-riscaldamento: porta il modello "a regime" prima di iniziare. Avvisa quando è pronto.
    print("· Pre-riscaldo il modello… (attendi il messaggio 'Pronto' prima di trascinare)", flush=True)

    def _scalda_e_avvisa():
        scalda_modello()
        print("✅ Modello pronto: ora le analisi sono veloci. Trascina pure uno screenshot.", flush=True)

    threading.Thread(target=_scalda_e_avvisa, daemon=True).start()
    if "--no-browser" not in sys.argv:
        _apri_browser()
    app.run(host="127.0.0.1", port=config.PORTA_INTERFACCIA, debug=False, threaded=True)
