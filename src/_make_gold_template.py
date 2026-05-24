"""
_make_gold_template.py — Genera plantilla para anotar el gold standard NER.

Selecciona los N papers (por defecto 8) que tienen acknowledgements mas largos
(mas probable que contengan entidades) y vuelca un fichero JSONL con la estructura:

    {"arxiv_id": "...", "text": "...", "entities": []}

El grupo debe rellenar `entities` con la lista de entidades observadas:

    {"arxiv_id": "...", "text": "...", "entities": [
        {"text": "European Commission", "label": "ORG"},
        {"text": "Horizon Europe", "label": "ORG"},
        {"text": "101070284", "label": "MISC"},
        {"text": "John Doe", "label": "PER"}
    ]}

Etiquetas permitidas: PER, ORG, LOC, MISC.

Tras rellenar el JSONL, 05_ner_acks.py lo usa automaticamente para calcular
precision/recall/F1 por modelo.

Sketch initially generated with AI assistance, subsequently reviewed by the group.

Uso:
    python src/_make_gold_template.py [--num 8]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXTRACTED_DIR = PROJECT_ROOT / "data" / "extracted"
OUT = PROJECT_ROOT / "data" / "gold_standard_ner.jsonl"

DEFAULT_NUM = 8


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--num", type=int, default=DEFAULT_NUM)
    args = parser.parse_args()

    if not EXTRACTED_DIR.exists():
        print(f"ERROR: no existe {EXTRACTED_DIR}", file=sys.stderr)
        return 1

    if OUT.exists():
        print(f"AVISO: ya existe {OUT}. Si quieres regenerar, borralo primero.")
        return 0

    # Cargar acks no vacios
    items: list[tuple[str, str]] = []
    for p in sorted(EXTRACTED_DIR.glob("*.json")):
        with p.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        ack = (data.get("acknowledgements") or "").strip()
        if ack:
            items.append((data["arxiv_id"], ack))

    if not items:
        print(
            "ERROR: ningun paper tiene acknowledgements no vacios.\n"
            "  Revisa que 02_extract_text.py haya funcionado.",
            file=sys.stderr,
        )
        return 1

    # Ordenar por longitud descendente y tomar los N primeros
    items.sort(key=lambda x: len(x[1]), reverse=True)
    selected = items[: args.num]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as fh:
        for aid, text in selected:
            rec = {
                "arxiv_id": aid,
                "text": text,
                "entities": [],
            }
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Plantilla generada: {OUT}")
    print(f"  {len(selected)} papers seleccionados (los de acknowledgement mas largo).")
    print(f"  Total disponibles con acks no vacios: {len(items)}.")
    print("\nProximos pasos:")
    print(f"  1. Abre {OUT.name} en un editor de texto.")
    print("  2. En cada linea, rellena el array 'entities' con las entidades")
    print('     que veas en el texto. Formato: {"text": "...", "label": "PER|ORG|LOC|MISC"}.')
    print("  3. Ejecuta de nuevo `python src/05_ner_acks.py` para obtener metricas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
