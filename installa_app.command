#!/bin/bash
# installa_app.command
# Doppio click (da Finder) per creare l'app "UX Agent" sulla Scrivania (con icona e nome).
# Va fatto UNA VOLTA per Mac. Dopo, avvii l'app dal suo doppio click sulla Scrivania.

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
  echo "⛔ Ambiente 'venv' non trovato. Fai prima il setup del README."
  read -n 1 -s -r -p "Premi un tasto per chiudere…"
  exit 1
fi

source venv/bin/activate
python crea_app.py

echo ""
echo "Premi un tasto per chiudere questa finestra."
read -n 1 -s -r
