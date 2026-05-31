"""
report.py — Presentazione del risultato.

Trasforma i dati prodotti dall'agente in:
  - un testo leggibile, stampato a terminale e salvato come report.md (Markdown);
  - un file report.json con tutti i dati grezzi (utile per riusarli o controllarli).

Qui non si fanno calcoli: si IMPAGINA soltanto cio' che cervello e mani hanno prodotto.
"""
import json

import config

SPUNTA = "✅"
CROCE = "❌"


def _riga_qualitativa(etichetta: str, valore) -> str:
    """Una voce del giudizio qualitativo. Le liste diventano elenchi puntati."""
    if isinstance(valore, list):
        if not valore:
            return f"- **{etichetta}:** —\n"
        punti = "\n".join(f"  - {voce}" for voce in valore)
        return f"- **{etichetta}:**\n{punti}\n"
    return f"- **{etichetta}:** {valore}\n"


def _sezione_qualitativa(qualitativo: dict) -> str:
    """Costruisce il blocco 'valutazione qualitativa' dal JSON del modello."""
    # Se il modello non avesse prodotto JSON valido, mostriamo il testo grezzo.
    if "_grezzo" in qualitativo:
        return ("> ⚠ Il modello non ha restituito un JSON valido. Testo grezzo:\n\n"
                f"```\n{qualitativo['_grezzo']}\n```\n")

    etichette = {
        "gerarchia_visiva": "Gerarchia visiva",
        "leggibilita": "Leggibilità",
        "chiarezza_cta": "Chiarezza della CTA",
        "coerenza_e_layout": "Coerenza e layout",
        "criticita_accessibilita": "Criticità di accessibilità",
        "aree_da_verificare": "Aree da verificare (contrasto)",
        "note": "Note",
    }
    testo = ""
    for chiave, etichetta in etichette.items():
        if chiave in qualitativo:
            testo += _riga_qualitativa(etichetta, qualitativo[chiave])
    return testo


def _tabella_contrasto(contrasto: dict) -> str:
    """Costruisce la tabella dei contrasti calcolati dai tool."""
    dettaglio = contrasto.get("dettaglio", [])
    if not dettaglio:
        return "_Nessuna coppia di colori da controllare._\n"

    righe = [
        "| Coppia (testo su sfondo) | Rapporto | AA norm. | AA grande | AAA norm. | AAA grande |",
        "|---|---|:---:|:---:|:---:|:---:|",
    ]
    for r in dettaglio:
        e = r["esiti"]
        etichetta = r.get("etichetta") or f"{r['colore_1']} su {r['colore_2']}"
        righe.append(
            f"| {etichetta} | {r['rapporto_formattato']} "
            f"| {SPUNTA if e['AA_testo_normale'] else CROCE} "
            f"| {SPUNTA if e['AA_testo_grande'] else CROCE} "
            f"| {SPUNTA if e['AAA_testo_normale'] else CROCE} "
            f"| {SPUNTA if e['AAA_testo_grande'] else CROCE} |"
        )
    return "\n".join(righe) + "\n"


def _sezione_palette(palette: list) -> str:
    """Elenco dei colori dominanti con percentuale."""
    if not palette:
        return ""
    voci = ", ".join(f"`{c['hex']}` ({c['percentuale']}%)" for c in palette)
    return f"**Colori dominanti:** {voci}\n\n"


def costruisci_markdown(risultati: list) -> str:
    """Unisce tutti gli screenshot analizzati in un unico report Markdown."""
    testo = "# Report UX & Accessibilità — prima passata\n\n"
    testo += ("_Generato in locale dall'agente-ux. È una valutazione di **prima "
              "passata**, non una certificazione WCAG legale: i colori sono stimati "
              "dai pixel dello screenshot._\n\n")

    for r in risultati:
        testo += f"---\n\n## 🖼 {r['immagine']}\n\n"
        if r.get("tempi"):
            t = r["tempi"]
            testo += (f"_⏱️ Tempo di analisi: modello {t['modello_s']}s + "
                      f"strumenti {t['strumenti_s']}s = {t['totale_s']}s_\n\n")
        testo += "### Valutazione qualitativa (modello vision)\n\n"
        testo += _sezione_qualitativa(r["qualitativo"]) + "\n"
        testo += "### Misure oggettive di contrasto (tool WCAG)\n\n"
        testo += _sezione_palette(r["palette"])
        if r.get("fonte_coppie"):
            testo += f"_Coppie testo/sfondo ricavate da: **{r['fonte_coppie']}**._\n\n"
        if r.get("nota_ocr"):
            testo += f"> ℹ️ {r['nota_ocr']}\n\n"
        testo += _tabella_contrasto(r["contrasto"]) + "\n"

    return testo


def stampa_e_salva(risultati: list) -> None:
    """Stampa il report a terminale e lo salva come report.md e report.json."""
    markdown = costruisci_markdown(risultati)

    # 1) A terminale (leggibile cosi' com'e').
    print("\n" + markdown)

    # 2) Su file Markdown.
    percorso_md = config.CARTELLA_REPORT / "report.md"
    percorso_md.write_text(markdown, encoding="utf-8")

    # 3) Su file JSON (dati grezzi).
    percorso_json = config.CARTELLA_REPORT / "report.json"
    percorso_json.write_text(
        json.dumps(risultati, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"\n💾 Report salvati in:\n   - {percorso_md}\n   - {percorso_json}")
