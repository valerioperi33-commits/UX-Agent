"""
main.py — Punto di partenza dell'agente.

Cosa fa, in ordine:
  1. controlla che Ollama e il modello siano pronti;
  2. trova gli screenshot nella cartella 'screens/' (o un percorso che passi tu);
  3. li analizza uno per uno;
  4. stampa un report leggibile e lo salva su file (report.md + report.json).

Avvio:
  python main.py                      # analizza tutte le immagini in screens/
  python main.py percorso/immagine.png   # analizza una singola immagine
"""
import sys
from pathlib import Path

import config
from agent import analizza_screenshot, verifica_modello
from report import stampa_e_salva


def trova_immagini(argomenti: list) -> list:
    """Se passi dei percorsi a riga di comando usa quelli, altrimenti la cartella screens/."""
    if argomenti:
        return [Path(a) for a in argomenti]
    return [
        p for p in sorted(config.CARTELLA_SCREEN.glob("*"))
        if p.suffix.lower() in config.ESTENSIONI_IMMAGINI
    ]


def main() -> None:
    print("· Controllo Ollama e modello…")
    ok, messaggio = verifica_modello()
    if not ok:
        print("\n⛔ " + messaggio)
        sys.exit(1)
    print("  " + messaggio)

    immagini = trova_immagini(sys.argv[1:])
    if not immagini:
        print(f"\n⛔ Nessuno screenshot trovato in '{config.CARTELLA_SCREEN}'.")
        print("   Metti un'immagine (.png/.jpg) nella cartella 'screens/' e riprova.")
        sys.exit(1)

    print(f"· Trovati {len(immagini)} screenshot. Inizio l'analisi…\n")
    risultati = []
    for immagine in immagini:
        if not immagine.exists():
            print(f"  ⚠ Salto '{immagine}': file non trovato.")
            continue
        print(f"  → Analizzo: {immagine.name}  (il modello vision può metterci un po'…)")
        risultati.append(analizza_screenshot(immagine))

    if risultati:
        stampa_e_salva(risultati)


if __name__ == "__main__":
    main()
