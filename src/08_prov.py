"""
08_prov.py — Genera el PROV-O del pipeline (ideal approach).

Lee data/run_log.json (capturado por cada script via _prov_logger) y produce un
grafo PROV-O completo con:
    - Timestamps reales (UTC) de inicio y fin de cada actividad.
    - Parametros usados (modelos, umbrales, endpoints) como prov:value en propiedades.
    - SHA-256 de cada entidad input/output como prov:value.
    - Tamano de fichero y conteo de items en directorios.
    - prov:SoftwareAgent por cada script + hash de commit Git.
    - Agentes humanos (3 miembros del Grupo 2) + grupo como agente colectivo.
    - prov:wasInformedBy entre actividades dependientes (cadena del pipeline).

Salida:
    - data/prov.ttl

Sketch initially generated with AI assistance, subsequently reviewed by the group.

Uso:
    python src/08_prov.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import FOAF, PROV, RDF, RDFS, XSD

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _prov_logger import start_activity, end_activity, get_log  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA = PROJECT_ROOT / "data"
OUT = DATA / "prov.ttl"

EX = Namespace("https://w3id.org/oeg/grupo2/prov/")
KG = Namespace("https://w3id.org/oeg/grupo2/ontology#")

# Mapeo actividad -> script y descripcion legible
ACTIVITY_META = {
    "build_corpus": ("01_build_corpus.py", "Construye corpus.csv consultando arXiv API."),
    "extract_text": ("02_extract_text.py", "Extrae texto estructurado de PDFs via Grobid."),
    "topic_modeling": ("03_topic_modeling.py", "Topic modeling con BERTopic + sentence-transformers."),
    "similarity": ("04_similarity.py", "Cosine similarity sobre embeddings de abstracts."),
    "ner": ("05_ner_acks.py", "NER en Acknowledgements con 2 modelos de HuggingFace."),
    "enrich": ("06_enrich.py", "Enriquecimiento via OpenAIRE Graph, HuggingFace Hub y Wikidata SPARQL."),
    "build_rdf": ("07_build_rdf.py", "Construye el KG en RDF Turtle con rdflib."),
}

# Cadena de dependencia entre actividades (B fue informada por A)
INFORMED_BY = {
    "extract_text": "build_corpus",
    "topic_modeling": "extract_text",
    "similarity": "topic_modeling",  # reusa embeddings
    "ner": "extract_text",
    "enrich": "ner",
    "build_rdf": "enrich",
}


def add_file_entity(g: Graph, file_info: dict, prefix: str = "entity") -> URIRef:
    """Crea un nodo prov:Entity para un fichero, anotando checksum/tamano/path."""
    path = file_info.get("path", "")
    slug = path.replace("/", "_").replace("\\", "_").replace(".", "_")
    uri = EX[f"{prefix}/{slug}"]
    g.add((uri, RDF.type, PROV.Entity))
    g.add((uri, RDFS.label, Literal(path)))
    g.add((uri, KG.path, Literal(path)))
    if file_info.get("type") == "file":
        if "sha256" in file_info and file_info["sha256"]:
            g.add((uri, KG.sha256, Literal(file_info["sha256"])))
        if "size_bytes" in file_info:
            g.add((uri, KG.sizeBytes, Literal(int(file_info["size_bytes"]), datatype=XSD.integer)))
    elif file_info.get("type") == "directory":
        g.add((uri, KG.fileCount, Literal(int(file_info.get("file_count", 0)), datatype=XSD.integer)))
        if "sha256_listing" in file_info:
            g.add((uri, KG.sha256Listing, Literal(file_info["sha256_listing"])))
    return uri


def main() -> int:
    # Registrar la propia actividad PROV
    start_activity(
        "make_prov",
        params={"vocabulary": "PROV-O", "format": "turtle"},
        inputs=[DATA / "run_log.json"] if (DATA / "run_log.json").exists() else [],
    )

    g = Graph()
    g.bind("prov", PROV)
    g.bind("ex", EX)
    g.bind("kg", KG)
    g.bind("foaf", FOAF)

    log = get_log()
    activities = log.get("activities", {})

    if not activities:
        print(
            "AVISO: data/run_log.json no contiene actividades.\n"
            "  Ejecuta antes los scripts 01-07 para capturar trazas reales.",
            file=sys.stderr,
        )

    # --- Agentes humanos ---
    members = [
        ("mamoun", "Mamoun Tahri Jautei Hassani"),
        ("julian", "Julián Alberto Villafuerte Zevallos"),
        ("alberto", "Alberto Barranquero Fernández"),
    ]
    group = EX["agent/grupo2"]
    g.add((group, RDF.type, PROV.Agent))
    g.add((group, RDF.type, FOAF.Organization))
    g.add((group, FOAF.name, Literal("Grupo 2 — OS&AI in RSE, UPM")))
    for slug, name in members:
        agent = EX[f"agent/{slug}"]
        g.add((agent, RDF.type, PROV.Agent))
        g.add((agent, RDF.type, FOAF.Person))
        g.add((agent, FOAF.name, Literal(name)))
        g.add((agent, PROV.actedOnBehalfOf, group))

    # --- SoftwareAgent por cada script + commit Git ---
    git_commits = {a: rec.get("git_commit", "") for a, rec in activities.items()}
    overall_commit = next((c for c in git_commits.values() if c), "")
    repo_agent = EX["agent/repo"]
    g.add((repo_agent, RDF.type, PROV.SoftwareAgent))
    g.add((repo_agent, RDFS.label, Literal("kg-genai-grupo2 source repository")))
    if overall_commit:
        g.add((repo_agent, KG.gitCommit, Literal(overall_commit)))

    for act_name, (script_name, _) in ACTIVITY_META.items():
        sw = EX[f"agent/{act_name}"]
        g.add((sw, RDF.type, PROV.SoftwareAgent))
        g.add((sw, RDFS.label, Literal(script_name)))
        g.add((sw, KG.scriptPath, Literal(f"src/{script_name}")))
        if git_commits.get(act_name):
            g.add((sw, KG.gitCommit, Literal(git_commits[act_name])))

    # --- Actividades + entidades ---
    entity_cache: dict[str, URIRef] = {}

    for act_name, rec in activities.items():
        if act_name not in ACTIVITY_META and act_name != "make_prov":
            continue

        script_name, desc = ACTIVITY_META.get(act_name, ("08_prov.py", "PROV-O generation."))
        act = EX[f"activity/{act_name}"]
        g.add((act, RDF.type, PROV.Activity))
        g.add((act, RDFS.label, Literal(f"{script_name} — {desc}")))

        if rec.get("started_at"):
            g.add((act, PROV.startedAtTime, Literal(rec["started_at"], datatype=XSD.dateTime)))
        if rec.get("ended_at"):
            g.add((act, PROV.endedAtTime, Literal(rec["ended_at"], datatype=XSD.dateTime)))

        # Atribucion
        g.add((act, PROV.wasAssociatedWith, group))
        g.add((act, PROV.wasAssociatedWith, EX[f"agent/{act_name}"]))

        # Entorno
        if rec.get("host"):
            g.add((act, KG.executionHost, Literal(rec["host"])))
        if rec.get("user"):
            g.add((act, KG.executionUser, Literal(rec["user"])))
        if rec.get("platform"):
            g.add((act, KG.platform, Literal(rec["platform"])))

        # Parametros (como kg:parameter literales tipo "key=value")
        for key, val in (rec.get("params") or {}).items():
            literal_val = json.dumps(val, ensure_ascii=False) if not isinstance(val, str) else val
            g.add((act, KG.parameter, Literal(f"{key}={literal_val}")))

        # Inputs
        for fi in rec.get("inputs") or []:
            path = fi.get("path", "")
            if not path:
                continue
            if path not in entity_cache:
                entity_cache[path] = add_file_entity(g, fi)
            g.add((act, PROV.used, entity_cache[path]))

        # Outputs
        for fi in rec.get("outputs") or []:
            path = fi.get("path", "")
            if not path:
                continue
            if path not in entity_cache:
                entity_cache[path] = add_file_entity(g, fi)
            g.add((entity_cache[path], PROV.wasGeneratedBy, act))
            g.add((entity_cache[path], PROV.wasAttributedTo, group))

    # --- Cadena wasInformedBy entre actividades ---
    for later, earlier in INFORMED_BY.items():
        if later in activities and earlier in activities:
            g.add((EX[f"activity/{later}"], PROV.wasInformedBy, EX[f"activity/{earlier}"]))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(destination=str(OUT), format="turtle")
    print(f"Generado {OUT} con {len(g)} triples.")
    print(f"  Actividades incluidas: {sum(1 for a in activities if a in ACTIVITY_META)}")
    print(f"  Entidades (ficheros): {len(entity_cache)}")
    if overall_commit:
        print(f"  Commit Git: {overall_commit[:8]}")

    end_activity("make_prov", outputs=[OUT])
    return 0


if __name__ == "__main__":
    sys.exit(main())
