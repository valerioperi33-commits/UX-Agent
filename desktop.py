"""
desktop.py — Avvia agente-ux come APP DESKTOP (finestra nativa, non nel browser).

Mostra la STESSA interfaccia dell'app web, ma dentro una finestra del sistema (tramite
PyWebView). Sotto il cofano gira lo stesso server Flask in locale: cambia solo che, invece
di aprire il browser, apriamo una finestra dedicata. Tutto resta sul tuo computer.

Avvio:
  source venv/bin/activate
  python desktop.py
"""
import socket
import threading
import time

import webview

import config
from agent import scalda_modello
from app import app                      # riusa l'app Flask gia' pronta (stesse pagine e rotte)


def _avvia_server():
    """Fa partire il server Flask in sottofondo (senza ricaricatore, va bene in un thread)."""
    app.run(host="127.0.0.1", port=config.PORTA_INTERFACCIA,
            debug=False, threaded=True, use_reloader=False)


def _attendi_server(porta: int, secondi: float = 10.0):
    """Aspetta che il server sia pronto prima di aprire la finestra (evita pagina vuota)."""
    scadenza = time.time() + secondi
    while time.time() < scadenza:
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", porta)) == 0:
                return
        time.sleep(0.1)


if __name__ == "__main__":
    print("· Avvio agente-ux come app desktop…")
    threading.Thread(target=_avvia_server, daemon=True).start()
    threading.Thread(target=scalda_modello, daemon=True).start()   # pre-riscalda il modello
    _attendi_server(config.PORTA_INTERFACCIA)

    # Apre la finestra nativa che mostra l'interfaccia. Si chiude come una normale app.
    webview.create_window(
        "agente-ux — valutazione UX & accessibilità",
        f"http://127.0.0.1:{config.PORTA_INTERFACCIA}",
        width=1200, height=860, min_size=(900, 600),
    )
    webview.start()
