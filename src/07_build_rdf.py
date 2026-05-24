"""
07_build_rdf.py — Construye el Knowledge Graph en RDF (Turtle) agregando todo.

Lee:
    - data/corpus.csv
    - data/extracted/*.json
    - data/paper_topics.json + data/topics.json
    - data/similarity.json
    - data/ner_results.json
    - data/enrichment.json + data/orgs_wikidata.json

Y genera:
    - data/kg.ttl  (Turtle serializado)

Sigue la ontologia documentada en docs/ontologia.md (prefix ns:).

Sketch initially generated with AI assistance, subsequently reviewed by the group.

Uso:
    python src/07_build_rdf.py
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD, OWL

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _prov_logger import start_activity, end_activity  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA = PROJECT_ROOT / "data"

NS = Namespace("https://w3id.org/oeg/grupo2/ontology#")
RES = Namespace("https://w3id.org/oeg/grupo2/resource/")

SLUG_RE = re.compile(r"[^a-zA-Z0-9]+")


def slug(s: str) -> str:
    return SLUG_RE.sub("-", (s or "").strip()).strip("-").lower() or "unknown"


def load_json(path: Path, default=None):
    if not path.exists():
        return default if default is not None else {}
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:
    start_activity(
        "build_rdf",
        params={
            "namespace": str(NS),
            "library": "rdflib",
            "format": "turtle",
        },
        inputs=[
            DATA / "corpus.csv",
            DATA / "paper_topics.json",
            DATA / "topics.json",
            DATA / "similarity.json",
            DATA / "ner_results.json",
            DATA / "enrichment.json",
            DATA / "orgs_wikidata.json",
        ],
    )
    g = Graph()
    g.bind("ns", NS)
    g.bind("res", RES)
    g.bind("rdfs", RDFS)
    g.bind("xsd", XSD)
    g.bind("owl", OWL)

    # --- Ontology header ---
    onto_iri = URIRef("https://w3id.org/oeg/grupo2/ontology")
    g.add((onto_iri, RDF.type, OWL.Ontology))
    g.add((onto_iri, RDFS.label, Literal("KG-GenAI ontology — Grupo 2", lang="en")))
    g.add((onto_iri, OWL.versionInfo, Literal("0.2")))

    # --- Declarar clases (asercion light) ---
    for cls in ["Paper", "Person", "Organization", "Project", "Topic", "Venue", "Model", "Dataset"]:
        g.add((NS[cls], RDF.type, OWL.Class))
        g.add((NS[cls], RDFS.label, Literal(cls)))

    # --- Cargar todos los inputs ---
    corpus = []
    corpus_csv = DATA / "corpus.csv"
    if corpus_csv.exists():
        with corpus_csv.open("r", encoding="utf-8") as fh:
            corpus = list(csv.DictReader(fh))
    paper_topics = {p["arxiv_id"]: p for p in load_json(DATA / "paper_topics.json", [])}
    topics_meta = {t["topic_id"]: t for t in load_json(DATA / "topics.json", [])}
    similarity = load_json(DATA / "similarity.json", {"pairs": []}).get("pairs", [])
    ner_all = load_json(DATA / "ner_results.json", {})
    enrichment = load_json(DATA / "enrichment.json", {})
    orgs_wd = load_json(DATA / "orgs_wikidata.json", {})

    # Usar el primer modelo NER para acknowledges
    ner = {}
    if ner_all:
        first_model = next(iter(ner_all.keys()))
        ner = ner_all[first_model]

    # --- Caches de URIs ---
    org_uri: dict[str, URIRef] = {}
    person_uri: dict[str, URIRef] = {}
    project_uri: dict[str, URIRef] = {}
    venue_uri: dict[str, URIRef] = {}
    model_uri: dict[str, URIRef] = {}
    dataset_uri: dict[str, URIRef] = {}
    topic_uri: dict[int, URIRef] = {}

    def get_org(name: str) -> URIRef:
        key = name.strip()
        if key not in org_uri:
            uri = RES[f"org/{slug(key)}"]
            g.add((uri, RDF.type, NS.Organization))
            g.add((uri, NS.name, Literal(key)))
            org_uri[key] = uri
            # enriquecimiento Wikidata
            wd = orgs_wd.get(key)
            if wd:
                if wd.get("wikidataId"):
                    g.add((uri, NS.wikidataId, Literal(wd["wikidataId"])))
                if wd.get("country"):
                    country_key = f"country:{wd['country']}"
                    if country_key not in org_uri:
                        c_uri = RES[f"org/{slug(country_key)}"]
                        g.add((c_uri, RDF.type, NS.Organization))
                        g.add((c_uri, NS.name, Literal(wd["country"])))
                        g.add((c_uri, NS.type, Literal("Country")))
                        org_uri[country_key] = c_uri
                    g.add((uri, NS.hasCountry, org_uri[country_key]))
                if wd.get("type"):
                    g.add((uri, NS.type, Literal(wd["type"])))
        return org_uri[key]

    def get_person(name: str) -> URIRef:
        key = name.strip()
        if key not in person_uri:
            uri = RES[f"person/{slug(key)}"]
            g.add((uri, RDF.type, NS.Person))
            g.add((uri, NS.name, Literal(key)))
            person_uri[key] = uri
        return person_uri[key]

    def get_project(code: str, title: str, funder: str, programme: str | None) -> URIRef:
        key = code or title
        if key not in project_uri:
            uri = RES[f"project/{slug(key)}"]
            g.add((uri, RDF.type, NS.Project))
            if code:
                g.add((uri, NS.grantNumber, Literal(code)))
            if title:
                g.add((uri, NS.title, Literal(title)))
            if programme:
                g.add((uri, NS.programme, Literal(programme)))
            if funder:
                g.add((uri, NS.hasFunder, get_org(funder)))
            project_uri[key] = uri
        return project_uri[key]

    def get_venue(name: str) -> URIRef:
        key = name.strip()
        if key not in venue_uri:
            uri = RES[f"venue/{slug(key)}"]
            g.add((uri, RDF.type, NS.Venue))
            g.add((uri, NS.name, Literal(key)))
            venue_uri[key] = uri
        return venue_uri[key]

    def get_topic(tid: int) -> URIRef:
        if tid not in topic_uri:
            uri = RES[f"topic/{tid}"]
            g.add((uri, RDF.type, NS.Topic))
            meta = topics_meta.get(tid, {})
            label = meta.get("label", f"Topic {tid}")
            g.add((uri, NS.label, Literal(label)))
            topic_uri[tid] = uri
        return topic_uri[tid]

    def get_model(d: dict) -> URIRef:
        mid = d.get("modelId")
        if not mid:
            return None
        if mid not in model_uri:
            uri = RES[f"model/{slug(mid)}"]
            g.add((uri, RDF.type, NS.Model))
            g.add((uri, NS.modelId, Literal(mid)))
            if d.get("pipeline_tag"):
                g.add((uri, NS.pipelineTag, Literal(d["pipeline_tag"])))
            if d.get("library_name"):
                g.add((uri, NS.library, Literal(d["library_name"])))
            if d.get("license"):
                g.add((uri, NS.license, Literal(str(d["license"]))))
            if d.get("downloads") is not None:
                g.add((uri, NS.downloads, Literal(int(d["downloads"]), datatype=XSD.integer)))
            # developedBy heuristica: la parte antes del / suele ser la organizacion
            owner = mid.split("/")[0]
            g.add((uri, NS.developedBy, get_org(owner)))
            model_uri[mid] = uri
        return model_uri[mid]

    def get_dataset(d: dict) -> URIRef:
        did = d.get("datasetId")
        if not did:
            return None
        if did not in dataset_uri:
            uri = RES[f"dataset/{slug(did)}"]
            g.add((uri, RDF.type, NS.Dataset))
            g.add((uri, NS.datasetId, Literal(did)))
            cats = d.get("task_categories") or []
            for c in cats[:5]:
                g.add((uri, NS.taskCategory, Literal(str(c))))
            if d.get("license"):
                g.add((uri, NS.license, Literal(str(d["license"]))))
            owner = did.split("/")[0]
            g.add((uri, NS.publishedBy, get_org(owner)))
            dataset_uri[did] = uri
        return dataset_uri[did]

    # --- Topics ---
    for tid, meta in topics_meta.items():
        get_topic(int(tid))

    # --- Papers + relaciones ---
    for row in corpus:
        aid = row["arxiv_id"]
        paper = RES[f"paper/{aid}"]
        g.add((paper, RDF.type, NS.Paper))
        if row.get("title"):
            g.add((paper, NS.title, Literal(row["title"])))
        if row.get("abstract"):
            g.add((paper, NS.abstract, Literal(row["abstract"])))
        if row.get("year"):
            try:
                g.add((paper, NS.year, Literal(row["year"], datatype=XSD.gYear)))
            except Exception:
                pass
        if row.get("doi"):
            g.add((paper, NS.doi, Literal(row["doi"])))
        # autores via OpenAIRE (mejor canonicalizacion); fallback a la columna 'authors'
        oa = enrichment.get(aid, {}).get("openaire", {}) or {}
        if oa.get("authors"):
            for a in oa["authors"]:
                if a.get("name"):
                    g.add((paper, NS.hasAuthor, get_person(a["name"])))
        elif row.get("authors"):
            for name in (n.strip() for n in row["authors"].split(";") if n.strip()):
                g.add((paper, NS.hasAuthor, get_person(name)))

        # Venue (placeholder via primary_category de arXiv)
        if row.get("primary_category"):
            g.add((paper, NS.publishedIn, get_venue(row["primary_category"])))

        # Topic
        pt = paper_topics.get(aid)
        if pt is not None and pt.get("topic_id") is not None:
            g.add((paper, NS.belongs_to_topic, get_topic(int(pt["topic_id"]))))

        # OpenAIRE projects -> Project
        for p in oa.get("projects", []) or []:
            proj = get_project(
                p.get("code") or "",
                p.get("title") or "",
                p.get("funder") or "",
                p.get("funding_stream"),
            )
            g.add((paper, NS.hasFundingProject, proj))

        # NER acknowledges -> Organization
        for ent in ner.get(aid, []) or []:
            if ent.get("label") == "ORG" and ent.get("text"):
                g.add((paper, NS.acknowledges, get_org(ent["text"])))

        # HuggingFace models / datasets
        for m in enrichment.get(aid, {}).get("hf_models", []) or []:
            uri = get_model(m)
            if uri:
                g.add((paper, NS.usesModel, uri))
        for d in enrichment.get(aid, {}).get("hf_datasets", []) or []:
            uri = get_dataset(d)
            if uri:
                g.add((paper, NS.usesDataset, uri))

    # --- Similar_to ---
    for pair in similarity:
        a = RES[f"paper/{pair['paperA']}"]
        b = RES[f"paper/{pair['paperB']}"]
        g.add((a, NS.similar_to, b))
        g.add((b, NS.similar_to, a))

    out_ttl = DATA / "kg.ttl"
    g.serialize(destination=str(out_ttl), format="turtle")
    print(f"Generado {out_ttl} con {len(g)} triples.")
    end_activity("build_rdf", outputs=[out_ttl])
    return 0


if __name__ == "__main__":
    sys.exit(main())
