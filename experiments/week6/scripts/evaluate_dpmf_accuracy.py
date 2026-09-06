import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path


LIVE_RESULT_PATH = Path(
    "experiments/week6/results/live/live_drift_cases.json"
)

STABLE_REPEAT_PATH = Path(
    "experiments/week6/results/live/S0_repeat_live.json"
)

RESULT_PATH = Path(
    "experiments/week6/results/dpmf_detection_metrics.json"
)

DETAIL_CSV_PATH = Path(
    "experiments/week6/results/dpmf_detection_details.csv"
)


# Fixed before evaluation.
# This is NOT tuned using the test labels.
BEHAVIOR_DRIFT_THRESHOLD = 0.40


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Required result file does not exist: {path}"
        )

    return json.loads(
        path.read_text(encoding="utf-8")
    )


def jaccard_similarity(ids_a, ids_b):
    set_a = set(ids_a)
    set_b = set(ids_b)

    union = set_a | set_b

    if not union:
        return 1.0

    return len(set_a & set_b) / len(union)


def detect_structural_drift(reference, candidate):
    topk_changed = (
        candidate["top_k"]
        != reference["top_k"]
    )

    policy_changed = (
        candidate["retrieval_policy"]
        != reference["retrieval_policy"]
    )

    if topk_changed and policy_changed:
        drift_type = "combined"

    elif topk_changed:
        drift_type = "retrieval_topk"

    elif policy_changed:
        drift_type = "retrieval_policy"

    else:
        drift_type = "none"

    return {
        "detected": drift_type != "none",
        "drift_type": drift_type,
        "topk_changed": topk_changed,
        "policy_changed": policy_changed,
    }


def safe_div(a, b):
    return a / b if b else 0.0


def binary_metrics(records, prediction_key):
    tp = sum(
        item["expected_drift"]
        and item[prediction_key]
        for item in records
    )

    tn = sum(
        not item["expected_drift"]
        and not item[prediction_key]
        for item in records
    )

    fp = sum(
        not item["expected_drift"]
        and item[prediction_key]
        for item in records
    )

    fn = sum(
        item["expected_drift"]
        and not item[prediction_key]
        for item in records
    )

    total = tp + tn + fp + fn

    accuracy = safe_div(tp + tn, total)
    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)

    f1 = safe_div(
        2 * precision * recall,
        precision + recall,
    )

    false_positive_rate = safe_div(
        fp,
        fp + tn,
    )

    specificity = safe_div(
        tn,
        tn + fp,
    )

    return {
        "TP": tp,
        "TN": tn,
        "FP": fp,
        "FN": fn,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "false_positive_rate": round(
            false_positive_rate,
            4,
        ),
        "specificity": round(
            specificity,
            4,
        ),
    }


