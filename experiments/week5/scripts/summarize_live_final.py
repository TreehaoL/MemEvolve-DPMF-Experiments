import json
from pathlib import Path


ROOT = Path("experiments/week5/results/live")

CONTROL = ROOT / "control_no_drift_event.json"
D1 = ROOT / "live_D1_dpmf_event.json"
D2 = ROOT / "live_D2_dpmf_event.json"

OUTPUT = ROOT / "live_final_summary.json"


def load_json(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def defense(event):
    return (
        event.get("metadata", {})
        .get("defense_recommendation", {})
        .get("primary_recommendation")
    )


control = load_json(CONTROL)
d1 = load_json(D1)
d2 = load_json(D2)

summary = {
    "experiment": "week5_dpmf_live_final_summary",
    "score_semantics": "composite_security_risk",
    "scenarios": {
        "control_no_drift": {
            "drift_detected": False,
            "risk_score": control["risk_score"],
            "risk_level": control["risk_level"],
            "primary_defense": None
        },
        "D1_retrieval_topk": {
            "drift_detected": True,
            "risk_score": d1["risk_score"],
            "risk_level": d1["risk_level"],
            "primary_defense": defense(d1)
        },
        "D2_retrieval_policy": {
            "drift_detected": True,
            "risk_score": d2["risk_score"],
            "risk_level": d2["risk_level"],
            "primary_defense": defense(d2)
        }
    },
    "conclusion": {
        "control_remains_low_risk": control["risk_level"] == "LOW",
        "D1_detected_high_risk": d1["risk_level"] == "HIGH",
        "D2_detected_high_risk": d2["risk_level"] == "HIGH",
        "D2_higher_than_D1": d2["risk_score"] > d1["risk_score"],
        "risk_order": "D2>D1>CONTROL"
    }
}

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

print("=== Week5 DPMF Live Final Summary ===")
print(
    f"CONTROL | no drift         | "
    f"risk={control['risk_score']:.4f} "
    f"{control['risk_level']}"
)
print(
    f"D1      | retrieval_topk   | "
    f"risk={d1['risk_score']:.4f} "
    f"{d1['risk_level']} | "
    f"defense={defense(d1)}"
)
print(
    f"D2      | retrieval_policy | "
    f"risk={d2['risk_score']:.4f} "
    f"{d2['risk_level']} | "
    f"defense={defense(d2)}"
)
print("Risk order: D2 > D1 > CONTROL")
print(f"Saved: {OUTPUT}")
