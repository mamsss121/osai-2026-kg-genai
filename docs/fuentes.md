# Fuentes elegidas para el KG


| # | Fuente | Tipo | Endpoint | Rol en el KG |
|---|--------|------|----------|--------------|
| 1 | **OpenAIRE Graph** | REST API (JSON) | https://graph.openaire.eu/docs/apis/ | Fuente principal de metadatos de papers, autores, organizaciones afiliadas y proyectos/financiacion. |
| 2 | **HuggingFace Hub** | REST API (JSON) | https://huggingface.co/api/ | Metadatos de los **modelos** y **datasets** mencionados en los papers. |
| 3 | **Wikidata** | SPARQL | https://query.wikidata.org/sparql (y https://query-scholarly.wikidata.org/sparql) | Enriquecimiento de organizaciones, topics y modelos/datasets famosos con identificadores y etiquetas multilingues. |

---

## 1. OpenAIRE Graph (REST) 

**Endpoint base:** `https://api.openaire.eu/graph/v1/`
**Documentacion:** https://graph.openaire.eu/docs/apis/
**Autenticacion:** Personal access token gratuito (https://graph.openaire.eu/docs/apis/authentication).

**Que esperamos traer al KG:**

- Para cada `Paper`: `title`, `description` (abstract), `publicationYear`, `pid` (DOI, arXiv), `language`, `journal` (venue), `authors`.
- Para cada `Person` (autor): `fullName`, `surname`, `name`, posicion en la lista de autores, y referencias a su afiliacion.
- Para cada `Organization` (afiliacion del autor o agencia financiadora): `legalName`, `country`, `pid` (cuando hay), tipo.
- Para cada `Project` mencionado en `relProject` del paper: `title`, `acronym`, `code` (grant number), `funder` (EC, NSF, MICIU, ERC...), `fundingStream` (H2020, HORIZON, ERC StG/CoG/AdG), `startDate`, `endDate`.
- Relacion `Paper -> Project -> Funder (Organization)` con datos canonicos en lugar de cadenas crudas.

**Por que es fuente principal:**

- Es la unica fuente formalmente mencionada en clase (sesion 9) que cubre simultaneamente papers y proyectos/financiacion en un solo endpoint.
- Cobertura amplia para publicaciones de acceso abierto, especialmente las de proyectos europeos.
- Permite cerrar la propiedad `acknowledges` y `hasFundingProject` sin depender exclusivamente del NER.

**Ejemplo:**
```
GET https://api.openaire.eu/graph/v1/researchProducts?pid=10.48550/arXiv.2604.05571
Authorization: Bearer <token>
```

---

## 2. HuggingFace Hub (REST) - modelos y datasets

**Endpoint base:** `https://huggingface.co/api/`
**Documentacion:** https://huggingface.co/docs/hub/api
**Autenticacion:** No requiere token para consultas publicas.

**Que esperamos traer al KG:**

- Para cada `Model` mencionado en un paper (matching contra el cuerpo del articulo, p.ej. `meta-llama/Llama-3-8B`, `stabilityai/stable-diffusion-xl-base-1.0`, `openai/whisper-large-v3`):
  - `modelId` canonico, `pipeline_tag` (`text-generation`, `text-to-image`, `automatic-speech-recognition`...), `library_name` (`transformers`, `diffusers`...), `license`, `downloads`, `likes`, `tags`.
  - `arxiv_id` referenciado en la card del modelo (permite cerrar el enlace `Paper <-> Model` sin ambiguedad).
- Para cada `Dataset` (p.ej. `openai/gsm8k`, `lmsys/chatbot_arena_conversations`, `HuggingFaceH4/ultrafeedback_binarized`):
  - `datasetId` canonico, `task_categories`, `language`, `size_categories`, `license`.

**Por que es necesaria:** justifica formalmente el origen de las clases `Model` y `Dataset` del diagrama (feedback explicito del profesor en la entrega 1). HuggingFace es el registro de facto en el dominio GenAI.

**Ejemplos:**
```
GET https://huggingface.co/api/models/meta-llama/Llama-3-8B
GET https://huggingface.co/api/datasets/openai/gsm8k
GET https://huggingface.co/api/models?search=diffusion&limit=20
```

---

## 3. Wikidata (SPARQL)

**Endpoint:** https://query.wikidata.org/sparql (alternativo para papers: https://query-scholarly.wikidata.org/sparql).
**Autenticacion:** No requiere token.

**Que esperamos traer al KG:**

- Para cada `Organization` (Google DeepMind, OpenAI, Meta AI, Anthropic, MIT, Stanford, ETH...): `wikidataId`, etiquetas multilingues (`rdfs:label`), `country` (P17), `inception` (P571), `headquarters_location` (P159), `instance of` (P31, distinguiendo university / company / research institute / funder).
- Para cada `Topic` extraido del topic modeling (cuando se pueda mapear a una entidad Wikidata, p.ej. *Large language model* -> Q115305900): `description` multilingue, `subclassOf` (P279).
- Para grandes `Model` con entrada propia en Wikidata (GPT-4, LLaMA, Stable Diffusion): `developer` (P178), `release_date` (P577).

**Ejemplo de consulta SPARQL (pais y tipo de varias organizaciones por nombre):**
```sparql
SELECT ?org ?orgLabel ?countryLabel ?typeLabel WHERE {
  VALUES ?orgLabel { "OpenAI"@en "Meta AI"@en "DeepMind"@en }
  ?org rdfs:label ?orgLabel ;
       wdt:P17 ?country ;
       wdt:P31 ?type .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}
```

---

## Mapeo fuente -> propiedades / clases del KG

Leyenda de tags: **[OAIRE]** OpenAIRE Graph, **[HF]** HuggingFace Hub, **[WD]** Wikidata, **[INT]** procesado interno (topic modeling, similitud, NER sobre el texto del paper).

| Clase / Propiedad del KG | Fuente |
|---|---|
| `Paper.title`, `Paper.abstract`, `Paper.year`, `Paper.doi` | [OAIRE] |
| `Person.name` | [OAIRE] |
| `Organization.name` | [OAIRE] |
| `Organization.wikidataId`, `Organization.type`, `Organization.country` | [WD] |
| `Project.title`, `Project.grantNumber`, `Project.programme` | [OAIRE] |
| `Topic.label` | [INT] |
| `Topic.wikidataId` | [WD] (cuando mapeable) |
| `Venue.name` | [OAIRE] |
| `Model.modelId`, `Model.pipelineTag`, `Model.library`, `Model.license`, `Model.downloads` | [HF] |
| `Dataset.datasetId`, `Dataset.taskCategory`, `Dataset.license` | [HF] |
| `belongs_to_topic` (Paper -> Topic) | [INT] (topic modeling con BERTopic) |
| `similar_to` (Paper -> Paper) | [INT] (cosine similarity sobre embeddings) |
| `acknowledges` (Paper -> Organization) | [INT] (NER sobre Acknowledgements) |
| `hasAuthor` (Paper -> Person) | [OAIRE] |
| `hasAffiliation` (Person -> Organization) | [OAIRE] |
| `hasFundingProject` (Paper -> Project) | [OAIRE] |
| `hasFunder` (Project -> Organization) | [OAIRE] |
| `publishedIn` (Paper -> Venue) | [OAIRE] |
| `hasCountry` (Organization -> Organization) | [WD] |
| `usesModel`, `evaluatesModel` (Paper -> Model) | [INT] (matching texto + arxiv_id) + [HF] |
| `usesDataset` (Paper -> Dataset) | [INT] + [HF] |
| `developedBy` (Model -> Organization) | [HF] + [WD] |
| `publishedBy` (Dataset -> Organization) | [HF] + [WD] |
