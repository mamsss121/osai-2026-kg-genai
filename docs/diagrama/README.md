# Diagrama de la ontologia

Este directorio contiene el diagrama de la ontologia en formatos editables y exportados.

## Ficheros previstos
- `ontologia.drawio` - Fuente editable en diagrams.net (recomendado por el profesor).
- `ontologia.png` - Exportacion en imagen para incluir en la entrega.
- `ontologia.svg` - Exportacion vectorial.
- `ontologia-chowlk.xml` *(opcional)* - Si decidimos usar [Chowlk](https://github.com/oeg-upm/Chowlk) para generar la TTL automaticamente.

## Como construirlo
1. Abrir https://app.diagrams.net (diagrams.net).
2. Empezar desde el diagrama Mermaid de [`../ontologia.md`](../ontologia.md) como referencia visual.
3. Usar la **plantilla de Chowlk** (https://chowlk.linkeddata.es/notation.html) para que las cajas y flechas sigan la convencion esperada por el profesor:
   - Clases: rectangulos amarillos con borde negro.
   - Propiedades de objeto: flechas azules con etiqueta `:propiedad`.
   - Propiedades de datos: rectangulos blancos conectados con `--`.
   - Tipos de dato (xsd:string, xsd:integer...) entre comillas.
4. Guardar el `.drawio` en este directorio y exportar a `.png` y `.svg` (Archivo -> Exportar como...).
5. *(Opcional)* Pasar el `.drawio` por [Chowlk](https://github.com/oeg-upm/Chowlk) para generar un primer borrador de la ontologia en Turtle.

## Recordatorio
- El diagrama debe contener al menos las **5 clases base** (`Paper`, `Person`, `Organization`, `Project`, `Topic`) y las **propiedades base** (`title`, `name`, `belongs_to_topic`, `similar_to`, `acknowledges`).
- Hay que mostrar **>=5 propiedades adicionales** procedentes de KGs externos.
- Incluir **propiedades de datos** (no solo relaciones entre clases).
