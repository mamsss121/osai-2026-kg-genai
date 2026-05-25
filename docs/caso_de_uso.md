# Caso de uso general

Un **estudiante o investigador** que inicia un trabajo en alguna subárea relacionada a la IA Generativa (LLMs, multimodal, agentes...). Necesita escribir el **capitulo del estado del arte** de su TFG, TFM o paper.

## Caso concreto

Estudiante de grado de ingeniería informática se plantea realizar su TFG sobre el uso de IA generativa en consultas de medicina de familia. Para ello, debe hacer una investigación profunda sobre el estado del arte de las herramientas y modelos actuales utilizados en el área de la salud. Hacerlo a mano lleva **2-3 semanas** y es muy fácil que se le escapen conexiones. 

---
**NOTE**
Por experiencia propia de los autores, añadir que es una tarea ardua, aún teniendo conocimiento del tema.
---


## Solucion propuesta

Un **Knowledge Graph (KG)** que materialice las relaciones entre los 30 papers, sus autores, organizaciones, financiacion, modelos y datasets. El investigador carga el corpus, ejecuta el pipeline y obtiene un grafo explorable mediante SPARQL desde una pequena aplicacion cliente.

Sobre ese grafo, el pipeline aplica las tecnicas vistas en clase:

- **Topic modeling** (BERTopic + HuggingFace) sobre los abstracts -> subareas (`Topic`).
- **Similitud por embeddings** del abstract (sentence-transformers) -> propiedad `similar_to`.
- **NER** (HuggingFace) sobre los Acknowledgements -> organizaciones financiadoras (`acknowledges`, `hasFundingProject`).
- **Matching texto + HuggingFace Hub** -> modelos y datasets reutilizados (`usesModel`, `usesDataset`).
- **Enriquecimiento** via OpenAIRE (proyectos y financiacion canonica) y Wikidata (pais, tipo de organizacion).

## Decisiones que habilita

El estudiante puede tomar las siguientes decisiones para estructurar su estado del arte:

1. **Estructurar el capitulo por subareas**: el topic modeling le dice cuantos sub-temas distintos contiene el corpus y como se solapan.
2. **Identificar los papers seminales** dentro del corpus: los mas conectados por `similar_to` o el centroide de cada cluster son los "imprescindibles".
3. **Detectar autores referencia**: las personas que aparecen en mas de N papers son candidatos naturales para citar repetidamente.
4. **Listar modelos y datasets compartidos**: los que aparecen en >1 paper merecen una subsección dedicada en la revisión.
5. **Ver el panorama de financiación**: detectar que proyectos publicos europeos / agencias estan detras del avance en cada subtema.
6. **Descartar redundancias**: si dos papers son muy similares y comparten autores, posiblemente baste con citar uno.

## Alcance del sistema.

Este KG **no pretende** ser representativo del estado del arte global de la IA Generativa. Trabaja sobre un corpus acotado y conocido de 30 papers seleccionados por el usuario. Las conclusiones que se extraen son **locales al corpus** (que autores estan en *este* corpus, que modelos comparten *estos* papers concretos) y no extrapolables al ecosistema mundial.


