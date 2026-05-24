# Instalación y uso

Esta página explica cómo desplegar el pipeline completo en local. El sistema corre como dos servicios Docker: un **Apache Jena Fuseki** que sirve el endpoint SPARQL del Knowledge Graph y una **app Streamlit** que ofrece la interfaz de usuario.

## Requisitos previos

- **Python 3.11** o superior
- **Docker** y **docker-compose**
- **Git**
- Un **token de OpenAIRE** (gratuito, ver más abajo)
- Espacio en disco: ~5 GB (los modelos de Hugging Face se descargan al primer uso)

## 1. Clonar el repositorio

```bash
git clone https://github.com/mamsss121/osai-2026-kg-genai.git
cd osai-2026-kg-genai
```

## 2. Configurar el entorno

```bash
python -m venv .venv
source .venv/bin/activate          # Linux/Mac
# .venv\Scripts\activate            # Windows

pip install -r requirements.txt
```

## 3. Configurar el token de OpenAIRE

OpenAIRE Graph requiere un token personal para usar su API REST.

1. Obtén un token en https://graph.openaire.eu/docs/apis/authentication
2. Copia el fichero de plantilla y rellénalo:

```bash
cp .env.example .env
# Edita .env y pon: OPENAIRE_TOKEN=tu_token_aquí
```

## 4. Ejecutar el pipeline

Los 9 pasos pueden lanzarse individualmente, en orden:

```bash
python src/01_build_corpus.py        # construye data/corpus.csv
python src/02_extract_text.py        # extrae abstract + acknowledgements de cada PDF
python src/03_topic_modeling.py      # topic modeling (BERTopic)
python src/04_similarity.py          # similitud coseno entre abstracts
python src/05_ner_acks.py            # NER + métricas Precision/Recall/F1
python src/06_enrich.py              # enriquecimiento con OpenAIRE, Wikidata, HF Hub
python src/07_build_rdf.py           # genera data/kg.ttl
python src/08_prov.py                # genera data/prov.ttl con provenance
python src/09_ro_crate.py            # empaqueta el experimento como RO-Crate
```

## 5. Lanzar los servicios

Con `kg.ttl` ya generado:

```bash
docker-compose up -d
```

Esto levanta dos servicios:

| Servicio | URL | Descripción |
|---|---|---|
| **Fuseki** | http://localhost:3030 | Endpoint SPARQL del KG |
| **Streamlit** | http://localhost:8501 | App de exploración |

Para parar los servicios:

```bash
docker-compose down
```

## 6. Ejemplos de consultas SPARQL

Puedes lanzar queries directamente contra Fuseki en `http://localhost:3030/kg/sparql`. Algunos ejemplos:

**Top 5 organizaciones más activas:**

\```sparql
PREFIX ns: <https://w3id.org/oeg/grupo2/ontology#>
SELECT ?org (COUNT(?paper) AS ?n) WHERE {
  ?paper a ns:Paper ;
         ns:hasAuthor ?author .
  ?author ns:affiliatedTo ?org .
}
GROUP BY ?org
ORDER BY DESC(?n)
LIMIT 5
\```

**Papers similares entre sí (similitud > 0.7):**

\```sparql
PREFIX ns: <https://w3id.org/oeg/grupo2/ontology#>
SELECT ?paperA ?paperB ?score WHERE {
  ?paperA ns:similar_to ?pair .
  ?pair ns:hasPair ?paperB ;
        ns:similarityScore ?score .
  FILTER(?score > 0.7)
}
\```

## Reproducibilidad

El experimento completo está empaquetado como **RO-Crate 1.1** en la carpeta `ro-crate/`. El RO-Crate contiene:

- Todos los scripts del pipeline (`src/01..09`)
- El corpus (`data/corpus.csv`)
- Los outputs intermedios y el `kg.ttl` final
- Metadatos FAIR (autores, licencia, descripción) en `ro-crate-metadata.json`

Para inspeccionar el RO-Crate programáticamente:

```python
from rocrate.rocrate import ROCrate
crate = ROCrate("ro-crate")
for entity in crate.data_entities:
    print(entity.id, entity.type)
```

## Troubleshooting

**Fuseki no se levanta:** comprueba que el puerto 3030 está libre con `lsof -i :3030`.

**`kg.ttl` no se ha generado:** asegúrate de haber ejecutado los pasos 01-07 en orden y de tener todos los outputs intermedios en `data/`.

**Modelos de Hugging Face se descargan muy lento:** la primera ejecución descarga ~2 GB de modelos. Las siguientes corren desde cache local en `~/.cache/huggingface/`.