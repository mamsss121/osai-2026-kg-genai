"""
02_extract_text.py — Extrae texto de los PDFs y separa abstract / body / acknowledgements.

Para cada PDF en data/pdfs/, escribe un JSON en data/papers/<arxiv_id>.json con:
    {
        "arxiv_id": "2604.05571",
        "abstract": "...",
        "acknowledgements": "...",
        "body": "...",
        "raw_text": "...",
        "num_pages": N
    }

Estrategia (sencilla, sin Grobid para no añadir dependencia):
  1. Extraer texto con pymupdf (rápido y de buena calidad).
  2. Localizar la cabecera "Abstract" y tomar texto hasta la siguiente cabecera grande.
  3. Localizar la cabecera "Acknowledgements" / "Acknowledgments" / "Funding" y tomar texto
     hasta la siguiente cabecera (References, Conclusions, etc.).

Sketch initially generated with AI assistance, subsequently reviewed by the group.

Uso:
    python src/02_extract_text.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import fitz  # pymupdf
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PDFS_DIR = PROJECT_ROOT / "data" / "pdfs"
PAPERS_DIR = PROJECT_ROOT / "data" / "papers"

ARXIV_ID_RE = re.compile(r"^(\d{4}\.\d{4,5})(v\d+)?\.pdf$")

# Cabeceras candidatas (case-insensitive); orden importa.
ABSTRACT_HEADERS = ["abstract"]
ACK_HEADERS = ["acknowledgements", "acknowledgments", "acknowledgement", "funding"]
SECTION_AFTER_ABSTRACT = [
    "introduction",
    "1 introduction",
    "1. introduction",
    "i. introduction",
    "keywords",
]
SECTION_AFTER_ACK = [
    "references",
    "bibliography",
    "appendix",
    "supplementary",
    "conclusion",
    "conclusions",
    "discussion",
]


def find_section(text: str, headers: list[str], stop_headers: list[str]) -> str:
    """
    Busca el primer header de `headers` y devuelve el texto hasta el primer `stop_headers`
    posterior. Devuelve "" si no se encuentra el header.
    """
    lowered = text.lower()
    start = -1
    for h in headers:
        idx = lowered.find(h)
        if idx != -1 and (start == -1 or idx < start):
            start = idx
    if start == -1:
        return ""
    # Avanzar pasada la cabecera misma
    after = start
    for h in headers:
        idx = lowered.find(h, start)
        if idx == start:
            after = idx + len(h)
            break

    # Buscar el primer stop_header después del start
    end = len(text)
    for h in stop_headers:
        idx = lowered.find(h, after)
        if idx != -1 and idx < end:
            end = idx
    return text[after:end].strip()


def arxiv_id_from_filename(fname: str) -> str | None:
    m = ARXIV_ID_RE.match(fname)
    return m.group(1) if m else None


def process_pdf(pdf_path: Path) -> dict:
    doc = fitz.open(pdf_path)
    pages_text: list[str] = []
    for page in doc:
        pages_text.append(page.get_text("text"))
    raw_text = "\n".join(pages_text)
    doc.close()

    abstract = find_section(raw_text, ABSTRACT_HEADERS, SECTION_AFTER_ABSTRACT)
    ack = find_section(raw_text, ACK_HEADERS, SECTION_AFTER_ACK)

    # body: todo el texto sin abstract ni acknowledgements (aprox.). Mantenemos raw_text completo aparte.
    body = raw_text
    if abstract:
        body = body.replace(abstract, "", 1)
    if ack:
        body = body.replace(ack, "", 1)

    return {
        "arxiv_id": arxiv_id_from_filename(pdf_path.name),
        "abstract": abstract,
        "acknowledgements": ack,
        "body": body.strip(),
        "raw_text": raw_text,
        "num_pages": len(pages_text),
    }


def main() -> int:
    if not PDFS_DIR.exists():
        print(f"ERROR: no existe {PDFS_DIR}", file=sys.stderr)
        return 1

    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(PDFS_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"ERROR: no hay PDFs en {PDFS_DIR}", file=sys.stderr)
        return 1

    stats = {"total": 0, "abstract_ok": 0, "ack_ok": 0}
    for pdf_path in tqdm(pdfs, desc="Extracting"):
        aid = arxiv_id_from_filename(pdf_path.name)
        if not aid:
            print(f"  Saltado (no arXiv id): {pdf_path.name}")
            continue
        try:
            data = process_pdf(pdf_path)
        except Exception as e:
            print(f"  ERROR procesando {pdf_path.name}: {e}", file=sys.stderr)
            continue
        out_path = PAPERS_DIR / f"{aid}.json"
        with out_path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        stats["total"] += 1
        if data["abstract"]:
            stats["abstract_ok"] += 1
        if data["acknowledgements"]:
            stats["ack_ok"] += 1

    print(
        f"\nProcesados {stats['total']} papers. "
        f"Abstract detectado en {stats['abstract_ok']}; "
        f"Acknowledgements en {stats['ack_ok']}."
    )
    print(f"Salida en: {PAPERS_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
