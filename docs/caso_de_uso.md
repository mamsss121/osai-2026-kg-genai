# Caso de uso general

Un **estudiante o investigador** inicia un trabajo en sobre el uso de IA Generativa en determinada área de conocimiento (ciencias de la salud, finanzas, marketing, negocios... ). Y necesita escribir el **capitulo del estado del arte** de su TFG, TFM o paper.

## Caso concreto

Estudiante de grado de ingeniería informática se plantea realizar su TFG sobre el uso de IA generativa en consultas de medicina de familia. Para ello, debe hacer una investigación profunda sobre el estado del arte de las herramientas y modelos actuales utilizados en el área de la salud. Hacerlo a mano lleva **2-3 semanas** y es muy fácil que se le escapen conexiones. 


## Solución propuesta

El sistema construye un Knowledge Graph que conecta los 30 papers con sus autores, organizaciones, financiación, modelos y datasets, explorable vía SPARQL desde una app cliente. El pipeline encadena Grobid (extracción), BERTopic (topic modeling), sentence-transformers (similitud), NER con HuggingFace (acknowledgements), matching contra HuggingFace Hub (modelos/datasets) y enriquecimiento final con OpenAIRE y Wikidata.

## Alcance del sistema.

Este sistema **no pretende** ser representar del estado del arte global de la IA Generativa. Trabaja sobre un corpus acotado y conocido de 30 papers seleccionados por el usuario. Las conclusiones que se extraen son **locales al corpus** (que autores estan en *este* corpus, que modelos comparten *estos* papers concretos) y no extrapolables al ecosistema mundial.
