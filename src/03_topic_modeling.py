"""
03_topic_modeling.py — Topic modeling sobre abstracts con BERTopic + HuggingFace.

Lee los abstracts de data/extracted/*.json, entrena un modelo BERTopic con embeddings de
sentence-transformers, y vuelca:
    - data/topics.json         : metadatos por topico (id, label, top words, coherence)
    - data/paper_topics.json   : asignacion paper -> topico (con probabilidad)
    - data/topic_model/        : modelo serializado (opcional, para reuso)

Modelo elegido: 'sentence-transformers/all-MiniLM-L6-v2' (rapido, 384 dim).
Justificacion: balance entre calidad y velocidad para corpus pequenos (30 papers).

Sketch initially generated with AI assistance, subsequently reviewed by the group.

Uso:
    python src/03_topic_modeling.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXTRACTED_DIR = PROJECT_ROOT / "data" / "extracted"
TOPICS_OUT = PROJECT_ROOT / "data" / "topics.json"
PAPER_TOPICS_OUT = PROJECT_ROOT / "data" / "paper_topics.json"
MODEL_DIR = PROJECT_ROOT / "data" / "topic_model"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Con 30 papers, no podemos tener muchos topicos. Configuramos min_topic_size=2
# para permitir topicos pequenos. nr_topics='auto' deja que HDBSCAN decida.
MIN_TOPIC_SIZE = 2


def load_abstracts() -> tuple[list[str], list[str]]:
    """Devuelve (paper_ids, abstracts) leidos de data/extracted/*.json."""
    paper_ids: list[str] = []
    abstracts: list[str] = []
    for p in sorted(EXTRACTED_DIR.glob("*.json")):
        with p.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not data.get("abstract"):
            print(f"  (sin abstract): {p.name} — se omite")
            continue
        paper_ids.append(data["arxiv_id"])
        abstracts.append(data["abstract"])
    return paper_ids, abstracts


def main() -> int:
    try:
        from bertopic import BERTopic
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        print(
            f"ERROR: faltan dependencias ({e}). Instala con:\n"
            f"    pip install bertopic sentence-transformers",
            file=sys.stderr,
        )
        return 1

    paper_ids, abstracts = load_abstracts()
    if len(paper_ids) < 5:
        print(f"ERROR: solo {len(paper_ids)} abstracts disponibles, demasiado pocos.", file=sys.stderr)
        return 1
    print(f"Cargados {len(paper_ids)} abstracts.")

    # 1. Embeddings (los reutilizara tambien 04_similarity.py)
    print(f"Calculando embeddings con {EMBEDDING_MODEL}...")
    embedder = SentenceTransformer(EMBEDDING_MODEL)
    embeddings = embedder.encode(abstracts, show_progress_bar=True)

    # 2. BERTopic
    print("Entrenando BERTopic...")
    topic_model = BERTopic(
        embedding_model=embedder,
        min_topic_size=MIN_TOPIC_SIZE,
        verbose=True,
    )
    topics, probs = topic_model.fit_transform(abstracts, embeddings)

    # 3. Resumen de topicos
    topic_info = topic_model.get_topic_info()
    print("\nTopicos detectados:")
    print(topic_info.to_string(index=False))

    # 4. Volcar resultados
    topics_out: list[dict] = []
    for _, row in topic_info.iterrows():
        tid = int(row["Topic"])
        words_with_scores = topic_model.get_topic(tid)
        if not words_with_scores:
            continue
        topics_out.append(
            {
                "topic_id": tid,
                "is_outlier": tid == -1,
                "size": int(row["Count"]),
                "label": row.get("Name", ""),
                "top_words": [{"word": w, "score": float(s)} for w, s in words_with_scores],
            }
        )

    paper_topics_out: list[dict] = []
    for pid, t, p in zip(paper_ids, topics, probs):
        # `probs` puede ser un float o un vector segun la version
        if hasattr(p, "__len__") and not isinstance(p, str):
            probability = float(max(p))
        else:
            probability = float(p) if p is not None else None
        paper_topics_out.append(
            {
                "arxiv_id": pid,
                "topic_id": int(t),
                "probability": probability,
            }
        )

    TOPICS_OUT.parent.mkdir(parents=True, exist_ok=True)
    with TOPICS_OUT.open("w", encoding="utf-8") as fh:
        json.dump(topics_out, fh, ensure_ascii=False, indent=2)
    with PAPER_TOPICS_OUT.open("w", encoding="utf-8") as fh:
        json.dump(paper_topics_out, fh, ensure_ascii=False, indent=2)

    # 5. Guardar embeddings para 04_similarity (evita recalcular)
    import numpy as np

    emb_path = PROJECT_ROOT / "data" / "embeddings.npy"
    ids_path = PROJECT_ROOT / "data" / "embedding_ids.json"
    np.save(emb_path, embeddings)
    with ids_path.open("w", encoding="utf-8") as fh:
        json.dump(paper_ids, fh, ensure_ascii=False, indent=2)

    print(f"\nGenerado: {TOPICS_OUT.name}, {PAPER_TOPICS_OUT.name}, embeddings.npy")
    print(f"Topicos: {len([t for t in topics_out if not t['is_outlier']])} (+ outliers)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
