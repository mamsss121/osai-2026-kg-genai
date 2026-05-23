# Preguntas para el profesor

1. **Alcance del corpus.** Trabajamos con 30 papers de IA generativa libremente elegidos por el grupo, o el profesor proporcionara un listado base? Es razonable acotar el dominio a *Generative AI* (LLMs, diffusion, multimodal, RLHF, agentes, evaluacion) usando los `concepts` de OpenAlex como filtro inicial?

2. **Granularidad de `belongs_to_topic`.** Conviene crear nuestros propios `Topic` a partir del topic modeling (etiquetas auto-generadas), reutilizar los `concepts` de OpenAlex (p.ej. *Large language model*, *Diffusion model*) como Topic, o ambos en paralelo (como dos jerarquias diferentes)?

3. **Score de similitud y de pertenencia a topico.** Recomienda la asignatura RDF estandar (reificacion / clase intermedia tipo `SimilarityRelation`) o RDF* / RDF 1.2 para anotar el score sobre `similar_to` y `belongs_to_topic`?

4. **Resolucion de entidades en Acknowledgements.** Tras NER tendremos cadenas como "European Commission", "OpenAI" o "MICIU". Cual es el nivel esperado de *entity linking*: best-effort contra ROR/Wikidata/OpenAIRE, o se puede dejar como literal cuando no hay match fiable?

5. **Modelos y datasets de HuggingFace.** Es valido modelar `Model` y `Dataset` como clases especificas con propiedades `usesModel`, `evaluatesModel` y `usesDataset`, dado que el enunciado pide explicitamente usar HuggingFace? Conviene reutilizar **MLS** (https://ml-schema.github.io/) o **schema:SoftwareApplication** / **dcat:Dataset**?

6. **Reutilizacion de vocabularios.** Es preferible reutilizar al maximo terminos de schema.org / FOAF / DCTerms / BIBO / FRAPO / MLS, o se valora mejor definir un namespace propio del grupo y mapearlo via `owl:equivalentClass` / `owl:equivalentProperty`?

7. **Profundidad de `cites`.** Modelamos solamente las citas dentro del corpus (papers del corpus que se citan entre si) o tambien las salientes hacia papers externos (creando "stubs")?

8. **OpenAIRE token.** Hay alguna cuota institucional disponible o cada grupo debe registrar su propio token? Hay alternativa equivalente sin token?

9. **Endpoint final.** Para la entrega de mayo, basta con un Fuseki local desplegado en docker-compose, o se valora un despliegue publico (e.g. Zenodo + endpoint en un VPS / GitHub Actions)?
