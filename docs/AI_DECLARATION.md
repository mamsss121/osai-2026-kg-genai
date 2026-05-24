# Declaracion de uso de Inteligencia Artificial

---

## Herramientas de IA utilizadas

| Herramienta | Proveedor | Uso |
|---|---|---|
| **Claude** (Anthropic) | Anthropic | Asistente conversacional para diseno, redaccion y revision. |

Adicionalmente, el pipeline **ejecuta modelos de HuggingFace** (sentence-transformers, BERTopic, NER) como parte del propio sistema. Esos modelos son la herramienta tecnica del trabajo, no un asistente, y estan documentados en `fuentes.md` y en el codigo.

## Tareas para las que se ha usado IA

### Diseño y arquitectura
- Brainstorming inicial sobre el **caso de uso** y descarte de alternativas (TTO, empresa, profesor) tras razonar sobre el tamano del corpus.
- Diseno de la **ontologia v1**: discusion sobre las clases base, sus propiedades y los vocabularios externos a reutilizar (FOAF, schema.org, DCTerms, BIBO, MLS).
- Discusion de **trade-offs** entre fuentes (OpenAIRE vs alternativas, decidir si Model/Dataset eran extensiones validas).
- Generacion inicial del **diagrama `.drawio`** en notacion Chowlk (despues editado manualmente por el grupo).

### Redaccion y documentacion
- Borradores iniciales de `README.md`, `caso_de_uso.md`, `fuentes.md`, `ontologia.md`, `preguntas.md`.
- Reescritura tras el feedback del profesor (entrega 1 -> entrega 2).
- Esta misma declaracion de IA.

### Código
- Plantillas (boilerplate) para los clientes HTTP de OpenAIRE, HuggingFace Hub y el endpoint SPARQL de Wikidata.
- Esqueletos de los scripts del pipeline (`01_build_corpus.py`, `02_extract_text.py`, `03_topic_modeling.py`, `04_similarity.py`, `05_ner_acks.py`, `06_enrich.py`, `07_build_rdf.py`, `08_prov.py`).
- Generacion de `docker-compose.yml` para levantar Fuseki + la app Streamlit.
- Sugerencias de fragmentos via Copilot durante la implementacion.

### Texto / etiquetas
- Sugerencias de **labels humanos para los topicos** generados por BERTopic (a partir de las palabras clave).
- Refinado de los **prompts** usados en el modelo NER (cuando se prueba la alternativa LLM-based mencionada en la sesion 11).

## Tareas que NO se han hecho con IA

- **Decision final** sobre el caso de uso, el stack de fuentes y la estructura de la ontologia: tomada por el grupo despues de discutir las opciones.
- **Seleccion del corpus** de 30 papers: hecha manualmente por los miembros del grupo.
- **Anotacion del gold standard** para evaluar los modelos NER: realizada manualmente por los miembros del grupo sobre 5-10 secciones de Acknowledgements (con su correspondiente inter-annotator agreement reportado).
- **Interpretacion** de los resultados de las metricas (precision/recall/F1 del NER, silhouette y coherence del topic modeling).
- **Validacion del KG generado**: comprobacion de que las triples tienen sentido y de que las URIs estan bien construidas.
- **Decisiones de modelado** en casos ambiguos (e.g., como representar el score de `similar_to`, si fusionar `usesModel`/`evaluatesModel`).
- **Preparacion y ensayo** de la presentacion oral.

## Revisión humana

Todos los outputs producidos por IA (texto, codigo, diagrama) han sido:

1. **Leidos** completamente por al menos un miembro del grupo antes de incorporarlos.
2. **Editados** cuando el contenido no encajaba con la realidad del trabajo, era generico o contenia errores.
3. **Verificados** comparando con la documentacion oficial de las fuentes (OpenAIRE API, HuggingFace docs, Wikidata) y con las transparencias de la asignatura.
4. **Aprobados** por consenso del grupo antes de subirse al repositorio.

Ningun fragmento se ha incluido sin revision.

