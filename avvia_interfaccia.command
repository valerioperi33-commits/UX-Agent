#!/bin/bash
# avvia_interfaccia.command
# Doppio click su questo file (da Finder) per avviare l'interfaccia grafica.
# Si apre il Terminale, parte il server locale e il browser va su http://127.0.0.1:5000
# Per fermarla: torna in questa finestra di Terminale e premi CTRL+C.

cd "$(dirname "$0")"        # entra nella cartella del progetto

if [ ! -d "venv" ]; then
  echo "⛔ Ambiente 'venv' non trovato."
  echo "   Esegui prima il setup descritto nel README (venv + pip install -r requirements.txt)."
  read -n 1 -s -r -p "Premi un tasto per chiudere…"
  exit 1
fi

source venv/bin/activate
python app.py
