"""
contrast.py — Rapporto di contrasto secondo lo standard WCAG 2.x

E' IL tool che dimostra il rigore del progetto: il rapporto di contrasto NON e'
un'opinione, e' una formula matematica esatta. Per questo lo calcoliamo qui, in
Python, e non lo facciamo "stimare a occhio" al modello (sarebbe un'allucinazione).

Formula ufficiale (WCAG 2.x), passo per passo:
  1. Si parte dai due colori sRGB (i normali #RRGGBB).
  2. Per ogni canale (R, G, B) si "linearizza" il valore -> vedi _linearizza().
  3. Si calcola la luminanza relativa L con i pesi della percezione umana:
        L = 0.2126*R + 0.7152*G + 0.0722*B     (sui canali linearizzati)
  4. Il rapporto di contrasto e':
        (L_chiaro + 0.05) / (L_scuro + 0.05)
     dove L_chiaro e' la luminanza maggiore e L_scuro la minore.

Soglie (per "testo grande" si intende >= 24px normale oppure >= 18.66px in grassetto):
  - AA  testo normale: >= 4.5:1
  - AA  testo grande:  >= 3.0:1
  - AAA testo normale: >= 7.0:1
  - AAA testo grande:  >= 4.5:1
"""

# --- "Carta d'identita'" del tool: il registry legge questo dizionario ---
TOOL_DEFINITION = {
    "nome": "contrast",
    "descrizione": (
        "Calcola il rapporto di contrasto WCAG 2.x tra due colori esadecimali "
        "(es. #1A1A1A e #FFFFFF) e dice se superano le soglie AA e AAA."
    ),
    "parametri": {
        "colore_1": "Primo colore in esadecimale, es. '#1A1A1A' (di solito il testo).",
        "colore_2": "Secondo colore in esadecimale, es. '#FFFFFF' (di solito lo sfondo).",
    },
}

# Soglie ufficiali WCAG, raccolte in un punto solo per chiarezza.
SOGLIE = {
    "AA_testo_normale": 4.5,
    "AA_testo_grande": 3.0,
    "AAA_testo_normale": 7.0,
    "AAA_testo_grande": 4.5,
}


def _hex_a_rgb(colore: str) -> tuple:
    """Converte '#1A2B3C' (o '1a2b3c', o la forma corta '#abc') in (26, 43, 60)."""
    c = colore.strip().lstrip("#")
    if len(c) == 3:                       # forma corta "abc" -> "aabbcc"
        c = "".join(canale * 2 for canale in c)
    if len(c) != 6:
        raise ValueError(f"Colore non valido: '{colore}'. Usa il formato #RRGGBB.")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def _linearizza(canale_0_255: int) -> float:
    """Linearizza un singolo canale sRGB (0-255) come prescrive la formula WCAG."""
    c = canale_0_255 / 255.0
    if c <= 0.03928:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def luminanza_relativa(colore_hex: str) -> float:
    """Luminanza relativa L (0 = nero, 1 = bianco) di un colore esadecimale."""
    r, g, b = (_linearizza(canale) for canale in _hex_a_rgb(colore_hex))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def rapporto_contrasto(colore_1: str, colore_2: str) -> float:
    """Rapporto di contrasto WCAG tra due colori (un numero, es. 4.54)."""
    l1 = luminanza_relativa(colore_1)
    l2 = luminanza_relativa(colore_2)
    chiaro, scuro = max(l1, l2), min(l1, l2)
    return (chiaro + 0.05) / (scuro + 0.05)


def run(args: dict) -> dict:
    """
    Punto d'ingresso standard del tool (quello che chiama l'orchestratore).
    Riceve {'colore_1': ..., 'colore_2': ...} e restituisce il rapporto e gli
    esiti rispetto alle quattro soglie.
    """
    colore_1 = args["colore_1"]
    colore_2 = args["colore_2"]
    rapporto = rapporto_contrasto(colore_1, colore_2)

    esiti = {nome: rapporto >= soglia for nome, soglia in SOGLIE.items()}

    return {
        "colore_1": colore_1,
        "colore_2": colore_2,
        "rapporto_contrasto": round(rapporto, 2),
        "rapporto_formattato": f"{round(rapporto, 2)}:1",
        "esiti": esiti,
        "soglie": SOGLIE,
    }


# Piccola prova rapida: si lancia con  `python tools/contrast.py`
# #767676 su bianco e' il grigio "di confine" che supera di un soffio l'AA normale.
if __name__ == "__main__":
    import json
    prova = run({"colore_1": "#767676", "colore_2": "#FFFFFF"})
    print(json.dumps(prova, indent=2, ensure_ascii=False))