def main():
    live_data = load_json(
        LIVE_RESULT_PATH
    )

    stable_repeat_data = load_json(
        STABLE_REPEAT_PATH
    )

    live_trials = live_data["trials"]
    stable_repeat_trials = (
        stable_repeat_data["trials"]
    )

    # --------------------------------------------------------
    # Original S0 is the reference architecture / behavior.
    # It is NOT part of the test set.
    # --------------------------------------------------------
    reference_trials = [
        item
        for item in live_trials
        if item["condition"] == "S0_stable"
    ]

    reference_map = {}

    for item in reference_trials:
        key = (
            item["group"],
            item["query_id"],
        )

        reference_map[key] = item

    if len(reference_map) != 10:
        raise RuntimeError(
            "Expected exactly 10 S0 reference samples, "
            f"found {len(reference_map)}"
        )

    # --------------------------------------------------------
    # Test set:
    # 10 new stable controls + 40 drift samples.
    # --------------------------------------------------------
    drift_trials = [
        item
        for item in live_trials
        if item["condition"] != "S0_stable"
    ]

    test_trials = (
        stable_repeat_trials
        + drift_trials
    )

    if len(test_trials) != 50:
        raise RuntimeError(
            "Expected 50 test samples, "
            f"found {len(test_trials)}"
        )

    evaluation_records = []

    for candidate in test_trials:
        key = (
            candidate["group"],
            candidate["query_id"],
        )

        if key not in reference_map:
            raise RuntimeError(
                f"No matching S0 reference for {key}"
            )

        reference = reference_map[key]

        # ----------------------------------------------------
        # 1. Structural detector
        # ----------------------------------------------------
        structural = detect_structural_drift(
            reference=reference,
            candidate=candidate,
        )

        # ----------------------------------------------------
        # 2. Retrieval behavior detector
        # ----------------------------------------------------
        similarity = jaccard_similarity(
            reference["used_memory_ids"],
            candidate["used_memory_ids"],
        )

        instability = 1.0 - similarity

        behavior_detected = (
            instability
            >= BEHAVIOR_DRIFT_THRESHOLD
        )

        # ----------------------------------------------------
        # 3. Fused DPMF signal
        #
        # Architecture changes have direct semantic meaning.
        # Behavioral instability is supplementary evidence.
        # ----------------------------------------------------
        fused_detected = (
            structural["detected"]
            or behavior_detected
        )

        if structural["detected"]:
            fused_type = structural["drift_type"]

        elif behavior_detected:
            fused_type = "retrieval_behavior"

        else:
            fused_type = "none"

        expected_drift = bool(
            candidate.get(
                "expected_drift",
                False,
            )
        )

        ground_truth_type = candidate.get(
            "ground_truth_drift_type",
            "none",
        )

        type_correct = (
            structural["drift_type"]
            == ground_truth_type
        )

        record = {
            "condition": candidate["condition"],
            "group": candidate["group"],
            "query_id": candidate["query_id"],
            "query": candidate["query"],

            "reference_top_k": (
                reference["top_k"]
            ),
            "candidate_top_k": (
                candidate["top_k"]
            ),

            "reference_policy": (
                reference["retrieval_policy"]
            ),
            "candidate_policy": (
                candidate["retrieval_policy"]
            ),

            "reference_memory_ids": (
                reference["used_memory_ids"]
            ),
            "candidate_memory_ids": (
                candidate["used_memory_ids"]
            ),

            "jaccard_similarity": round(
                similarity,
                4,
            ),
            "retrieval_instability": round(
                instability,
                4,
            ),

            "expected_drift": expected_drift,
            "ground_truth_type": (
                ground_truth_type
            ),

            "structural_detected": (
                structural["detected"]
            ),
            "structural_type": (
                structural["drift_type"]
            ),
            "structural_type_correct": (
                type_correct
            ),

            "behavior_detected": (
                behavior_detected
            ),

            "fused_detected": (
                fused_detected
            ),
            "fused_type": fused_type,

            "topk_changed": (
                structural["topk_changed"]
            ),
            "policy_changed": (
                structural["policy_changed"]
            ),

            "poison_hit_at_k": candidate.get(
                "poison_hit_at_k"
            ),
            "final_attack_success": (
                candidate.get(
                    "attack_success"
                )
            ),
        }

        evaluation_records.append(record)

    # --------------------------------------------------------
    # Overall metrics
    # --------------------------------------------------------
    structural_metrics = binary_metrics(
        evaluation_records,
        "structural_detected",
    )

    behavioral_metrics = binary_metrics(
        evaluation_records,
        "behavior_detected",
    )

    fused_metrics = binary_metrics(
        evaluation_records,
        "fused_detected",
    )

    # --------------------------------------------------------
    # Structural drift-type classification accuracy.
    # Calculate on all samples and drift samples separately.
    # --------------------------------------------------------
    overall_type_correct = sum(
        item["structural_type_correct"]
        for item in evaluation_records
    )

    drift_records = [
        item
        for item in evaluation_records
        if item["expected_drift"]
    ]

    drift_type_correct = sum(
        item["structural_type_correct"]
        for item in drift_records
    )

    type_metrics = {
        "overall_type_accuracy": round(
            safe_div(
                overall_type_correct,
                len(evaluation_records),
            ),
            4,
        ),
        "drift_only_type_accuracy": round(
            safe_div(
                drift_type_correct,
                len(drift_records),
            ),
            4,
        ),
    }

    # --------------------------------------------------------
    # Per-condition detection.
    # --------------------------------------------------------
    condition_records = defaultdict(list)

    for item in evaluation_records:
        condition_records[
            item["condition"]
        ].append(item)

    per_condition = {}

    for condition_name, items in (
        condition_records.items()
    ):
        avg_similarity = safe_div(
            sum(
                item["jaccard_similarity"]
                for item in items
            ),
            len(items),
        )

        avg_instability = safe_div(
            sum(
                item["retrieval_instability"]
                for item in items
            ),
            len(items),
        )

        structural_rate = safe_div(
            sum(
                item["structural_detected"]
                for item in items
            ),
            len(items),
        )

        behavior_rate = safe_div(
            sum(
                item["behavior_detected"]
                for item in items
            ),
            len(items),
        )

        fused_rate = safe_div(
            sum(
                item["fused_detected"]
                for item in items
            ),
            len(items),
        )

        per_condition[condition_name] = {
            "samples": len(items),
            "expected_drift": (
                items[0]["expected_drift"]
            ),
            "ground_truth_type": (
                items[0]["ground_truth_type"]
            ),
            "avg_jaccard_similarity": round(
                avg_similarity,
                4,
            ),
            "avg_retrieval_instability": round(
                avg_instability,
                4,
            ),
            "structural_detection_rate": round(
                structural_rate,
                4,
            ),
            "behavior_detection_rate": round(
                behavior_rate,
                4,
            ),
            "fused_detection_rate": round(
                fused_rate,
                4,
            ),
        }

    # --------------------------------------------------------
    # Clean / poisoned behavioral comparison.
    # --------------------------------------------------------
    per_group = {}

    for group_name in ["clean", "poisoned"]:
        items = [
            item
            for item in evaluation_records
            if item["group"] == group_name
        ]

        avg_instability = safe_div(
            sum(
                item["retrieval_instability"]
                for item in items
            ),
            len(items),
        )

        behavior_detection_rate = safe_div(
            sum(
                item["behavior_detected"]
                for item in items
            ),
            len(items),
        )

        per_group[group_name] = {
            "samples": len(items),
            "avg_retrieval_instability": round(
                avg_instability,
                4,
            ),
            "behavior_detection_rate": round(
                behavior_detection_rate,
                4,
            ),
        }

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------
    result = {
        "experiment": (
            "week6_dpmf_detection_evaluation"
        ),
        "created_at": (
            datetime.now()
            .astimezone()
            .isoformat()
        ),
        "reference_condition": "S0_stable",
        "reference_samples": (
            len(reference_trials)
        ),
        "test_samples": len(
            evaluation_records
        ),
        "test_composition": {
            "stable_negative_samples": len(
                [
                    item
                    for item in evaluation_records
                    if not item["expected_drift"]
                ]
            ),
            "drift_positive_samples": len(
                drift_records
            ),
        },
        "behavior_drift_threshold": (
            BEHAVIOR_DRIFT_THRESHOLD
        ),
        "metrics": {
            "structural_detection": (
                structural_metrics
            ),
            "behavioral_detection": (
                behavioral_metrics
            ),
            "fused_dpmf_detection": (
                fused_metrics
            ),
            "drift_type_classification": (
                type_metrics
            ),
        },
        "per_condition": per_condition,
        "per_group": per_group,
        "details": evaluation_records,
    }

    RESULT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    RESULT_PATH.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # CSV for later plotting / report.
    # --------------------------------------------------------
    fieldnames = [
        "condition",
        "group",
        "query_id",
        "expected_drift",
        "ground_truth_type",
        "candidate_top_k",
        "candidate_policy",
        "jaccard_similarity",
        "retrieval_instability",
        "structural_detected",
        "structural_type",
        "behavior_detected",
        "fused_detected",
        "fused_type",
        "poison_hit_at_k",
        "final_attack_success",
    ]

    with DETAIL_CSV_PATH.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for item in evaluation_records:
            writer.writerow(
                {
                    field: item.get(field)
                    for field in fieldnames
                }
            )

    print()
    print("=" * 80)
    print("DPMF DETECTION EVALUATION")
    print("=" * 80)

    print()
    print("Reference samples:", len(reference_trials))
    print("Test samples:", len(evaluation_records))
    print(
        "Behavior threshold:",
        BEHAVIOR_DRIFT_THRESHOLD,
    )

    print()
    print("--- STRUCTURAL DETECTION ---")
    print(
        json.dumps(
            structural_metrics,
            ensure_ascii=False,
            indent=2,
        )
    )

    print()
    print("--- BEHAVIORAL DETECTION ---")
    print(
        json.dumps(
            behavioral_metrics,
            ensure_ascii=False,
            indent=2,
        )
    )

    print()
    print("--- FUSED DPMF DETECTION ---")
    print(
        json.dumps(
            fused_metrics,
            ensure_ascii=False,
            indent=2,
        )
    )

    print()
    print("--- DRIFT TYPE CLASSIFICATION ---")
    print(
        json.dumps(
            type_metrics,
            ensure_ascii=False,
            indent=2,
        )
    )

    print()
    print("--- PER CONDITION ---")
    print(
        json.dumps(
            per_condition,
            ensure_ascii=False,
            indent=2,
        )
    )

    print()
    print("Result JSON:", RESULT_PATH.resolve())
    print("Detail CSV:", DETAIL_CSV_PATH.resolve())


if __name__ == "__main__":
    main()