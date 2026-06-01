#!/bin/bash
# avvia_app_desktop.command
# Doppio click (da Finder) per avviare agente-ux come APP DESKTOP (finestra nativa).
# Si apre il Terminale, poi compare la finestra dell'app. Per chiudere: chiudi la finestra.

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
  echo "⛔ Ambiente 'venv' non trovato."
  echo "   Esegui prima il setup del README (venv + pip install -r requirements.txt)."
  read -n 1 -s -r -p "Premi un tasto per chiudere…"
  exit 1
fi

source venv/bin/activate
python desktop.py
