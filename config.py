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
# Default veloce per la dimostrazione; per piu' qualita' si puo' usare qwen2.5vl:7b.
MODELLO_VISION = os.getenv("MODELLO_VISION", "qwen2.5vl:3b")

# Cartella degli screenshot e cartella dei report (percorsi assoluti).
CARTELLA_SCREEN = RADICE / os.getenv("CARTELLA_SCREEN", "screens")
CARTELLA_REPORT = RADICE / os.getenv("CARTELLA_REPORT", ".")

# Lingua per l'OCR (Tesseract), usata nella Fase OCR.
OCR_LINGUA = os.getenv("OCR_LINGUA", "ita+eng")

# Indirizzo del server Ollama: vuoto/assente = default locale (127.0.0.1:11434).
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "").strip() or None

# --- Impostazioni per la VELOCITA' (utili per la dimostrazione all'esame) ---
# Lato massimo (in pixel) a cui rimpicciolire l'immagine PRIMA di darla al modello:
# meno pixel = il modello "vede" prima = analisi piu' veloce. 0 = non ridimensionare.
LATO_MAX_MODELLO = int(os.getenv("LATO_MAX_MODELLO", "512"))

# Tetto ai "token" (pezzi di parola) che il modello puo' generare: tiene corta la
# risposta, quindi rapida. Abbastanza alto da non troncare il JSON.
MAX_TOKEN_RISPOSTA = int(os.getenv("MAX_TOKEN_RISPOSTA", "200"))

# Per quanto Ollama tiene il modello in memoria tra due richieste (es. "30m"):
# cosi' la seconda analisi non deve ricaricarlo da zero.
OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "30m")

# Porta dell'interfaccia grafica. NON usiamo la 5000: su macOS e' occupata dal
# "Ricevitore AirPlay" (Control Center). La 5001 di solito e' libera.
PORTA_INTERFACCIA = int(os.getenv("PORTA", "5001"))

# Estensioni immagine che consideriamo "screenshot".
ESTENSIONI_IMMAGINI = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
