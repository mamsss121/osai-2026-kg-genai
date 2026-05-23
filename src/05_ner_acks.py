"""
05_ner_acks.py — Named Entity Recognition sobre Acknowledgements.

Compara 2 modelos NER de HuggingFace sobre las secciones de Acknowledgements de los papers
y, si existe gold standard, calcula precision/recall/F1 por modelo.

Modelos comparados:
    1. Jean-Baptiste/roberta-large-ner-english       (mencionado en sesion 11 del curso)
    2. dslim/bert-base-NER                           (alternativa estandar, mas ligera)

Salidas:
    - data/ner_results.json    : entidades detectadas por cada modelo en cada paper
    - data/ner_metrics.json    : precision/recall/F1 por modelo y tipo de entidad (si hay gold)

Gold standard: data/gold_standard_ner.jsonl (un JSON por linea con
    {"arxiv_id": "...", "text": "...", "entities": [{"start":..,"end":..,"label":"ORG"}, ...]})

Sketch initially generated with AI assistance, subsequently reviewed by the group.

Uso:
    python src/05_ner_acks.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXTRACTED_DIR = PROJECT_ROOT / "data" / "extracted"
NER_OUT = PROJECT_ROOT / "data" / "ner_results.json"
METRICS_OUT = PROJECT_ROOT / "data" / "ner_metrics.json"
GOLD_PATH = PROJECT_ROOT / "data" / "gold_standard_ner.jsonl"

MODELS = {
    "roberta-large-ner-english": "Jean-Baptiste/roberta-large-ner-english",
    "bert-base-NER": "dslim/bert-base-NER",
}

# Mapeo de etiquetas heterogeneas (los modelos pueden devolver ORG, B-ORG, I-ORG, etc.)
LABEL_NORM = {
    "PER": "PER", "B-PER": "PER", "I-PER": "PER",
    "ORG": "ORG", "B-ORG": "ORG", "I-ORG": "ORG",
    "LOC": "LOC", "B-LOC": "LOC", "I-LOC": "LOC",
    "MISC": "MISC", "B-MISC": "MISC", "I-MISC": "MISC",
}


def load_acknowledgements() -> dict[str, str]:
    """Devuelve {arxiv_id: ack_text} para papers con acknowledgements."""
    out: dict[str, str] = {}
    for p in sorted(EXTRACTED_DIR.glob("*.json")):
        with p.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        ack = data.get("acknowledgements", "").strip()
        if ack:
            out[data["arxiv_id"]] = ack
    return out


def load_gold_standard() -> dict[str, list[dict]]:
    """Carga el gold standard, formato JSONL."""
    out: dict[str, list[dict]] = {}
    if not GOLD_PATH.exists():
        return out
    with GOLD_PATH.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            out[rec["arxiv_id"]] = rec.get("entities", [])
    return out


def run_model(model_name: str, texts: dict[str, str]) -> dict[str, list[dict]]:
    """Ejecuta un modelo NER de HuggingFace sobre los textos. Devuelve {arxiv_id: [entities]}."""
    from transformers import pipeline

    print(f"Cargando modelo: {model_name}...")
    pipe = pipeline("ner", model=model_name, aggregation_strategy="simple")
    results: dict[str, list[dict]] = {}
    for aid, text in texts.items():
        # Truncar a 512 tokens aprox (~2000 chars) para no explotar el modelo
        snippet = text[:2000]
        try:
            entities = pipe(snippet)
        except Exception as e:
            print(f"  ERROR procesando {aid} con {model_name}: {e}", file=sys.stderr)
            entities = []
        results[aid] = [
            {
                "text": str(e["word"]).strip(),
                "label": LABEL_NORM.get(e.get("entity_group", e.get("entity", "")), e.get("entity_group", "")),
                "score": float(e["score"]),
                "start": int(e["start"]),
                "end": int(e["end"]),
            }
            for e in entities
        ]
    return results


def compute_metrics(
    predictions: list[dict], gold: list[dict], iou_threshold: float = 0.5
) -> dict[str, dict]:
    """
    Calcula precision/recall/F1 por etiqueta. Match si IoU(span) >= threshold y label coincide.
    Devuelve dict[label] = {precision, recall, f1, tp, fp, fn}.
    """
    tp = defaultdict(int)
    fp = defaultdict(int)
    fn = defaultdict(int)

    matched_gold = set()
    for pred in predictions:
        best_iou = 0.0
        best_idx = -1
        for gi, g in enumerate(gold):
            if gi in matched_gold:
                continue
            if g["label"] != pred["label"]:
                continue
            overlap = max(0, min(pred["end"], g["end"]) - max(pred["start"], g["start"]))
            union = max(pred["end"], g["end"]) - min(pred["start"], g["start"])
            iou = overlap / union if union > 0 else 0.0
            if iou > best_iou:
                best_iou = iou
                best_idx = gi
        if best_iou >= iou_threshold and best_idx >= 0:
            tp[pred["label"]] += 1
            matched_gold.add(best_idx)
        else:
            fp[pred["label"]] += 1

    for gi, g in enumerate(gold):
        if gi not in matched_gold:
            fn[g["label"]] += 1

    labels = set(tp.keys()) | set(fp.keys()) | set(fn.keys())
    metrics = {}
    for lab in labels:
        t, f_p, f_n = tp[lab], fp[lab], fn[lab]
        precision = t / (t + f_p) if (t + f_p) > 0 else 0.0
        recall = t / (t + f_n) if (t + f_n) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        metrics[lab] = {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "tp": t,
            "fp": f_p,
            "fn": f_n,
        }
    return metrics


def main() -> int:
    texts = load_acknowledgements()
    if not texts:
        print("ERROR: no hay acknowledgements en data/extracted/. Ejecuta 02_extract_text.py.", file=sys.stderr)
        return 1
    print(f"Cargados acknowledgements de {len(texts)} papers.")

    gold = load_gold_standard()
    print(f"Gold standard: {len(gold)} papers anotados.")

    all_results: dict[str, dict] = {}
    all_metrics: dict[str, dict] = {}

    for short, full in MODELS.items():
        results = run_model(full, texts)
        all_results[short] = results

        if gold:
            # Aplanar predicciones de papers del gold
            agg_metrics_by_label: dict[str, dict[str, int]] = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
            for aid, gold_ents in gold.items():
                if aid not in results:
                    continue
                m = compute_metrics(results[aid], gold_ents)
                for lab, v in m.items():
                    agg_metrics_by_label[lab]["tp"] += v["tp"]
                    agg_metrics_by_label[lab]["fp"] += v["fp"]
                    agg_metrics_by_label[lab]["fn"] += v["fn"]
            label_metrics = {}
            for lab, c in agg_metrics_by_label.items():
                t, f_p, f_n = c["tp"], c["fp"], c["fn"]
                p = t / (t + f_p) if (t + f_p) > 0 else 0.0
                r = t / (t + f_n) if (t + f_n) > 0 else 0.0
                f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
                label_metrics[lab] = {
                    "precision": round(p, 3),
                    "recall": round(r, 3),
                    "f1": round(f1, 3),
                    "tp": t, "fp": f_p, "fn": f_n,
                }
            # macro avg
            if label_metrics:
                avg_p = sum(v["precision"] for v in label_metrics.values()) / len(label_metrics)
                avg_r = sum(v["recall"] for v in label_metrics.values()) / len(label_metrics)
                avg_f1 = sum(v["f1"] for v in label_metrics.values()) / len(label_metrics)
                label_metrics["__macro_avg__"] = {
                    "precision": round(avg_p, 3),
                    "recall": round(avg_r, 3),
                    "f1": round(avg_f1, 3),
                }
            all_metrics[short] = label_metrics

    NER_OUT.parent.mkdir(parents=True, exist_ok=True)
    with NER_OUT.open("w", encoding="utf-8") as fh:
        json.dump(all_results, fh, ensure_ascii=False, indent=2)
    print(f"Generado {NER_OUT.name}")

    if all_metrics:
        with METRICS_OUT.open("w", encoding="utf-8") as fh:
            json.dump(all_metrics, fh, ensure_ascii=False, indent=2)
        print(f"Generado {METRICS_OUT.name}")
        print("\nMetricas por modelo:")
        for m, v in all_metrics.items():
            macro = v.get("__macro_avg__", {})
            print(f"  {m}: P={macro.get('precision','-')} R={macro.get('recall','-')} F1={macro.get('f1','-')}")
    else:
        print("\nNo hay gold standard todavia. Crea data/gold_standard_ner.jsonl para calcular metricas.")
        print("Formato: una linea por paper, ej.:")
        print('  {"arxiv_id":"2604.05571","text":"...","entities":[{"start":12,"end":34,"label":"ORG"}]}')

    return 0


if __name__ == "__main__":
    sys.exit(main())
