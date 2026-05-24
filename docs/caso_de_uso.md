# Caso de uso

Un **investigador junior** (doctorando o estudiante de master de IA) que inicia un trabajo en alguna subarea de la Inteligencia Artificial Generativa (LLMs, modelos de difusion, multimodal, RLHF, agentes, evaluacion...). Necesita escribir el **capitulo de estado del arte** de su tesis o la seccion *Related Work* del paper.

## Problema concreto

En IA generativa la velocidad de publicacion es altisima. El investigador tipico:

1. Hace una busqueda inicial en arXiv y descarga **~30 papers candidatos** que parecen relevantes.
2. Tiene que **leerlos, anotar manualmente** autores, organizaciones, modelos referenciados, financiacion, y mentalmente **agruparlos por subtemas**.
3. Identificar cuales son **centrales** (citados/usados por muchos) y cuales son **perifericos** o redundantes.
4. Detectar **modelos y datasets recurrentes** que merecen una seccion propia en la revision.

Hacerlo a mano lleva **2-3 semanas** y es muy facil que se le escapen conexiones (un autor que aparece en 4 papers de subtemas distintos, un proyecto europeo que financia 3 trabajos relacionados, un dataset que comparten 5 papers...).

## Solucion propuesta

Un **Knowledge Graph (KG)** que materialice las relaciones entre los 30 papers, sus autores, organizaciones, financiacion, modelos y datasets. El investigador carga el corpus, ejecuta el pipeline y obtiene un grafo explorable mediante SPARQL desde una pequena aplicacion cliente.

Sobre ese grafo, el pipeline aplica las tecnicas vistas en clase:

- **Topic modeling** (BERTopic + HuggingFace) sobre los abstracts -> subareas (`Topic`).
- **Similitud por embeddings** del abstract (sentence-transformers) -> propiedad `similar_to`.
- **NER** (HuggingFace) sobre los Acknowledgements -> organizaciones financiadoras (`acknowledges`, `hasFundingProject`).
- **Matching texto + HuggingFace Hub** -> modelos y datasets reutilizados (`usesModel`, `usesDataset`).
- **Enriquecimiento** via OpenAIRE (proyectos y financiacion canonica) y Wikidata (pais, tipo de organizacion).

## Decisiones que habilita

El investigador puede tomar las siguientes decisiones para estructurar su estado del arte:

1. **Estructurar el capitulo por subareas**: el topic modeling le dice cuantos sub-temas distintos contiene el corpus y como se solapan.
2. **Identificar los papers seminales** dentro del corpus: los mas conectados por `similar_to` o el centroide de cada cluster son los "imprescindibles".
3. **Detectar autores referencia**: las personas que aparecen en mas de N papers son candidatos naturales para citar repetidamente.
4. **Listar modelos y datasets compartidos**: los que aparecen en >1 paper merecen una subseccion dedicada en la revision.
5. **Ver el panorama de financiacion**: detectar que proyectos publicos europeos / agencias estan detras del avance en cada subtema.
6. **Descartar redundancias**: si dos papers son muy similares y comparten autores, posiblemente baste con citar uno.

## Preguntas competenciales (consultas SPARQL que el sistema debe responder)

1. Dado un paper P del corpus, devolver los 5 papers mas similares (`similar_to` ordenado por score).
2. Listar los papers que pertenecen al topico T y ordenarlos por numero de relaciones entrantes (centralidad).
3. Devolver los autores que aparecen en >=2 papers del corpus.
4. Listar las organizaciones que aparecen como afiliacion en mas de N papers.
5. Devolver los modelos HuggingFace que se usan o evaluan en >=2 papers.
6. Devolver los datasets HuggingFace compartidos por papers de un mismo topico.
7. Listar los proyectos (con `grantNumber` y `funder`) que financian papers del corpus.
8. Devolver los papers que comparten financiacion (mismo `hasFunder`).

## Alcance y limitaciones (honestidad sobre el corpus)

Este KG **no pretende** ser representativo del estado del arte global de la IA Generativa. Trabaja sobre un corpus acotado y conocido de 30 papers seleccionados por el usuario. Las conclusiones que se extraen son **locales al corpus** (que autores estan en *este* corpus, que modelos comparten *estos* papers concretos) y no extrapolables al ecosistema mundial.


