# Práctica 2 - IA y Ciencia Abierta en RSE

**Acelerador del estado del arte en Inteligencia Artificial Generativa.**

Knowledge Graph construido a partir de un corpus de 30 papers de arXiv sobre IA generativa, enriquecido con datos de OpenAIRE Graph, Wikidata y Hugging Face Hub. Permite obtener en minutos lo que de otra forma llevaría 2-3 semanas de lectura manual: subáreas, papers seminales, autores referencia, modelos/datasets compartidos y panorama de financiación.

[![DOI](https://zenodo.org/badge/1221481993.svg)](https://doi.org/10.5281/zenodo.20363978)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/mamsss121/osai-2026-kg-genai/blob/main/LICENSE)

## ¿Qué hace este proyecto?

Dado un corpus de 30 PDFs de arXiv sobre Gen AI, el pipeline:

1. **Extrae** metadatos canónicos de arXiv (título, abstract, autores, DOI)
2. **Procesa** los PDFs para obtener abstracts y secciones de Acknowledgements
3. **Agrupa** los papers por subtemas usando topic modeling (BERTopic + sentence-transformers)
4. **Calcula similitud** entre papers basada en embeddings de abstracts
5. **Detecta entidades** (organizaciones, proyectos, financiación) en los Acknowledgements con NER
6. **Enriquece** la información con OpenAIRE, Wikidata y Hugging Face Hub
7. **Construye un Knowledge Graph** en RDF/Turtle y lo expone vía SPARQL en Apache Jena Fuseki

## Caso de uso

Un estudiante o investigador inicia un trabajo sobre el uso de IA Generativa y quiere escribir el capítulo de *state of the art* de su tesis. Tiene 30 papers candidatos pero no tiempo de leerlos todos. Con este sistema obtiene de forma automática las preguntas clave de su revisión: ¿qué sub-áreas dominan? ¿qué papers son redundantes entre sí? ¿qué modelos/datasets aparecen recurrentemente? ¿qué financiación los sostiene?

[Ver caso de uso completo →](caso_de_uso.md)

## Documentación

- [Instalación](install.md)
- [Caso de uso](caso_de_uso.md)
- [Ontología](ontologia.md)
- [Fuentes](fuentes.md)
- [Declaración de IA](AI_DECLARATION.md)

## Repositorio y citación

- **Código:** https://github.com/mamsss121/osai-2026-kg-genai
- **DOI:** [10.5281/zenodo.20363978](https://doi.org/10.5281/zenodo.20363978)
- **Citación:** ver [CITATION.cff](https://github.com/mamsss121/osai-2026-kg-genai/blob/main/CITATION.cff)

## Equipo

Trabajo del **Grupo 2** de la asignatura *Open Science and Artificial Intelligence in Research Software Engineering*, UPM ETSI Informáticos, Ontology Engineering Group (OEG):

- Mamoun Tahri Jautei Hassani
- Julián Alberto Villafuerte Zevallos
- Alberto Barranquero Fernández
