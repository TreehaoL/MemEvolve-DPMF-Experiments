import json
from pathlib import Path


RESULTS = Path("experiments/week5/results")
LIVE = RESULTS / "live"

OFFLINE_D1 = RESULTS / "D1_dpmf_event.json"
OFFLINE_D2 = RESULTS / "D2_dpmf_event.json"

LIVE_D1 = LIVE / "live_D1_dpmf_event.json"
LIVE_D2 = LIVE / "live_D2_dpmf_event.json"

OUTPUT = LIVE / "offline_vs_live_summary.json"


def load_json(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def primary_defense(event):
    return (
        event.get("metadata", {})
        .get("defense_recommendation", {})
        .get("primary_recommendation")
    )


def extract(event):
    evidence = event.get("evidence", {})

    return {
        "risk_score": event["risk_score"],
        "risk_level": event["risk_level"],
        "clean_correct_rate_before":
            evidence.get("clean_correct_rate_before"),
        "clean_correct_rate_after":
            evidence.get("clean_correct_rate_after"),
        "clean_utility_drop":
            evidence.get("clean_utility_drop"),
        "retrieval_overlap":
            evidence.get("retrieval_overlap"),
        "poisoned_retrieval_overlap":
            evidence.get("poisoned_retrieval_overlap"),
        "attack_success_rate":
            evidence.get("attack_success_rate"),
        "primary_defense":
            primary_defense(event)
    }


offline_d1 = load_json(OFFLINE_D1)
offline_d2 = load_json(OFFLINE_D2)
live_d1 = load_json(LIVE_D1)
live_d2 = load_json(LIVE_D2)

offline_d1_data = extract(offline_d1)
offline_d2_data = extract(offline_d2)
live_d1_data = extract(live_d1)
live_d2_data = extract(live_d2)

offline_order = (
    "D2>D1"
    if offline_d2["risk_score"] > offline_d1["risk_score"]
    else "D1>D2"
)

live_order = (
    "D2>D1"
    if live_d2["risk_score"] > live_d1["risk_score"]
    else "D1>D2"
)

summary = {
    "experiment": "week5_offline_replay_vs_live_observation",
    "offline_replay": {
        "D1": offline_d1_data,
        "D2": offline_d2_data
    },
    "live_observation": {
        "D1": live_d1_data,
        "D2": live_d2_data
    },
    "comparison": {
        "D1_risk_delta": round(
            live_d1["risk_score"] - offline_d1["risk_score"],
            4
        ),
        "D2_risk_delta": round(
            live_d2["risk_score"] - offline_d2["risk_score"],
            4
        ),
        "offline_risk_order": offline_order,
        "live_risk_order": live_order,
        "risk_order_stable": offline_order == live_order,
        "D1_defense_stable":
            primary_defense(offline_d1)
            == primary_defense(live_d1),
        "D2_defense_stable":
            primary_defense(offline_d2)
            == primary_defense(live_d2)
    }
}

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

print("=== Offline Replay vs Live Observation ===")

print(
    f"D1 risk: "
    f"{offline_d1['risk_score']:.4f} -> "
    f"{live_d1['risk_score']:.4f} "
    f"(delta={summary['comparison']['D1_risk_delta']:+.4f})"
)

print(
    f"D2 risk: "
    f"{offline_d2['risk_score']:.4f} -> "
    f"{live_d2['risk_score']:.4f} "
    f"(delta={summary['comparison']['D2_risk_delta']:+.4f})"
)

print(
    "Risk order:",
    offline_order,
    "->",
    live_order
)

print(
    "Risk order stable:",
    summary["comparison"]["risk_order_stable"]
)

print(
    "D1 defense:",
    primary_defense(offline_d1),
    "->",
    primary_defense(live_d1)
)

print(
    "D2 defense:",
    primary_defense(offline_d2),
    "->",
    primary_defense(live_d2)
)

print(
    "Defense recommendation stable:",
    summary["comparison"]["D1_defense_stable"]
    and summary["comparison"]["D2_defense_stable"]
)

print(f"Saved: {OUTPUT}")
