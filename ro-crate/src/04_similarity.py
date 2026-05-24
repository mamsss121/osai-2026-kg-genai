"""
04_similarity.py — Calcula similitud por pares entre papers a partir de embeddings.

Reutiliza los embeddings calculados por 03_topic_modeling.py (data/embeddings.npy).
Para cada par (paperA, paperB) con paperA < paperB, calcula la cosine similarity
y guarda los pares por encima de un umbral.

Salida:
    - data/similarity.json : lista de {paperA, paperB, score} con score >= UMBRAL

Sketch initially generated with AI assistance, subsequently reviewed by the group.

Uso:
    python src/04_similarity.py [--threshold 0.6]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EMB_PATH = PROJECT_ROOT / "data" / "embeddings.npy"
IDS_PATH = PROJECT_ROOT / "data" / "embedding_ids.json"
SIM_OUT = PROJECT_ROOT / "data" / "similarity.json"

DEFAULT_THRESHOLD = 0.6


def cosine_matrix(embeddings: np.ndarray) -> np.ndarray:
    """Matriz NxN de cosine similarity (devuelve valores en [-1, 1])."""
    norm = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norm[norm == 0] = 1.0
    normalized = embeddings / norm
    return normalized @ normalized.T


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help=f"Umbral minimo de similitud (default {DEFAULT_THRESHOLD})",
    )
    args = parser.parse_args()

    if not EMB_PATH.exists() or not IDS_PATH.exists():
        print(
            "ERROR: faltan los embeddings. Ejecuta antes 03_topic_modeling.py.",
            file=sys.stderr,
        )
        return 1

    embeddings = np.load(EMB_PATH)
    with IDS_PATH.open("r", encoding="utf-8") as fh:
        paper_ids: list[str] = json.load(fh)
    print(f"Cargados {len(paper_ids)} embeddings de dimension {embeddings.shape[1]}.")

    sim = cosine_matrix(embeddings)

    pairs: list[dict] = []
    n = len(paper_ids)
    for i in range(n):
        for j in range(i + 1, n):
            score = float(sim[i, j])
            if score >= args.threshold:
                pairs.append(
                    {
                        "paperA": paper_ids[i],
                        "paperB": paper_ids[j],
                        "score": round(score, 4),
                    }
                )

    pairs.sort(key=lambda x: x["score"], reverse=True)

    SIM_OUT.parent.mkdir(parents=True, exist_ok=True)
    with SIM_OUT.open("w", encoding="utf-8") as fh:
        json.dump(
            {
                "threshold": args.threshold,
                "num_papers": n,
                "num_pairs_above_threshold": len(pairs),
                "pairs": pairs,
            },
            fh,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Generado {SIM_OUT} con {len(pairs)} pares (umbral={args.threshold}).")
    if pairs:
        print(f"  Top 5 pares mas similares:")
        for p in pairs[:5]:
            print(f"    {p['paperA']} <-> {p['paperB']} : {p['score']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
