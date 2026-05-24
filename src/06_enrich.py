"""
06_enrich.py — Enriquece el corpus consultando las 3 fuentes externas.

1. OpenAIRE Graph (REST): para cada paper por DOI o arxiv_id, busca metadatos +
   proyectos asociados (funder, grant, programme).
2. HuggingFace Hub (REST): hace matching del nombre de modelos/datasets sobre el
   cuerpo de los papers, y consulta su metadata.
3. Wikidata (SPARQL): para cada organizacion detectada, busca pais, tipo, wikidataId.

Salida:
    - data/enrichment.json : dict {arxiv_id: {openaire, hf_models, hf_datasets}}
    - data/orgs_wikidata.json : dict {orgName: {wikidataId, country, type}}

Sketch initially generated with AI assistance, subsequently reviewed by the group.

Uso:
    python src/06_enrich.py
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import requests
from tqdm import tqdm

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _prov_logger import start_activity, end_activity  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CORPUS_CSV = PROJECT_ROOT / "data" / "corpus.csv"
EXTRACTED_DIR = PROJECT_ROOT / "data" / "extracted"
NER_OUT = PROJECT_ROOT / "data" / "ner_results.json"
ENRICH_OUT = PROJECT_ROOT / "data" / "enrichment.json"
ORGS_OUT = PROJECT_ROOT / "data" / "orgs_wikidata.json"

OPENAIRE_API = "https://api.openaire.eu/graph/v1/researchProducts"
OPENAIRE_TOKEN = os.environ.get("OPENAIRE_TOKEN", "")

HF_API = "https://huggingface.co/api"
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"

# Heuristica simple para detectar menciones HF en el texto: cadenas de la forma "org/model".
HF_ID_RE = re.compile(r"\b([a-zA-Z0-9][a-zA-Z0-9_\-\.]{0,38})/([a-zA-Z0-9][a-zA-Z0-9_\-\.]{0,80})\b")


def read_corpus() -> list[dict]:
    import csv
    rows: list[dict] = []
    with CORPUS_CSV.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(row)
    return rows


# ----------------------------- OpenAIRE -----------------------------
def fetch_openaire(arxiv_id: str, doi: str) -> dict[str, Any]:
    """Consulta OpenAIRE Graph por DOI o arxiv_id."""
    headers = {}
    if OPENAIRE_TOKEN:
        headers["Authorization"] = f"Bearer {OPENAIRE_TOKEN}"
    pid_value = doi or f"arXiv.{arxiv_id}"
    params = {"pid": pid_value, "size": 1}
    try:
        r = requests.get(OPENAIRE_API, params=params, headers=headers, timeout=30)
        if r.status_code != 200:
            return {"error": f"HTTP {r.status_code}", "raw": r.text[:200]}
        data = r.json()
        items = data.get("results") or data.get("results", [])
        if not items:
            return {"found": False}
        item = items[0]
        # Reducir el item a lo que nos interesa
        return {
            "found": True,
            "openaire_id": item.get("id"),
            "title": item.get("mainTitle"),
            "language": item.get("language"),
            "publication_year": item.get("publicationDate", "")[:4],
            "authors": [
                {"name": a.get("fullName"), "rank": a.get("rank")}
                for a in item.get("authors", []) or []
            ],
            "projects": [
                {
                    "code": p.get("code"),
                    "title": p.get("title"),
                    "acronym": p.get("acronym"),
                    "funder": (p.get("funder") or {}).get("name"),
                    "funding_stream": (p.get("funder") or {}).get("fundingStream"),
                }
                for p in item.get("relatedProjects", []) or []
            ],
            "publisher": item.get("publisher"),
        }
    except Exception as e:
        return {"error": str(e)}


# ----------------------------- HuggingFace -----------------------------
def fetch_hf_model(model_id: str) -> dict[str, Any] | None:
    try:
        r = requests.get(f"{HF_API}/models/{model_id}", timeout=10)
        if r.status_code != 200:
            return None
        d = r.json()
        return {
            "modelId": d.get("modelId") or d.get("id"),
            "pipeline_tag": d.get("pipeline_tag"),
            "library_name": d.get("library_name"),
            "license": (d.get("cardData") or {}).get("license") if d.get("cardData") else None,
            "downloads": d.get("downloads"),
            "likes": d.get("likes"),
            "tags": d.get("tags", [])[:10],
        }
    except Exception:
        return None


def fetch_hf_dataset(dataset_id: str) -> dict[str, Any] | None:
    try:
        r = requests.get(f"{HF_API}/datasets/{dataset_id}", timeout=10)
        if r.status_code != 200:
            return None
        d = r.json()
        cd = d.get("cardData") or {}
        return {
            "datasetId": d.get("id"),
            "task_categories": cd.get("task_categories", []),
            "license": cd.get("license"),
            "language": cd.get("language", []),
            "size_categories": cd.get("size_categories", []),
        }
    except Exception:
        return None


def extract_hf_candidates(text: str) -> set[str]:
    """Encuentra cadenas tipo 'org/name' en el texto. Filtrar despues con HF API."""
    candidates = set()
    for m in HF_ID_RE.finditer(text or ""):
        candidates.add(f"{m.group(1)}/{m.group(2)}")
    return candidates


# ----------------------------- Wikidata -----------------------------
def query_wikidata_org(name: str) -> dict[str, Any] | None:
    """Busca una organizacion por etiqueta y devuelve wikidataId, pais, tipo."""
    name_clean = name.replace('"', '\\"').strip()
    if len(name_clean) < 3:
        return None
    query = f'''
    SELECT ?org ?orgLabel ?countryLabel ?typeLabel WHERE {{
      ?org rdfs:label "{name_clean}"@en .
      OPTIONAL {{ ?org wdt:P17 ?country . }}
      OPTIONAL {{ ?org wdt:P31 ?type . }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    LIMIT 1
    '''
    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": "KG-GenAI-Grupo2/0.1 (UPM OEG course)",
    }
    try:
        r = requests.get(
            WIKIDATA_SPARQL, params={"query": query}, headers=headers, timeout=20
        )
        if r.status_code != 200:
            return None
        data = r.json()
        bindings = data.get("results", {}).get("bindings", [])
        if not bindings:
            return None
        b = bindings[0]
        return {
            "wikidataId": b.get("org", {}).get("value", "").rsplit("/", 1)[-1],
            "country": b.get("countryLabel", {}).get("value"),
            "type": b.get("typeLabel", {}).get("value"),
        }
    except Exception:
        return None


# ----------------------------- Main -----------------------------
def main() -> int:
    if not OPENAIRE_TOKEN:
        print(
            "AVISO: OPENAIRE_TOKEN no esta definido. Las consultas a OpenAIRE pueden fallar.\n"
            "  Copia .env.example a .env y rellena el token.",
            file=sys.stderr,
        )

    rows = read_corpus()
    print(f"Corpus: {len(rows)} papers.")

    start_activity(
        "enrich",
        params={
            "sources": ["OpenAIRE Graph", "HuggingFace Hub", "Wikidata SPARQL"],
            "endpoints": {
                "openaire": OPENAIRE_API,
                "huggingface": HF_API,
                "wikidata": WIKIDATA_SPARQL,
            },
            "num_papers": len(rows),
            "openaire_authenticated": bool(OPENAIRE_TOKEN),
        },
        inputs=[CORPUS_CSV, EXTRACTED_DIR, NER_OUT if NER_OUT.exists() else CORPUS_CSV],
    )

    enrichment: dict[str, dict] = {}
    org_cache: dict[str, dict] = {}

    # Cargar resultados NER si existen (para extraer organizaciones)
    ner: dict[str, dict] = {}
    if NER_OUT.exists():
        with NER_OUT.open("r", encoding="utf-8") as fh:
            ner_data = json.load(fh)
        # Usar el primer modelo disponible
        if ner_data:
            first_model = next(iter(ner_data.keys()))
            ner = ner_data[first_model]
            print(f"Usando NER de modelo: {first_model}")

    for row in tqdm(rows, desc="OpenAIRE"):
        aid = row["arxiv_id"]
        entry: dict[str, Any] = {}
        # 1. OpenAIRE
        entry["openaire"] = fetch_openaire(aid, row.get("doi", ""))
        time.sleep(0.5)

        # 2. HuggingFace: candidatos del body
        paper_json = EXTRACTED_DIR / f"{aid}.json"
        body = ""
        if paper_json.exists():
            with paper_json.open("r", encoding="utf-8") as fh:
                body = json.load(fh).get("body", "")
        candidates = extract_hf_candidates(body)
        hf_models, hf_datasets = [], []
        for cand in list(candidates)[:30]:  # cap para evitar tormentas
            md = fetch_hf_model(cand)
            if md:
                hf_models.append(md)
                continue
            ds = fetch_hf_dataset(cand)
            if ds:
                hf_datasets.append(ds)
        entry["hf_models"] = hf_models
        entry["hf_datasets"] = hf_datasets

        enrichment[aid] = entry

    # 3. Wikidata: para cada org detectada via NER (Acknowledgements)
    for aid, entities in ner.items():
        for e in entities:
            if e.get("label") != "ORG":
                continue
            name = e["text"]
            if name in org_cache:
                continue
            res = query_wikidata_org(name)
            if res:
                org_cache[name] = res
            time.sleep(0.5)  # respect WD rate limits

    ENRICH_OUT.parent.mkdir(parents=True, exist_ok=True)
    with ENRICH_OUT.open("w", encoding="utf-8") as fh:
        json.dump(enrichment, fh, ensure_ascii=False, indent=2)
    with ORGS_OUT.open("w", encoding="utf-8") as fh:
        json.dump(org_cache, fh, ensure_ascii=False, indent=2)

    print(f"\nEnriquecimiento guardado en {ENRICH_OUT.name}")
    print(f"Organizaciones Wikidata: {len(org_cache)} resueltas, guardadas en {ORGS_OUT.name}")
    end_activity("enrich", outputs=[ENRICH_OUT, ORGS_OUT])
    return 0


if __name__ == "__main__":
    sys.exit(main())
