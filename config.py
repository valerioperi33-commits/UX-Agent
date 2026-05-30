"""
config.py — Le impostazioni del progetto, in un posto solo.

Il resto del codice non deve sapere DA DOVE arrivano le impostazioni: le chiede
qui. I valori reali stanno nel file .env (diverso su ogni Mac e non versionato);
qui mettiamo dei valori di default sensati nel caso .env manchi o sia incompleto.
"""
from pathlib import Path
import os

from dotenv import load_dotenv

# Carica le variabili scritte in .env dentro l'ambiente (se il file esiste).
load_dotenv()

# Cartella che contiene questo file = radice del progetto.
RADICE = Path(__file__).parent

# Nome del modello vision da usare via Ollama (vedi .env).
MODELLO_VISION = os.getenv("MODELLO_VISION", "qwen2.5vl:7b")

# Cartella degli screenshot e cartella dei report (percorsi assoluti).
CARTELLA_SCREEN = RADICE / os.getenv("CARTELLA_SCREEN", "screens")
CARTELLA_REPORT = RADICE / os.getenv("CARTELLA_REPORT", ".")

# Lingua per l'OCR (Tesseract), usata nella Fase OCR.
OCR_LINGUA = os.getenv("OCR_LINGUA", "ita+eng")

# Indirizzo del server Ollama: vuoto/assente = default locale (127.0.0.1:11434).
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "").strip() or None

# Estensioni immagine che consideriamo "screenshot".
ESTENSIONI_IMMAGINI = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
