"""
02_extract_text.py — Extrae texto estructurado de los PDFs usando Grobid.

Para cada PDF en data/papers/, llama al endpoint HTTP de Grobid
(http://localhost:8070/api/processFulltextDocument), parsea la respuesta TEI XML
y escribe un JSON en data/extracted/<arxiv_id>.json con:
    {
        "arxiv_id": "2604.05571",
        "title": "...",
        "abstract": "...",
        "authors": [{"name": "...", "affiliations": [...]}],
        "acknowledgements": "...",
        "body": "...",
        "num_pages": N
    }

Antes de ejecutar, arranca Grobid:
    docker compose up -d grobid
    # o sin compose:
    docker run --rm --init -p 8070:8070 lfoppiano/grobid:0.8.1

Justificacion de Grobid (vs pymupdf con heuristicas):
    Las transparencias del curso (sesiones 1, 11, 12, 13) muestran Grobid como
    el paso canonico de extraccion de PDFs cientificos. Da seccionamiento
    estructurado (abstract, body, acknowledgements, references) muy superior
    a heuristicas de string-search.

Sketch initially generated with AI assistance, subsequently reviewed by the group.

Uso:
    python src/02_extract_text.py
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from xml.etree import ElementTree as ET

import requests
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _prov_logger import start_activity, end_activity  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PAPERS_DIR = PROJECT_ROOT / "data" / "papers"
EXTRACTED_DIR = PROJECT_ROOT / "data" / "extracted"

GROBID_URL = "http://localhost:8070"
GROBID_ENDPOINT = f"{GROBID_URL}/api/processFulltextDocument"

ARXIV_ID_RE = re.compile(r"^(\d{4}\.\d{4,5})(v\d+)?\.pdf$")
TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}


def arxiv_id_from_filename(fname: str) -> str | None:
    m = ARXIV_ID_RE.match(fname)
    return m.group(1) if m else None


def wait_for_grobid(timeout: int = 60) -> bool:
    """Espera a que Grobid este vivo. Devuelve True si responde antes del timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{GROBID_URL}/api/isalive", timeout=5)
            if r.status_code == 200 and r.text.strip().lower() in ("true", "ok"):
                return True
        except requests.RequestException:
            pass
        time.sleep(2)
    return False


def text_of(node: ET.Element | None) -> str:
    """Devuelve el texto plano de un nodo TEI, concatenando descendientes."""
    if node is None:
        return ""
    return " ".join((node.itertext())).strip()


def parse_tei(tei_xml: str) -> dict:
    """Parsea la respuesta TEI de Grobid y devuelve un dict normalizado."""
    root = ET.fromstring(tei_xml)

    # --- Title ---
    title_node = root.find(".//tei:fileDesc/tei:titleStmt/tei:title", TEI_NS)
    title = text_of(title_node)

    # --- Abstract ---
    abstract_node = root.find(".//tei:profileDesc/tei:abstract", TEI_NS)
    abstract = text_of(abstract_node)

    # --- Authors with affiliations ---
    authors: list[dict] = []
    for author in root.findall(".//tei:fileDesc//tei:author", TEI_NS):
        pers = author.find("tei:persName", TEI_NS)
        if pers is None:
            continue
        forename = text_of(pers.find("tei:forename", TEI_NS))
        surname = text_of(pers.find("tei:surname", TEI_NS))
        name = (forename + " " + surname).strip()
        if not name:
            continue
        affiliations = []
        for aff in author.findall("tei:affiliation", TEI_NS):
            org_names = [text_of(o) for o in aff.findall("tei:orgName", TEI_NS)]
            country = text_of(aff.find(".//tei:country", TEI_NS))
            affiliations.append(
                {
                    "orgNames": [o for o in org_names if o],
                    "country": country,
                }
            )
        authors.append({"name": name, "affiliations": affiliations})

    # --- Body (todas las secciones del cuerpo) ---
    body_parts: list[str] = []
    for div in root.findall(".//tei:text/tei:body//tei:div", TEI_NS):
        body_parts.append(text_of(div))
    body = "\n\n".join(p for p in body_parts if p)

    # --- Acknowledgements (pueden estar en back/div[@type='acknowledgement'] o body) ---
    ack_parts: list[str] = []
    for div in root.findall(".//tei:back//tei:div[@type='acknowledgement']", TEI_NS):
        ack_parts.append(text_of(div))
    for div in root.findall(".//tei:body//tei:div[@type='acknowledgement']", TEI_NS):
        ack_parts.append(text_of(div))
    # Fallback: buscar por encabezado "Acknowledgement(s)" / "Funding" en el body
    if not ack_parts:
        for div in root.findall(".//tei:text//tei:div", TEI_NS):
            head = div.find("tei:head", TEI_NS)
            head_text = text_of(head).lower()
            if any(k in head_text for k in ("acknowledg", "funding")):
                ack_parts.append(text_of(div))
    acknowledgements = "\n\n".join(p for p in ack_parts if p)

    return {
        "title": title,
        "abstract": abstract,
        "authors": authors,
        "body": body,
        "acknowledgements": acknowledgements,
    }


