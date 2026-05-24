# Declaración de uso de IA generativa

## Herramientas de IA generativa utilizadas

| Herramienta | Proveedor | Uso |
|---|---|---|
| **Claude** (Anthropic) | Anthropic | Asistente conversacional para redacción y código. |


## Tareas para las que se ha usado IA

### Redacción y documentación
- Borradores iniciales de `README.md`, `caso_de_uso.md`, `fuentes.md`, `ontologia.md`.
- Esta misma declaracion de IA.

### Código
- Plantillas para los clientes HTTP de OpenAIRE, HuggingFace Hub y el endpoint SPARQL de Wikidata.
- Esqueletos de los scripts del pipeline (`01_build_corpus.py`, `02_extract_text.py`, `03_topic_modeling.py`, `04_similarity.py`, `05_ner_acks.py`, `06_enrich.py`, `07_build_rdf.py`, `08_prov.py`).
- Generación de `docker-compose.yml` para levantar Fuseki + la app Streamlit.

## Tareas que NO se han hecho con IA

- **Decisión final** sobre el caso de uso, el stack de fuentes y la estructura de la ontologia: tomada por el grupo despues de discutir las opciones.
- **Selección del corpus** de 30 papers: hecha manualmente por los miembros del grupo.
- **Interpretación** de los resultados de las metricas (precision/recall/F1 del NER, silhouette y coherence del topic modeling).
- **Validación del KG generado**: comprobación de que las triples tienen sentido y de que las URIs estan bien construidas.
- **Decisiones de modelado** en casos ambiguos (e.g., como representar el score de `similar_to`, si fusionar `usesModel`/`evaluatesModel`).
- **Preparación y ensayo** de la presentacion oral.

## Revisión humana

Todos los outputs producidos por IA (texto, codigo, diagrama) han sido:

1. **Leídos** completamente por al menos un miembro del grupo antes de incorporarlos.
2. **Editados** cuando el contenido no encajaba con la realidad del trabajo, era genérico o contenia errores.
3. **Verificados** comparando con la documentacion oficial de las fuentes (OpenAIRE API, HuggingFace docs, Wikidata) y con las transparencias de la asignatura.
4. **Aprobados** por consenso del grupo antes de subirse al repositorio.

Ningún fragmento se ha incluido sin revision.

