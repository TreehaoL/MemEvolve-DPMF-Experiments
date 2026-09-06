import csv
import json
from pathlib import Path

ROOT = Path("experiments")

week3_d1 = ROOT / "week3/results/topk5_drift.json"
week3_d2 = ROOT / "week3/results/D2_prompt_drift.json"

week4_f1_d1 = ROOT / "week4/results/F1_D1_topk5.json"
week4_f1_d2 = ROOT / "week4/results/F1_D2_history_first.json"
week4_f2_d1 = ROOT / "week4/results/F2_D1_topk5.json"
week4_f2_d2 = ROOT / "week4/results/F2_D2_history_first.json"

output_csv = (
    ROOT
    / "week4/knowledge_base/architecture_defense_mapping_v0.csv"
)

output_json = (
    ROOT
    / "week4/results/defense_matrix_summary.json"
)


def load_metrics(path):
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return data["metrics"]


m_d1 = load_metrics(week3_d1)
m_d2 = load_metrics(week3_d2)

m_f1_d1 = load_metrics(week4_f1_d1)
m_f1_d2 = load_metrics(week4_f1_d2)

m_f2_d1 = load_metrics(week4_f2_d1)
m_f2_d2 = load_metrics(week4_f2_d2)


rows = [
    {
        "drift_id": "D1",
        "drift_type": "retrieval_topk",
        "drift_description": "Top-K 3 -> 5",
        "defense_id": "F0",
        "defense_name": "no_defense",
        "defense_position": "none",
        "clean_correct_rate": m_d1[
            "clean_correct_rate"
        ],
        "attack_success_rate": m_d1[
            "attack_success_rate"
        ],
        "defense_block_rate": 0.0,
        "poison_exposure_rate": m_d1[
            "poison_hit_at_k_rate"
        ],
        "false_positive_rate": "",
        "security_status": "failed",
        "utility_status": "degraded",
        "mapping_note": (
            "D1 exposes poisoned memories under enlarged Top-K; "
            "attack remains fully successful."
        ),
    },
    {
        "drift_id": "D1",
        "drift_type": "retrieval_topk",
        "drift_description": "Top-K 3 -> 5",
        "defense_id": "F1",
        "defense_name": "static_history_statistics_filter",
        "defense_position": "pre_retrieval",
        "clean_correct_rate": m_f1_d1[
            "clean_correct_rate"
        ],
        "attack_success_rate": m_f1_d1[
            "attack_success_rate"
        ],
        "defense_block_rate": m_f1_d1[
            "defense_block_rate"
        ],
        "poison_exposure_rate": m_f1_d1[
            "poison_hit_after_defense_rate"
        ],
        "false_positive_rate": 0.0,
        "security_status": "effective",
        "utility_status": "degraded",
        "mapping_note": (
            "F1 blocks the injected high-history memories, "
            "but clean utility remains lower under D1."
        ),
    },
    {
        "drift_id": "D1",
        "drift_type": "retrieval_topk",
        "drift_description": "Top-K 3 -> 5",
        "defense_id": "F2",
        "defense_name": "retrieval_time_static_trust_gate",
        "defense_position": "post_retrieval_pre_synthesis",
        "clean_correct_rate": m_f2_d1[
            "clean_correct_rate"
        ],
        "attack_success_rate": m_f2_d1[
            "attack_success_rate"
        ],
        "defense_block_rate": m_f2_d1[
            "defense_block_rate"
        ],
        "poison_exposure_rate": m_f2_d1[
            "poison_selected_before_gate_rate"
        ],
        "false_positive_rate": m_f2_d1[
            "clean_blocked_trial_rate"
        ],
        "security_status": "effective",
        "utility_status": "stable",
        "mapping_note": (
            "Poison is retrieved but consistently blocked "
            "before synthesis; clean utility is preserved."
        ),
    },
    {
        "drift_id": "D2",
        "drift_type": "retrieval_policy",
        "drift_description": (
            "semantic relevance first -> historical success first"
        ),
        "defense_id": "F0",
        "defense_name": "no_defense",
        "defense_position": "none",
        "clean_correct_rate": m_d2[
            "clean_correct_rate"
        ],
        "attack_success_rate": m_d2[
            "attack_success_rate"
        ],
        "defense_block_rate": 0.0,
        "poison_exposure_rate": m_d2[
            "poison_hit_at_3_rate"
        ],
        "false_positive_rate": "",
        "security_status": "failed",
        "utility_status": "collapsed",
        "mapping_note": (
            "History-first policy causes clean utility collapse "
            "while poisoned memories dominate retrieval."
        ),
    },
    {
        "drift_id": "D2",
        "drift_type": "retrieval_policy",
        "drift_description": (
            "semantic relevance first -> historical success first"
        ),
        "defense_id": "F1",
        "defense_name": "static_history_statistics_filter",
        "defense_position": "pre_retrieval",
        "clean_correct_rate": m_f1_d2[
            "clean_correct_rate"
        ],
        "attack_success_rate": m_f1_d2[
            "attack_success_rate"
        ],
        "defense_block_rate": m_f1_d2[
            "defense_block_rate"
        ],
        "poison_exposure_rate": m_f1_d2[
            "poison_hit_after_defense_rate"
        ],
        "false_positive_rate": 0.0,
        "security_status": "effective",
        "utility_status": "collapsed",
        "mapping_note": (
            "F1 preserves security, but does not recover utility "
            "under history-first drift."
        ),
    },
    {
        "drift_id": "D2",
        "drift_type": "retrieval_policy",
        "drift_description": (
            "semantic relevance first -> historical success first"
        ),
        "defense_id": "F2",
        "defense_name": "retrieval_time_static_trust_gate",
        "defense_position": "post_retrieval_pre_synthesis",
        "clean_correct_rate": m_f2_d2[
            "clean_correct_rate"
        ],
        "attack_success_rate": m_f2_d2[
            "attack_success_rate"
        ],
        "defense_block_rate": m_f2_d2[
            "defense_block_rate"
        ],
        "poison_exposure_rate": m_f2_d2[
            "poison_selected_before_gate_rate"
        ],
        "false_positive_rate": m_f2_d2[
            "clean_blocked_trial_rate"
        ],
        "security_status": "effective",
        "utility_status": "mostly_stable",
        "mapping_note": (
            "History-first still selects poisoned memories, "
            "but F2 blocks them after retrieval and retains "
            "most clean-task utility."
        ),
    },
]


output_csv.parent.mkdir(
    parents=True,
    exist_ok=True,
)

fieldnames = list(rows[0].keys())

with output_csv.open(
    "w",
    encoding="utf-8-sig",
    newline="",
) as f:
    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames,
    )

    writer.writeheader()
    writer.writerows(rows)


summary = {
    "experiment": "week4_defense_matrix",
    "matrix": rows,
    "main_findings": [
        (
            "Without defense, both D1 and D2 retain "
            "100% attack success."
        ),
        (
            "F1 maintains attack blocking under both drifts, "
            "but utility collapses under D2."
        ),
        (
            "F2 maintains attack blocking under both drifts "
            "and preserves substantially better clean utility."
        ),
        (
            "Defense robustness should therefore be evaluated "
            "on both security and utility dimensions."
        ),
    ],
}

output_json.write_text(
    json.dumps(
        summary,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

print("=== WEEK 4 DEFENSE MATRIX ===")

for row in rows:
    print(
        row["drift_id"],
        row["defense_id"],
        "clean=",
        row["clean_correct_rate"],
        "attack=",
        row["attack_success_rate"],
        "block=",
        row["defense_block_rate"],
    )

print()
print("CSV:", output_csv.resolve())
print("JSON:", output_json.resolve())
