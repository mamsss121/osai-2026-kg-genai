"""
09_ro_crate.py, Genera un RO-Crate del proyecto en ./ro-crate/.

Empaqueta los outputs del pipeline (corpus, KG, métricas) con metadatos FAIR
siguiendo el estándar RO-Crate 1.1.

Uso:
    python src/09_ro_crate.py
"""
from __future__ import annotations
import sys
from pathlib import Path
from rocrate.rocrate import ROCrate

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CRATE_DIR = PROJECT_ROOT / "ro-crate"
DATA = PROJECT_ROOT / "data"


def main() -> int:
    CRATE_DIR.mkdir(exist_ok=True)
    crate = ROCrate()

    crate.name = "KG-GenAI: Knowledge Graph for State-of-the-Art Review of Generative AI Papers"
    crate.description = (
        "Knowledge Graph construido a partir de 30 papers de arXiv sobre IA Generativa, "
        "enriquecido con OpenAIRE Graph, Wikidata y Hugging Face Hub. "
        "Incluye topic modeling, similitud entre papers y NER sobre acknowledgements."
    )
    crate.license = "https://spdx.org/licenses/MIT.html"
    crate.creator = [
        {"@id": "#mamoun", "@type": "Person", "name": "Mamoun Tahri Jautei Hassani"},
        {"@id": "#julian", "@type": "Person", "name": "Julián Alberto Villafuerte Zevallos"},
        {"@id": "#alberto", "@type": "Person", "name": "Alberto Barranquero Fernández"},
    ]

    # Anadir datasets / outputs si existen
    for fname in ["corpus.csv", "kg.ttl", "prov.ttl", "topics.json",
                  "paper_topics.json", "similarity.json", "ner_results.json",
                  "enrichment.json", "orgs_wikidata.json"]:
        f = DATA / fname
        if f.exists():
            crate.add_file(f, dest_path=f"data/{fname}")

    # Anadir scripts del pipeline
    src_dir = PROJECT_ROOT / "src"
    for s in sorted(src_dir.glob("*.py")):
        crate.add_file(s, dest_path=f"src/{s.name}")

    # Documentacion y ficheros raiz
    for fname in ["README.md", "LICENSE", "CITATION.cff", "codemeta.json",
                  "requirements.txt", "docker-compose.yml"]:
        f = PROJECT_ROOT / fname
        if f.exists():
            crate.add_file(f, dest_path=fname)

    crate.write(CRATE_DIR)
    print(f"RO-Crate escrito en: {CRATE_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())