import json
from pathlib import Path


ROOT = Path("experiments/week5/results/live")

L0_PATH = ROOT / "L0_baseline_live.json"
L1_PATH = ROOT / "L1_topk5_live.json"
L2_PATH = ROOT / "L2_history_first_live.json"

OUTPUT_PATH = ROOT / "live_retrieval_overlap.json"


def load_json(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def jaccard(ids_a, ids_b):
    a = set(ids_a)
    b = set(ids_b)

    if not a and not b:
        return 1.0

    return len(a & b) / len(a | b)


def trial_map(data):
    return {
        (item["group"], item["trial"]): item
        for item in data["trials"]
    }


l0 = load_json(L0_PATH)
l1 = load_json(L1_PATH)
l2 = load_json(L2_PATH)

baseline = trial_map(l0)


def compare(after_data, scenario_id):
    after = trial_map(after_data)
    records = []

    for group in ("clean", "poisoned"):
        for trial in range(1, 6):
            before_item = baseline[(group, trial)]
            after_item = after[(group, trial)]

            overlap = jaccard(
                before_item["used_memory_ids"],
                after_item["used_memory_ids"]
            )

            records.append({
                "scenario_id": scenario_id,
                "group": group,
                "trial": trial,
                "before_ids": before_item["used_memory_ids"],
                "after_ids": after_item["used_memory_ids"],
                "jaccard_overlap": round(overlap, 4)
            })

    return records


records = (
    compare(l1, "D1")
    + compare(l2, "D2")
)

averages = {}

for scenario_id in ("D1", "D2"):
    for group in ("clean", "poisoned"):
        values = [
            item["jaccard_overlap"]
            for item in records
            if item["scenario_id"] == scenario_id
            and item["group"] == group
        ]

        averages[f"{scenario_id}_{group}"] = round(
            sum(values) / len(values),
            4
        )


result = {
    "metric": "Jaccard retrieval-set overlap",
    "source": "week5_live_observation",
    "pairing_method": "Same group and same trial number",
    "averages": averages,
    "records": records
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(
        result,
        f,
        indent=2,
        ensure_ascii=False
    )

print("=== Week5 Live Retrieval Overlap ===")
for key, value in averages.items():
    print(f"{key}: {value}")

print(f"Saved: {OUTPUT_PATH}")
