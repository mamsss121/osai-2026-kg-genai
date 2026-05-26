# KG-GenAI — Knowledge Graph para revisión bibliográfica de papers de IA Generativa
[![DOI](https://zenodo.org/badge/1221481993.svg)](https://doi.org/10.5281/zenodo.20363978)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/mamsss121/osai-2026-kg-genai/actions/workflows/ci.yml/badge.svg)](https://github.com/mamsss121/osai-2026-kg-genai/actions/workflows/ci.yml)

Trabajo del **Grupo 2** de la asignatura *Open Science and Artificial Intelligence in Research Software Engineering* (UPM, ETSI Informáticos, Ontology Engineering Group — OEG).

**Integrantes**:
- Mamoun Tahri Jautei Hassani
- Julián Alberto Villafuerte Zevallos
- Alberto Barranquero Fernández


## Estructura del repositorio

```
proyecto/
├── README.md                   ← este fichero
├── requirements.txt            ← dependencias Python
├── docker-compose.yml          ← Fuseki + Streamlit
├── docs/                       ← documentación + diagrama
├── src/                        ← scripts del pipeline (01..08)
├── data/                       ← corpus.csv, kg.ttl, prov.ttl, métricas
│   ├── papers/                 ← PDFs (versionados)
│   └── extracted/              ← texto extraído por paper (ignorado en git)
├── app/                        ← demo Streamlit
└── ro-crate/                   ← empaquetado FAIR final
```

## Reproducir el experimento

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar token de OpenAIRE
cp .env.example .env
# editar .env y poner OPENAIRE_TOKEN=<tu_token>

# 3. Ejecutar el pipeline (cada paso se puede correr por separado)
python src/01_build_corpus.py        # construye data/corpus.csv
python src/02_extract_text.py        # extrae abstract + acks por PDF
python src/03_topic_modeling.py      # BERTopic
python src/04_similarity.py          # cosine similarity
python src/05_ner_acks.py            # NER + métricas P/R/F1
python src/06_enrich.py              # OpenAIRE + Wikidata + HF Hub
python src/07_build_rdf.py           # genera data/kg.ttl
python src/08_prov.py                # genera data/prov.ttl
python src/09_ro_crate.py            # genera el RO-Crate del proyecto en ./ro-crate/

# 4. Levantar el endpoint SPARQL + la demo
docker-compose up -d
# Fuseki:    http://localhost:3030
# Streamlit: http://localhost:8501
```

## Documentación adicional
- [`docs/index.md`](docs/index.md) — índice de la documentación.
- [`docs/install.md`](docs/install.md) — guía de instalación.
- [`docs/caso_de_uso.md`](docs/caso_de_uso.md) — caso de uso general y concreto.
- [`docs/ontologia.md`](docs/ontologia.md) — clases y propiedades.
- [`docs/fuentes.md`](docs/fuentes.md) — fuentes externas.
- [`docs/AI_DECLARATION.md`](docs/AI_DECLARATION.md) — declaración de uso de IA.

[Link a la documentación](https://acelerador-state-of-the-art.readthedocs.io/es/latest/)

## Presentación del trabajo

[Presentación Práctica 2](https://docs.google.com/presentation/d/1EfEEik2Q48WPJXtfNmTgQlwoBWDhxtddkxzjiKEKNS4/edit?usp=sharing)

## Citación

Si reutilizas este software, cítalo usando los metadatos de [`CITATION.cff`](CITATION.cff) o el siguiente DOI:

> Tahri Jautei Hassani, M., Villafuerte Zevallos, J. A., & Barranquero Fernández, A. (2026). *KG-GenAI: Knowledge Graph for State-of-the-Art Review of Generative AI Papers* (v1.0.0) [Software]. Zenodo. https://doi.org/10.5281/zenodo.20363978
