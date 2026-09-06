import json
from pathlib import Path


ROOT = Path("experiments/week5/results")

D1_PATH = ROOT / "D1_dpmf_event.json"
D2_PATH = ROOT / "D2_dpmf_event.json"
OUTPUT_PATH = ROOT / "dpmf_summary.json"


def load_json(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def summarize(event):
    metadata = event.get("metadata", {})
    evidence = event.get("evidence", {})
    recommendation = metadata.get(
        "defense_recommendation",
        {}
    )

    return {
        "event_id": event["event_id"],
        "drift_type": event["drift_type"],
        "component": event["component"],
        "before": event["before"],
        "after": event["after"],
        "change_score": event["change_score"],
        "clean_correct_rate_before": evidence.get(
            "clean_correct_rate_before"
        ),
        "clean_correct_rate_after": evidence.get(
            "clean_correct_rate_after"
        ),
        "clean_utility_drop": evidence.get(
            "clean_utility_drop"
        ),
        "retrieval_overlap": evidence.get(
            "retrieval_overlap"
        ),
        "poisoned_retrieval_overlap": evidence.get(
            "poisoned_retrieval_overlap"
        ),
        "attack_success_rate": evidence.get(
            "attack_success_rate"
        ),
        "risk_score": event["risk_score"],
        "risk_level": event["risk_level"],
        "risk_components": metadata.get(
            "components",
            {}
        ),
        "primary_defense": recommendation.get(
            "primary_recommendation"
        ),
        "recommended_defenses": event.get(
            "recommended_defenses",
            []
        ),
        "defense_ranking": recommendation.get(
            "ranking",
            []
        )
    }


d1 = load_json(D1_PATH)
d2 = load_json(D2_PATH)

d1_summary = summarize(d1)
d2_summary = summarize(d2)

higher = (
    "D1"
    if d1["risk_score"] > d2["risk_score"]
    else "D2"
)

summary = {
    "experiment": "week5_dpmf_drift_risk_defense_summary",
    "risk_model": "prototype_heuristic_v0",
    "defense_selection_method": "empirical_lexicographic_v0",
    "pipeline": [
        "architecture_snapshot",
        "drift_detection",
        "risk_assessment",
        "knowledge_base_mapping",
        "defense_recommendation"
    ],
    "scenarios": {
        "D1": d1_summary,
        "D2": d2_summary
    },
    "comparison": {
        "higher_risk_scenario": higher,
        "D1_risk_score": d1["risk_score"],
        "D2_risk_score": d2["risk_score"],
        "risk_score_gap": round(
            abs(d2["risk_score"] - d1["risk_score"]),
            4
        ),
        "D1_primary_defense": d1_summary["primary_defense"],
        "D2_primary_defense": d2_summary["primary_defense"]
    }
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(
        summary,
        f,
        indent=2,
        ensure_ascii=False
    )

print("=== DPMF Final Summary ===")

print(
    f"D1 | {d1['drift_type']} | "
    f"{d1['before']} -> {d1['after']} | "
    f"risk={d1['risk_score']:.4f} "
    f"{d1['risk_level']} | "
    f"defense={d1_summary['primary_defense']}"
)

print(
    f"D2 | {d2['drift_type']} | "
    f"{d2['before']} -> {d2['after']} | "
    f"risk={d2['risk_score']:.4f} "
    f"{d2['risk_level']} | "
    f"defense={d2_summary['primary_defense']}"
)

print(
    f"Higher risk scenario: {higher}"
)

print(
    "Risk score gap:",
    summary["comparison"]["risk_score_gap"]
)

print(f"Saved: {OUTPUT_PATH}")