def process_pdf(pdf_path: Path) -> dict | None:
    """Envia un PDF a Grobid y devuelve los datos extraidos."""
    with pdf_path.open("rb") as fh:
        files = {"input": (pdf_path.name, fh, "application/pdf")}
        params = {"consolidateHeader": "1", "includeRawAffiliations": "1"}
        try:
            r = requests.post(GROBID_ENDPOINT, files=files, data=params, timeout=120)
        except requests.RequestException as e:
            print(f"  ERROR de red procesando {pdf_path.name}: {e}", file=sys.stderr)
            return None
    if r.status_code != 200:
        print(f"  ERROR Grobid {r.status_code} en {pdf_path.name}: {r.text[:200]}", file=sys.stderr)
        return None
    try:
        parsed = parse_tei(r.text)
    except ET.ParseError as e:
        print(f"  ERROR parseando TEI de {pdf_path.name}: {e}", file=sys.stderr)
        return None
    parsed["arxiv_id"] = arxiv_id_from_filename(pdf_path.name)
    return parsed


def main() -> int:
    start_activity(
        "extract_text",
        params={"tool": "Grobid", "endpoint": GROBID_URL, "options": "consolidateHeader=1, includeRawAffiliations=1"},
        inputs=[PAPERS_DIR],
    )
    if not PAPERS_DIR.exists():
        print(f"ERROR: no existe {PAPERS_DIR}", file=sys.stderr)
        return 1

    print(f"Conectando a Grobid en {GROBID_URL}...")
    if not wait_for_grobid():
        print(
            f"ERROR: Grobid no responde en {GROBID_URL}.\n"
            "  Arranca el contenedor:\n"
            "    docker compose up -d grobid\n"
            "    # o sin compose:\n"
            "    docker run --rm --init -p 8070:8070 lfoppiano/grobid:0.8.1",
            file=sys.stderr,
        )
        return 1
    print("  Grobid OK.")

    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(PAPERS_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"ERROR: no hay PDFs en {PAPERS_DIR}", file=sys.stderr)
        return 1

    stats = {"total": 0, "abstract_ok": 0, "ack_ok": 0, "auth_ok": 0}
    for pdf_path in tqdm(pdfs, desc="Grobid"):
        aid = arxiv_id_from_filename(pdf_path.name)
        if not aid:
            print(f"  Saltado (no arXiv id): {pdf_path.name}")
            continue
        data = process_pdf(pdf_path)
        if data is None:
            continue
        out_path = EXTRACTED_DIR / f"{aid}.json"
        with out_path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        stats["total"] += 1
        if data.get("abstract"):
            stats["abstract_ok"] += 1
        if data.get("acknowledgements"):
            stats["ack_ok"] += 1
        if data.get("authors"):
            stats["auth_ok"] += 1

    print(
        f"\nProcesados {stats['total']} papers. "
        f"Abstract en {stats['abstract_ok']}; "
        f"Acknowledgements en {stats['ack_ok']}; "
        f"Autores estructurados en {stats['auth_ok']}."
    )
    print(f"Salida en: {EXTRACTED_DIR}")
    end_activity("extract_text", outputs=[EXTRACTED_DIR])
    return 0


if __name__ == "__main__":
    sys.exit(main())
