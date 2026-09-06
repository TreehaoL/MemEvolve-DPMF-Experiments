import json
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path("experiments/week6")

METRICS_PATH = ROOT / "results/dpmf_detection_metrics.json"
PIPELINE_PATH = ROOT / "results/dpmf_end_to_end.json"
LLM_PATH = ROOT / "results/llm_judge_reports.json"

SUMMARY_PATH = ROOT / "results/week6_summary.json"
FIGURE_DIR = ROOT / "results/figures"


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path}"
        )

    return json.loads(
        path.read_text(encoding="utf-8")
    )


def main():
    metrics_data = load_json(METRICS_PATH)
    pipeline_data = load_json(PIPELINE_PATH)
    llm_data = load_json(LLM_PATH)

    FIGURE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    metrics = metrics_data["metrics"]
    per_condition = metrics_data["per_condition"]
    events = pipeline_data["events"]

    # --------------------------------------------------------
    # 1. Freeze key detection metrics
    # --------------------------------------------------------
    structural = metrics["structural_detection"]
    behavioral = metrics["behavioral_detection"]
    fused = metrics["fused_dpmf_detection"]
    type_metrics = metrics["drift_type_classification"]

    event_map = {
        event["condition"]: event
        for event in events
    }

    condition_order = [
        "S0_repeat",
        "D1_topk5",
        "D2_topk7",
        "D3_history_first",
        "D4_combined",
    ]

    condition_labels = {
        "S0_repeat": "S0 Stable",
        "D1_topk5": "D1 Top-K=5",
        "D2_topk7": "D2 Top-K=7",
        "D3_history_first": "D3 History-first",
        "D4_combined": "D4 Combined",
    }

    condition_summary = {}

    for condition in condition_order:
        event = event_map[condition]
        behavior = per_condition[condition]

        condition_summary[condition] = {
            "drift_detected": event[
                "drift_detection"
            ]["drift_detected"],
            "drift_type": event[
                "drift_detection"
            ]["drift_type"],
            "top_k": event[
                "architecture_state"
            ]["top_k"],
            "retrieval_policy": event[
                "architecture_state"
            ]["retrieval_policy"],
            "avg_retrieval_instability": behavior[
                "avg_retrieval_instability"
            ],
            "risk_score": event[
                "risk_assessment"
            ]["risk_score"],
            "risk_level": event[
                "risk_assessment"
            ]["risk_level"],
            "primary_defense": event[
                "defense_recommendation"
            ]["primary"],
            "secondary_defense": event[
                "defense_recommendation"
            ].get("secondary"),
        }

    summary = {
        "experiment": "week6_summary",
        "created_at": (
            datetime.now()
            .astimezone()
            .isoformat()
        ),
        "model": pipeline_data["model"],
        "reference_condition": (
            pipeline_data["reference_condition"]
        ),
        "dataset": {
            "reference_samples": (
                metrics_data["reference_samples"]
            ),
            "test_samples": (
                metrics_data["test_samples"]
            ),
            "stable_negative_samples": (
                metrics_data[
                    "test_composition"
                ]["stable_negative_samples"]
            ),
            "drift_positive_samples": (
                metrics_data[
                    "test_composition"
                ]["drift_positive_samples"]
            ),
            "behavior_threshold": (
                metrics_data[
                    "behavior_drift_threshold"
                ]
            ),
        },
        "detection_metrics": {
            "structural": structural,
            "behavioral": behavioral,
            "fused": fused,
            "drift_type_classification": (
                type_metrics
            ),
        },
        "conditions": condition_summary,
        "llm_explanation": {
            "model": llm_data["model"],
            "role": llm_data["role"],
            "event_count": (
                llm_data["event_count"]
            ),
        },
        "key_findings": [
            (
                "Structural drift detection achieved "
                "100% accuracy, precision, recall, and F1 "
                "on the 50-sample Week 6 test set."
            ),
            (
                "Drift-type classification achieved "
                "100% accuracy for explicit Top-K, "
                "retrieval-policy, and combined drift."
            ),
            (
                "Behavioral detection achieved 88% accuracy, "
                "97.5% recall, and 92.86% F1, but produced "
                "a 50% false-positive rate on stable controls."
            ),
            (
                "Stable architecture can exhibit retrieval "
                "behavior fluctuations without structural drift."
            ),
            (
                "Structural drift can occur while the retrieved "
                "memory set remains temporarily unchanged, "
                "forming a silent-drift case."
            ),
            (
                "DPMF therefore uses structural state as the "
                "primary drift criterion and behavioral change "
                "as auxiliary risk evidence."
            ),
        ],
    }

    SUMMARY_PATH.write_text(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # Figure 1: Risk score by condition
    # --------------------------------------------------------
    labels = [
        condition_labels[x]
        for x in condition_order
    ]

    risk_scores = [
        condition_summary[x]["risk_score"]
        for x in condition_order
    ]

    plt.figure(figsize=(9, 5))
    plt.bar(labels, risk_scores)

    plt.axhline(
        0.30,
        linestyle="--",
        linewidth=1,
        label="MEDIUM threshold",
    )

    plt.axhline(
        0.60,
        linestyle="--",
        linewidth=1,
        label="HIGH threshold",
    )

    plt.ylabel("Risk Score")
    plt.xlabel("Architecture Condition")
    plt.title("DPMF Risk Score under Architecture Drift")
    plt.ylim(0, 0.75)
    plt.xticks(rotation=18)

    for index, value in enumerate(risk_scores):
        plt.text(
            index,
            value + 0.015,
            f"{value:.4f}",
            ha="center",
        )

    plt.legend()
    plt.tight_layout()

    risk_path = (
        FIGURE_DIR / "week6_risk_scores.png"
    )

    plt.savefig(
        risk_path,
        dpi=220,
        bbox_inches="tight",
    )

    plt.close()

    # --------------------------------------------------------
    # Figure 2: Retrieval instability
    # --------------------------------------------------------
    instability = [
        condition_summary[x][
            "avg_retrieval_instability"
        ]
        for x in condition_order
    ]

    plt.figure(figsize=(9, 5))
    plt.bar(labels, instability)

    plt.axhline(
        metrics_data[
            "behavior_drift_threshold"
        ],
        linestyle="--",
        linewidth=1,
        label="Behavior threshold = 0.40",
    )

    plt.ylabel("Average Retrieval Instability")
    plt.xlabel("Architecture Condition")
    plt.title(
        "Retrieval Behavioral Instability "
        "under Architecture Drift"
    )
    plt.ylim(0, 0.7)
    plt.xticks(rotation=18)

    for index, value in enumerate(instability):
        plt.text(
            index,
            value + 0.015,
            f"{value:.4f}",
            ha="center",
        )

    plt.legend()
    plt.tight_layout()

    instability_path = (
        FIGURE_DIR
        / "week6_retrieval_instability.png"
    )

    plt.savefig(
        instability_path,
        dpi=220,
        bbox_inches="tight",
    )

    plt.close()

    # --------------------------------------------------------
    # Figure 3: Structural vs behavioral metrics
    # --------------------------------------------------------
    metric_names = [
        "Accuracy",
        "Precision",
        "Recall",
        "F1",
    ]

    structural_values = [
        structural["accuracy"],
        structural["precision"],
        structural["recall"],
        structural["f1"],
    ]

    behavioral_values = [
        behavioral["accuracy"],
        behavioral["precision"],
        behavioral["recall"],
        behavioral["f1"],
    ]

    x = list(range(len(metric_names)))
    width = 0.36

    plt.figure(figsize=(8, 5))

    plt.bar(
        [i - width / 2 for i in x],
        structural_values,
        width=width,
        label="Structural",
    )

    plt.bar(
        [i + width / 2 for i in x],
        behavioral_values,
        width=width,
        label="Behavioral",
    )

    plt.xticks(x, metric_names)
    plt.ylim(0, 1.08)
    plt.ylabel("Score")
    plt.xlabel("Metric")
    plt.title(
        "DPMF Structural vs Behavioral Detection"
    )
    plt.legend()

    for i, value in enumerate(
        structural_values
    ):
        plt.text(
            i - width / 2,
            value + 0.015,
            f"{value:.2f}",
            ha="center",
        )

    for i, value in enumerate(
        behavioral_values
    ):
        plt.text(
            i + width / 2,
            value + 0.015,
            f"{value:.2f}",
            ha="center",
        )

    plt.tight_layout()

    metrics_path = (
        FIGURE_DIR
        / "week6_detection_metrics.png"
    )

    plt.savefig(
        metrics_path,
        dpi=220,
        bbox_inches="tight",
    )

    plt.close()

    print("=" * 80)
    print("WEEK 6 SUMMARY ASSETS")
    print("=" * 80)

    print("Summary JSON:")
    print(SUMMARY_PATH.resolve())

    print()
    print("Figures:")
    print(risk_path.resolve())
    print(instability_path.resolve())
    print(metrics_path.resolve())

    print()
    print("Key metrics:")
    print(
        "Structural Accuracy:",
        structural["accuracy"],
    )
    print(
        "Behavioral Accuracy:",
        behavioral["accuracy"],
    )
    print(
        "Behavioral F1:",
        behavioral["f1"],
    )
    print(
        "Behavioral FPR:",
        behavioral[
            "false_positive_rate"
        ],
    )


if __name__ == "__main__":
    main()