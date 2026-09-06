import csv
import json
import sys
from pathlib import Path


def load_json(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def to_float(value, default=1.0):
    if value is None or str(value).strip() == "":
        return default

    try:
        return float(value)
    except ValueError:
        return default


def load_mapping(csv_path):
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def candidate_sort_key(row):
    security_effective = (
        0 if row.get("security_status") == "effective" else 1
    )

    attack_success = to_float(
        row.get("attack_success_rate"),
        default=1.0
    )

    clean_correct = to_float(
        row.get("clean_correct_rate"),
        default=0.0
    )

    false_positive = to_float(
        row.get("false_positive_rate"),
        default=1.0
    )

    defense_block = to_float(
        row.get("defense_block_rate"),
        default=0.0
    )

    poison_exposure = to_float(
        row.get("poison_exposure_rate"),
        default=1.0
    )

    return (
        security_effective,
        attack_success,
        -clean_correct,
        false_positive,
        -defense_block,
        poison_exposure
    )


def recommend(event, mapping_rows):
    drift_type = event.get("drift_type")

    candidates = [
        row
        for row in mapping_rows
        if row.get("drift_type") == drift_type
        and row.get("defense_id") != "F0"
    ]

    if not candidates:
        raise ValueError(
            f"No defense mapping found for drift_type={drift_type}"
        )

    candidates.sort(key=candidate_sort_key)

    ranking = []

    for rank, row in enumerate(candidates, start=1):
        ranking.append({
            "rank": rank,
            "defense_id": row.get("defense_id"),
            "defense_name": row.get("defense_name"),
            "defense_position": row.get("defense_position"),
            "clean_correct_rate": to_float(
                row.get("clean_correct_rate"),
                default=0.0
            ),
            "attack_success_rate": to_float(
                row.get("attack_success_rate"),
                default=1.0
            ),
            "defense_block_rate": to_float(
                row.get("defense_block_rate"),
                default=0.0
            ),
            "poison_exposure_rate": to_float(
                row.get("poison_exposure_rate"),
                default=1.0
            ),
            "false_positive_rate": to_float(
                row.get("false_positive_rate"),
                default=1.0
            ),
            "security_status": row.get("security_status"),
            "utility_status": row.get("utility_status"),
            "mapping_note": row.get("mapping_note")
        })

    event["recommended_defenses"] = [
        f"{item['defense_id']}:{item['defense_name']}"
        for item in ranking
    ]

    metadata = event.setdefault("metadata", {})

    metadata["defense_recommendation"] = {
        "selection_method": "empirical_lexicographic_v0",
        "primary_recommendation": ranking[0]["defense_id"],
        "ranking": ranking
    }

    return event


def main():
    if len(sys.argv) != 4:
        print(
            "Usage: python defense_mapper.py "
            "<event.json> <mapping.csv> <output.json>"
        )
        sys.exit(1)

    event_path = Path(sys.argv[1])
    mapping_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3])

    event = load_json(event_path)
    mapping_rows = load_mapping(mapping_path)

    updated_event = recommend(
        event,
        mapping_rows
    )

    save_json(updated_event, output_path)

    recommendation = (
        updated_event["metadata"]["defense_recommendation"]
    )

    print("=== DPMF Defense Recommendation ===")
    print(f"Drift type: {updated_event['drift_type']}")
    print(
        "Primary recommendation:",
        recommendation["primary_recommendation"]
    )

    print("\nRanking:")
    for item in recommendation["ranking"]:
        print(
            f"  {item['rank']}. "
            f"{item['defense_id']} "
            f"{item['defense_name']} | "
            f"clean={item['clean_correct_rate']} | "
            f"attack={item['attack_success_rate']} | "
            f"utility={item['utility_status']}"
        )

    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    main()
