"""
registry.py — Il "catalogo" dei tool, costruito da solo.

Scorre la cartella tools/ e, per ogni file .py che espone un TOOL_DEFINITION e
una funzione run(), lo registra automaticamente. Cosi' per aggiungere un nuovo
tool basta creare un file in tools/: NON serve modificare nessun altro file.

E' la dimostrazione pratica dell'idea "agente = cervello + MANI + sistema nervoso":
qui costruiamo l'elenco delle mani disponibili.
"""
import importlib.util
from pathlib import Path

CARTELLA_TOOLS = Path(__file__).parent / "tools"


def scopri_tool() -> dict:
    """
    Restituisce un dizionario:
        { "nome_tool": {"definizione": {...}, "esegui": <funzione run>} , ... }
    """
    tool = {}
    for percorso in sorted(CARTELLA_TOOLS.glob("*.py")):
        if percorso.name.startswith("_"):     # salta file tipo __init__.py
            continue

        # Carica il file Python come modulo "al volo".
        spec = importlib.util.spec_from_file_location(percorso.stem, percorso)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)

        definizione = getattr(modulo, "TOOL_DEFINITION", None)
        funzione = getattr(modulo, "run", None)

        # Registriamo solo i file che rispettano il "patto" (definizione + run).
        if isinstance(definizione, dict) and callable(funzione):
            tool[definizione["nome"]] = {"definizione": definizione, "esegui": funzione}

    return tool


# Prova rapida: `python registry.py` elenca i tool trovati.
if __name__ == "__main__":
    for nome, t in scopri_tool().items():
        print(f"- {nome}: {t['definizione']['descrizione']}")
