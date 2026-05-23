"""
08_prov.py — Genera el PROV-O del pipeline.

Describe en RDF (Turtle, vocabulario prov:) la ejecucion completa: actividades, entidades
generadas/consumidas y agentes (los tres miembros del Grupo 2).

Salida:
    - data/prov.ttl

Sketch initially generated with AI assistance, subsequently reviewed by the group.

Uso:
    python src/08_prov.py
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import FOAF, PROV, RDF, RDFS, XSD

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA = PROJECT_ROOT / "data"
OUT = DATA / "prov.ttl"

EX = Namespace("https://w3id.org/oeg/grupo2/prov/")


def main() -> int:
    g = Graph()
    g.bind("prov", PROV)
    g.bind("ex", EX)
    g.bind("foaf", FOAF)

    now = dt.datetime.utcnow().replace(microsecond=0)
    started = now - dt.timedelta(hours=2)  # placeholder; en produccion timestamps reales

    # --- Agentes (Group 2) ---
    members = [
        ("mamoun", "Mamoun Tahri Jautei Hassani"),
        ("julian", "Julián Alberto Villafuerte Zevallos"),
        ("alberto", "Alberto Barranquero Fernández"),
    ]
    for slug, name in members:
        agent = EX[f"agent/{slug}"]
        g.add((agent, RDF.type, PROV.Agent))
        g.add((agent, RDF.type, FOAF.Person))
        g.add((agent, FOAF.name, Literal(name)))

    group = EX["agent/grupo2"]
    g.add((group, RDF.type, PROV.Agent))
    g.add((group, RDF.type, FOAF.Organization))
    g.add((group, FOAF.name, Literal("Grupo 2 — OS&AI in RSE, UPM")))
    for slug, _ in members:
        g.add((EX[f"agent/{slug}"], PROV.actedOnBehalfOf, group))

    # --- Entidades base (corpus + outputs) ---
    entities = {
        "corpus_pdfs": ("dataset", "Corpus of 30 arXiv PDFs"),
        "corpus_csv": ("dataset", "Metadatos del corpus (data/corpus.csv)"),
        "extracted_text": ("dataset", "Texto extraido por paper (data/extracted/*.json)"),
        "embeddings": ("dataset", "Embeddings de los abstracts (data/embeddings.npy)"),
        "topics": ("dataset", "Topicos detectados (data/topics.json + paper_topics.json)"),
        "similarity": ("dataset", "Pares similar_to (data/similarity.json)"),
        "ner_results": ("dataset", "Entidades NER en Acknowledgements (data/ner_results.json)"),
        "ner_metrics": ("dataset", "Metricas P/R/F1 del NER (data/ner_metrics.json)"),
        "enrichment": ("dataset", "Enriquecimiento OpenAIRE + HuggingFace (data/enrichment.json)"),
        "orgs_wikidata": ("dataset", "Enriquecimiento Wikidata (data/orgs_wikidata.json)"),
        "kg_ttl": ("dataset", "Knowledge Graph en Turtle (data/kg.ttl)"),
    }
    for key, (_, label) in entities.items():
        ent = EX[f"entity/{key}"]
        g.add((ent, RDF.type, PROV.Entity))
        g.add((ent, RDFS.label, Literal(label)))

    # --- Actividades del pipeline ---
    activities = [
        ("build_corpus", "01_build_corpus.py — consulta arXiv API", ["corpus_pdfs"], ["corpus_csv"]),
        ("extract_text", "02_extract_text.py — pymupdf + heuristicas", ["corpus_pdfs"], ["extracted_text"]),
        ("topic_modeling", "03_topic_modeling.py — BERTopic + sentence-transformers", ["extracted_text"], ["topics", "embeddings"]),
        ("similarity", "04_similarity.py — cosine sobre embeddings", ["embeddings"], ["similarity"]),
        ("ner", "05_ner_acks.py — comparativa NER (roberta-large + bert-base-NER)", ["extracted_text"], ["ner_results", "ner_metrics"]),
        ("enrich", "06_enrich.py — OpenAIRE + HuggingFace + Wikidata", ["corpus_csv", "extracted_text", "ner_results"], ["enrichment", "orgs_wikidata"]),
        ("build_rdf", "07_build_rdf.py — agrega todo en kg.ttl con rdflib", ["corpus_csv", "topics", "similarity", "ner_results", "enrichment", "orgs_wikidata"], ["kg_ttl"]),
    ]
    delta = (now - started) / max(len(activities), 1)
    for i, (slug, label, used, generated) in enumerate(activities):
        act = EX[f"activity/{slug}"]
        g.add((act, RDF.type, PROV.Activity))
        g.add((act, RDFS.label, Literal(label)))
        g.add((act, PROV.startedAtTime, Literal((started + delta * i).isoformat(), datatype=XSD.dateTime)))
        g.add((act, PROV.endedAtTime, Literal((started + delta * (i + 1)).isoformat(), datatype=XSD.dateTime)))
        g.add((act, PROV.wasAssociatedWith, group))
        for u in used:
            g.add((act, PROV.used, EX[f"entity/{u}"]))
        for gen in generated:
            g.add((EX[f"entity/{gen}"], PROV.wasGeneratedBy, act))
            g.add((EX[f"entity/{gen}"], PROV.wasAttributedTo, group))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(destination=str(OUT), format="turtle")
    print(f"Generado {OUT} con {len(g)} triples.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
