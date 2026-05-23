"""
01_build_corpus.py — Construye data/corpus.csv a partir de los PDFs de data/pdfs/.

Lee los nombres de fichero (formato arXiv: 2604.05571v1.pdf), extrae el arxiv_id,
consulta la API de arXiv para obtener metadatos (title, abstract, authors, primary_category,
published, doi) y los vuelca en data/corpus.csv.

Sketch initially generated with AI assistance, subsequently reviewed by the group.

Uso:
    python src/01_build_corpus.py
"""
from __future__ import annotations

import csv
import re
import time
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

import requests
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PDFS_DIR = PROJECT_ROOT / "data" / "pdfs"
CORPUS_CSV = PROJECT_ROOT / "data" / "corpus.csv"

ARXIV_API = "http://export.arxiv.org/api/query"
ARXIV_NS = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def arxiv_id_from_filename(fname: str) -> str | None:
    """Extrae el arxiv_id de un nombre de fichero tipo '2604.05571v1.pdf'."""
    m = re.match(r"^(\d{4}\.\d{4,5})(v\d+)?\.pdf$", fname)
    return m.group(1) if m else None


def fetch_arxiv_metadata(arxiv_ids: list[str]) -> dict[str, dict]:
    """Consulta arXiv API por id_list y devuelve dict {arxiv_id: metadata}."""
    out: dict[str, dict] = {}
    # arXiv API acepta hasta 100 ids por consulta; trabajamos en lotes de 25 por amabilidad
    batch_size = 25
    for i in tqdm(range(0, len(arxiv_ids), batch_size), desc="Querying arXiv"):
        batch = arxiv_ids[i : i + batch_size]
        params = {
            "id_list": ",".join(batch),
            "max_results": len(batch),
        }
        r = requests.get(ARXIV_API, params=params, timeout=30)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        for entry in root.findall("a:entry", ARXIV_NS):
            id_node = entry.find("a:id", ARXIV_NS)
            if id_node is None or id_node.text is None:
                continue
            # id viene tipo http://arxiv.org/abs/2604.05571v1
            url = id_node.text.strip()
            id_match = re.search(r"abs/(\d{4}\.\d{4,5})", url)
            if not id_match:
                continue
            aid = id_match.group(1)

            title = (entry.find("a:title", ARXIV_NS).text or "").strip().replace("\n", " ")
            abstract = (entry.find("a:summary", ARXIV_NS).text or "").strip().replace("\n", " ")
            published = (entry.find("a:published", ARXIV_NS).text or "").strip()
            authors = [
                (a.find("a:name", ARXIV_NS).text or "").strip()
                for a in entry.findall("a:author", ARXIV_NS)
            ]
            primary_category_node = entry.find("arxiv:primary_category", ARXIV_NS)
            primary_category = (
                primary_category_node.attrib.get("term")
                if primary_category_node is not None
                else ""
            )
            doi_node = entry.find("arxiv:doi", ARXIV_NS)
            doi = doi_node.text.strip() if doi_node is not None and doi_node.text else ""

            out[aid] = {
                "arxiv_id": aid,
                "title": title,
                "abstract": abstract,
                "authors": "; ".join(authors),
                "year": published[:4] if published else "",
                "published": published,
                "primary_category": primary_category,
                "doi": doi,
                "url": f"https://arxiv.org/abs/{aid}",
            }
        time.sleep(3)  # arXiv pide >= 3 segundos entre consultas
    return out


def main() -> int:
    if not PDFS_DIR.exists():
        print(f"ERROR: no existe {PDFS_DIR}", file=sys.stderr)
        return 1

    pdfs = sorted(PDFS_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"ERROR: no hay PDFs en {PDFS_DIR}", file=sys.stderr)
        return 1

    arxiv_ids: list[str] = []
    skipped: list[str] = []
    for p in pdfs:
        aid = arxiv_id_from_filename(p.name)
        if aid:
            arxiv_ids.append(aid)
        else:
            skipped.append(p.name)

    print(f"Encontrados {len(pdfs)} PDFs; {len(arxiv_ids)} con id arXiv reconocible.")
    if skipped:
        print(f"  Saltados (no parecen arXiv): {skipped}")

    metadata = fetch_arxiv_metadata(arxiv_ids)
    print(f"arXiv devolvio metadatos de {len(metadata)} papers.")

    # Escribir CSV
    fields = [
        "arxiv_id",
        "title",
        "abstract",
        "authors",
        "year",
        "published",
        "primary_category",
        "doi",
        "url",
        "pdf_path",
    ]
    CORPUS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with CORPUS_CSV.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for aid in arxiv_ids:
            row = metadata.get(aid, {"arxiv_id": aid})
            # buscar el PDF correspondiente
            matching = [p for p in pdfs if arxiv_id_from_filename(p.name) == aid]
            row["pdf_path"] = str(matching[0].relative_to(PROJECT_ROOT)) if matching else ""
            w.writerow({k: row.get(k, "") for k in fields})

    print(f"Escrito {CORPUS_CSV} con {len(arxiv_ids)} filas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
