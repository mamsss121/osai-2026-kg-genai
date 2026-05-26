# Ontología del proyecto

Esta ontología incluye los siguientes elementos:

- **Clases base:** `Paper`, `Person`, `Organization`, `Project`, `Topic`.
- **Clases especificas del dominio GenAI:** `Model`, `Dataset`, `Venue`.
- **Propiedades base:** `belongs_to_topic`, `similar_to`, `title`, `name`, `acknowledges`.
- **Propiedades adicionales** procedentes de fuentes externas (OpenAIRE, HuggingFace, Wikidata).


## Tags de origen de las propiedades

| Tag | Fuente | Tipo |
|---|---|---|
| **[OAIRE]** | OpenAIRE Graph | REST |
| **[HF]** | HuggingFace Hub | REST |
| **[WD]** | Wikidata | SPARQL |
| **[INT]** | Procesado interno (topic modeling, similitud, NER) | - |

## Diagrama

![Diagrama de la ontología](diagrama/ontologia.png)

Fuente editable: [`diagrama/ontologia.drawio`](diagrama/ontologia.drawio) (notación Chowlk, abrir con [diagrams.net](https://app.diagrams.net)).

## Tabla de clases

| Clase | Descripcion | Termino reutilizado (propuesta) |
|---|---|---|
| `ns:Paper` | Articulo cientifico de IA generativa. | `bibo:AcademicArticle` / `schema:ScholarlyArticle` |
| `ns:Person` | Autor o agente humano. | `foaf:Person` / `schema:Person` |
| `ns:Organization` | Institucion academica, lab, empresa, agencia financiadora, gobierno. | `foaf:Organization` / `schema:Organization` |
| `ns:Project` | Proyecto de financiacion identificado por OpenAIRE o NER en Acknowledgements. | `foaf:Project` / `frapo:Project` |
| `ns:Topic` | Tema (sub-area de GenAI) obtenido por topic modeling. | `skos:Concept` |
| `ns:Venue` | Revista o conferencia (NeurIPS, ICLR, ACL, arXiv...). | `bibo:Journal` / `schema:Periodical` |
| `ns:Model` | Modelo de ML/IA generativa publicado en HuggingFace o referenciado en el paper. | `mls:Model` / `schema:SoftwareApplication` |
| `ns:Dataset` | Dataset usado o introducido por el paper. | `dcat:Dataset` / `schema:Dataset` |

## Tabla de propiedades

### Propiedades base

| Propiedad | Dominio | Rango | Fuente | Descripcion |
|---|---|---|---|---|
| `ns:title` | `Paper` | `xsd:string` | [OAIRE] | Titulo del paper. |
| `ns:name` | `Person`, `Organization` | `xsd:string` | [OAIRE] | Nombre canonico. |
| `ns:belongs_to_topic` | `Paper` | `Topic` | [INT] | Asignacion paper-topico (varios). |
| `ns:similar_to` | `Paper` | `Paper` | [INT] | Pares con similitud sobre umbral. |
| `ns:acknowledges` | `Paper` | `Organization` | [INT] | Mencion extraida de Acknowledgements. |

### Propiedades de objeto adicionales

| Propiedad | Dominio | Rango | Fuente |
|---|---|---|---|
| `ns:hasAuthor` | `Paper` | `Person` | [OAIRE] |
| `ns:hasAffiliation` | `Person` | `Organization` | [OAIRE] |
| `ns:hasFundingProject` | `Paper` | `Project` | [OAIRE] |
| `ns:hasFunder` | `Project` | `Organization` | [OAIRE] |
| `ns:hasCountry` | `Organization` | `Organization` | [WD] |
| `ns:publishedIn` | `Paper` | `Venue` | [OAIRE] |
| `ns:usesModel` | `Paper` | `Model` | [INT] + [HF] |
| `ns:evaluatesModel` | `Paper` | `Model` | [INT] + [HF] |
| `ns:usesDataset` | `Paper` | `Dataset` | [INT] + [HF] |
| `ns:developedBy` | `Model` | `Organization` | [HF] + [WD] |
| `ns:publishedBy` | `Dataset` | `Organization` | [HF] + [WD] |

### Propiedades de datos adicionales

| Propiedad | Dominio | Rango | Fuente |
|---|---|---|---|
| `ns:abstract` | `Paper` | `xsd:string` | [OAIRE] |
| `ns:year` | `Paper` | `xsd:gYear` | [OAIRE] |
| `ns:doi` | `Paper` | `xsd:string` | [OAIRE] |
| `ns:wikidataId` | `Organization`, `Topic`, `Model` | `xsd:string` | [WD] |
| `ns:type` | `Organization` | `xsd:string` | [WD] |
| `ns:grantNumber` | `Project` | `xsd:string` | [OAIRE] |
| `ns:programme` | `Project` | `xsd:string` | [OAIRE] |
| `ns:label` | `Topic` | `xsd:string` | [INT] |
| `ns:modelId` | `Model` | `xsd:string` | [HF] |
| `ns:pipelineTag` | `Model` | `xsd:string` | [HF] |
| `ns:library` | `Model` | `xsd:string` | [HF] |
| `ns:license` | `Model`, `Dataset` | `xsd:string` | [HF] |
| `ns:downloads` | `Model` | `xsd:integer` | [HF] |
| `ns:datasetId` | `Dataset` | `xsd:string` | [HF] |
| `ns:taskCategory` | `Dataset` | `xsd:string` | [HF] |
