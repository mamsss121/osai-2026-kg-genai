# Caso de uso general

Un **estudiante o investigador** inicia un trabajo sobre el uso de IA Generativa en determinada área de conocimiento (ciencias de la salud, finanzas, marketing, negocios... ). Y necesita escribir el **capitulo del estado del arte** de su TFG, TFM o paper.

## Caso concreto

Estudiante de grado de ingeniería informática se plantea realizar su TFG sobre el uso de IA generativa en consultas médicas. Para ello, debe hacer una investigación profunda sobre el estado del arte de las herramientas y modelos actuales utilizados en el área de la salud. Hacerlo a mano lleva **2-3 semanas** y es muy fácil que se le escapen conexiones. 


## Solución propuesta

<<<<<<< HEAD
El sistema construye un Knowledge Graph que conecta los 30 papers con sus autores, organizaciones, financiación, modelos y datasets, explorable vía SPARQL desde una app cliente. El pipeline encadena Grobid (extracción), BERTopic (topic modeling), sentence-transformers (similitud), NER con HuggingFace (acknowledgements), matching contra HuggingFace Hub (modelos/datasets) y enriquecimiento final con OpenAIRE y Wikidata.

=======
Un sistema que materialice las relaciones entre los 30 papers a través de un KG, sus autores, organizaciones, financiacion, modelos y datasets. El investigador carga el corpus, ejecuta el pipeline y obtiene un grafo explorable mediante SPARQL desde una pequena aplicacion cliente.

Sobre ese grafo, el pipeline aplica las tecnicas vistas en clase:

- **Topic modeling** (BERTopic + HuggingFace) sobre los abstracts -> subareas (`Topic`).
- **Similitud por embeddings** del abstract (sentence-transformers) -> propiedad `similar_to`.
- **NER** (HuggingFace) sobre los Acknowledgements -> organizaciones financiadoras (`acknowledges`, `hasFundingProject`).
- **Matching texto + HuggingFace** -> modelos y datasets reutilizados (`usesModel`, `usesDataset`).
- **Enriquecimiento** via OpenAIRE (proyectos y financiacion canonica) y Wikidata (pais, tipo de organización).

s
>>>>>>> 335436f86eaf1f740fa8092f8a0fead60a68957f
## Alcance del sistema.

Este sistema **no pretende** ser representar del estado del arte global de la IA Generativa. Trabaja sobre un corpus acotado seleccionado por el usuario. Las conclusiones que se extraen son **locales al corpus** y no extrapolables al ecosistema mundial.
