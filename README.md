# KG-GenAI — Knowledge Graph para revisión bibliográfica de papers de IA Generativa

Trabajo del **Grupo 2** de la asignatura *Open Science and Artificial Intelligence in Research Software Engineering* (UPM, ETSI Informáticos, Ontology Engineering Group — OEG).

**Integrantes**:
- Mamoun Tahri Jautei Hassani
- Julián Alberto Villafuerte Zevallos
- Alberto Barranquero Fernández

## Caso de uso

Acelerador de **estado del arte (state of the art)** sobre IA generativa: un investigador junior con 30 papers candidatos de arXiv obtiene en minutos lo que de otra forma le llevaría 2-3 semanas de lectura manual: subáreas, papers seminales, autores referencia, modelos/datasets compartidos y panorama de financiación.

Ver [`docs/caso_de_uso.md`](docs/caso_de_uso.md) para los detalles.

## Pipeline

```
PDFs (30 papers arXiv)
        |
        v
  Extracción (texto + abstract + Acknowledgements)
        |
        v
  Topic modeling (BERTopic) ────── Similitud (sentence-transformers + cosine)
        |                                 |
        v                                 v
  NER en Acknowledgements (HuggingFace) — gold standard + métricas P/R/F1
        |
        v
  Matching contra HuggingFace Hub (Model, Dataset)
        |
        v
  Enriquecimiento (OpenAIRE, Wikidata SPARQL)
        |
        v
  Generación RDF (kg.ttl) + PROV (prov.ttl)
        |
        v
  Fuseki (endpoint SPARQL) + Streamlit (demo)
```

## Fuentes externas

- **OpenAIRE Graph** (REST) — papers, autores, organizaciones, proyectos/financiación.
- **HuggingFace Hub** (REST) — modelos y datasets.
- **Wikidata** (SPARQL) — enriquecimiento de organizaciones, topics y modelos famosos.

Detalle en [`docs/fuentes.md`](docs/fuentes.md).

## Ontología

Clases: `Paper`, `Person`, `Organization`, `Project`, `Topic`, `Venue`, `Model`, `Dataset`.
Diagrama en [`docs/diagrama/ontologia.png`](docs/diagrama/ontologia.png) (fuente editable `.drawio` en la misma carpeta).
Documentación en [`docs/ontologia.md`](docs/ontologia.md).

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

# 4. Levantar el endpoint SPARQL + la demo
docker-compose up -d
# Fuseki:    http://localhost:3030
# Streamlit: http://localhost:8501
```

## Documentación adicional

- [`docs/caso_de_uso.md`](docs/caso_de_uso.md) — caso de uso completo.
- [`docs/fuentes.md`](docs/fuentes.md) — fuentes externas y mapeo a propiedades.
- [`docs/ontologia.md`](docs/ontologia.md) — clases, propiedades, decisiones de modelado.
- [`docs/AI_DECLARATION.md`](docs/AI_DECLARATION.md) — declaración de uso de IA.
- [`docs/ner_evaluation.md`](docs/ner_evaluation.md) — comparación de modelos NER + métricas (en construcción).
- [`docs/preguntas.md`](docs/preguntas.md) — preguntas para el profesor.

## Licencia

Por determinar (probable: MIT o Apache-2.0).

## Citación

Si reutilizáis este trabajo, consultad [`CITATION.cff`](CITATION.cff) (pendiente).
