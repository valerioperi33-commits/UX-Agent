"""
crea_app.py — Crea l'app "UX Agent.app" sulla Scrivania (con icona e nome), da doppio click.

Cosa fa:
  1. prende il logo del progetto (icona.jpg), lo rende quadrato e gli arrotonda gli angoli;
  2. lo converte nel formato icona di macOS (.icns, con tutte le misure);
  3. costruisce un vero ".app" che, al doppio click, apre l'interfaccia in finestra nativa.

Va rieseguito SU OGNI MAC (il percorso del progetto cambia da un computer all'altro).

Uso:  python crea_app.py        (oppure doppio click su installa_app.command)
"""
import plistlib
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

PROGETTO = Path(__file__).parent.resolve()
NOME_APP = "UX Agent"
SORGENTE_ICONA = PROGETTO / "icona.jpg"          # il logo (jpg o png)
DESKTOP = Path.home() / "Desktop"


def _icona_arrotondata(percorso: Path, lato: int = 1024) -> Image.Image:
    """Carica il logo, lo rende quadrato e gli arrotonda gli angoli (stile macOS)."""
    img = Image.open(percorso).convert("RGBA").resize((lato, lato), Image.LANCZOS)
    raggio = int(lato * 0.2237)                  # curvatura tipica delle icone macOS
    maschera = Image.new("L", (lato, lato), 0)
    ImageDraw.Draw(maschera).rounded_rectangle([0, 0, lato, lato], radius=raggio, fill=255)
    img.putalpha(maschera)
    return img


def _crea_icns(icona: Image.Image, destinazione: Path):
    """Genera il file .icns con tutte le misure richieste da macOS (tramite iconutil)."""
    with tempfile.TemporaryDirectory() as tmp:
        iconset = Path(tmp) / "icona.iconset"
        iconset.mkdir()
        for dim in (16, 32, 128, 256, 512):
            icona.resize((dim, dim), Image.LANCZOS).save(iconset / f"icon_{dim}x{dim}.png")
            doppio = dim * 2
            icona.resize((doppio, doppio), Image.LANCZOS).save(iconset / f"icon_{dim}x{dim}@2x.png")
        subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(destinazione)], check=True)


def crea_app():
    if not SORGENTE_ICONA.exists():
        raise SystemExit(f"Manca l'icona: metti '{SORGENTE_ICONA.name}' nella cartella del progetto.")

    app = DESKTOP / f"{NOME_APP}.app"
    if app.exists():
        shutil.rmtree(app)                       # rifa' da capo se esiste gia'
    contents = app / "Contents"
    (contents / "MacOS").mkdir(parents=True)
    (contents / "Resources").mkdir(parents=True)

    # 1) Icona
    _crea_icns(_icona_arrotondata(SORGENTE_ICONA), contents / "Resources" / "icona.icns")

    # 2) Eseguibile: uno script che apre l'app in finestra nativa (usa il python del venv)
    avvia = contents / "MacOS" / "avvia"
    avvia.write_text(
        "#!/bin/bash\n"
        f'cd "{PROGETTO}" || exit 1\n'
        # Registriamo cosa succede in un log: se l'app non parte, l'errore e' qui.
        f'exec "{PROGETTO}/venv/bin/python" desktop.py >> "{PROGETTO}/desktop_app.log" 2>&1\n'
    )
    avvia.chmod(0o755)

    # 3) Info.plist (nome visualizzato, icona, ecc.)
    info = {
        "CFBundleName": NOME_APP,
        "CFBundleDisplayName": NOME_APP,
        "CFBundleExecutable": "avvia",
        "CFBundleIconFile": "icona",
        "CFBundleIdentifier": "it.lumsa.lm91.uxagent",
        "CFBundlePackageType": "APPL",
        "CFBundleVersion": "1.0",
        "CFBundleShortVersionString": "1.0",
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "11.0",
    }
    with open(contents / "Info.plist", "wb") as f:
        plistlib.dump(info, f)

    subprocess.run(["touch", str(app)], check=False)     # invita il Finder ad aggiornare l'icona
    print(f"✅ Creata: {app}")
    print("   La trovi sulla Scrivania. Se l'icona non si aggiorna subito, attendi un attimo.")


if __name__ == "__main__":
    crea_app()
