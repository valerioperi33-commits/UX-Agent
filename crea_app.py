"""
crea_app.py — Mette sulla Scrivania un avvio comodo di UX Agent, con icona, da doppio click.

NOTA TECNICA (importante): un vero ".app" NON firmato non riesce ad aprirsi se il progetto
sta sulla Scrivania, perche' macOS protegge quella cartella e non lascia leggere i file
all'app. Quindi creiamo un launcher ".command" con l'icona di UX Agent: il doppio click lo
apre passando dal Terminale (che quel permesso ce l'ha gia'), e compare la finestra nativa
dell'app. Cosi' funziona anche dalla Scrivania.

Va rieseguito su ogni Mac (il percorso del progetto cambia).
Uso:  python crea_app.py        (oppure doppio click su  installa_app.command)
"""
import os
from pathlib import Path

from AppKit import NSImage, NSWorkspace          # API native di macOS (arrivano con pywebview/pyobjc)
from PIL import Image, ImageDraw

PROGETTO = Path(__file__).parent.resolve()
SORGENTE_ICONA = PROGETTO / "icona.jpg"
DESKTOP = Path.home() / "Desktop"
LAUNCHER = DESKTOP / "Avvia UX Agent.command"


def _icona_arrotondata(percorso: Path, lato: int = 512) -> Image.Image:
    """Logo reso quadrato e con angoli arrotondati (stile icona macOS)."""
    img = Image.open(percorso).convert("RGBA").resize((lato, lato), Image.LANCZOS)
    raggio = int(lato * 0.2237)
    maschera = Image.new("L", (lato, lato), 0)
    ImageDraw.Draw(maschera).rounded_rectangle([0, 0, lato, lato], radius=raggio, fill=255)
    img.putalpha(maschera)
    return img


def _imposta_icona(file_path: Path, icona: Image.Image):
    """Applica un'icona personalizzata a un file (API native, niente strumenti esterni)."""
    tmp = PROGETTO / ".icona_tmp.png"             # temporaneo dentro il progetto (accessibile)
    icona.save(tmp)
    nsimg = NSImage.alloc().initWithContentsOfFile_(str(tmp))
    NSWorkspace.sharedWorkspace().setIcon_forFile_options_(nsimg, str(file_path), 0)
    tmp.unlink(missing_ok=True)


def crea_app():
    if not SORGENTE_ICONA.exists():
        raise SystemExit(f"Manca l'icona: metti '{SORGENTE_ICONA.name}' nella cartella del progetto.")

    # 1) Il launcher sulla Scrivania: ha "incollato" dentro il percorso del progetto, quindi
    #    funziona ovunque lo si clicchi (passa dal Terminale, che ha i permessi).
    LAUNCHER.write_text(
        "#!/bin/bash\n"
        f'cd "{PROGETTO}" || exit 1\n'
        "source venv/bin/activate\n"
        "python desktop.py\n"
    )
    LAUNCHER.chmod(0o755)

    # 2) Icona di UX Agent sul launcher (e anche sul gemello dentro la cartella del progetto)
    icona = _icona_arrotondata(SORGENTE_ICONA)
    _imposta_icona(LAUNCHER, icona)
    interno = PROGETTO / "avvia_app_desktop.command"
    if interno.exists():
        _imposta_icona(interno, icona)

    print(f"✅ Creato: {LAUNCHER}")
    print("   Doppio click su 'Avvia UX Agent' sulla Scrivania → si apre la finestra dell'app.")


if __name__ == "__main__":
    crea_app()
