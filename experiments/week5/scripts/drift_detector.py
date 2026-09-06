import json
import sys
from pathlib import Path


def load_json(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def save_json(data, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def detect_d1(before, after):
    parameter_before = before.get("parameter")
    parameter_after = after.get("parameter")

    if parameter_before != parameter_after:
        raise ValueError(
            f"Parameter mismatch: {parameter_before} != {parameter_after}"
        )

    parameter = parameter_before
    before_value = before.get("value")
    after_value = after.get("value")

    detected = before_value != after_value

    if parameter == "top_k_longterm":
        drift_type = "retrieval_topk"
        component = "retriever"

        if detected and isinstance(before_value, (int, float)) and before_value != 0:
            change_score = abs(after_value - before_value) / abs(before_value)
            change_score = min(change_score, 1.0)
        elif detected:
            change_score = 1.0
        else:
            change_score = 0.0
    else:
        drift_type = "unknown"
        component = "unknown"
        change_score = 1.0 if detected else 0.0

    if not detected:
        direction = "unchanged"
    elif isinstance(before_value, (int, float)) and isinstance(after_value, (int, float)):
        direction = "increase" if after_value > before_value else "decrease"
    else:
        direction = "changed"

    return {
        "drift_detected": detected,
        "drift_type": drift_type,
        "component": component,
        "parameter": parameter,
        "before": before_value,
        "after": after_value,
        "direction": direction,
        "change_score": round(change_score, 4)
    }


def detect_d2(before, after):
    before_policy = before.get("retrieval_policy")
    after_policy = after.get("retrieval_policy")

    detected = before_policy != after_policy

    structural_changes = {}

    if before.get("semantic_relevance_role") != after.get("semantic_relevance_role"):
        structural_changes["semantic_relevance_role"] = {
            "before": before.get("semantic_relevance_role"),
            "after": after.get("semantic_relevance_role")
        }

    # Categorical policy replacement:
    # 1.0 means a complete policy-category switch was observed.
    # It is a drift magnitude indicator, not the final security risk.
    change_score = 1.0 if detected else 0.0

    return {
        "drift_detected": detected,
        "drift_type": "retrieval_policy",
        "component": "retriever",
        "parameter": "retrieval_policy",
        "before": before_policy,
        "after": after_policy,
        "direction": "changed" if detected else "unchanged",
        "change_score": change_score,
        "structural_changes": structural_changes
    }


def detect_drift(before, after):
    scenario_before = before.get("scenario_id")
    scenario_after = after.get("scenario_id")

    if scenario_before != scenario_after:
        raise ValueError(
            f"Scenario mismatch: {scenario_before} != {scenario_after}"
        )

    if scenario_before == "D1":
        return detect_d1(before, after)

    if scenario_before == "D2":
        return detect_d2(before, after)

    raise ValueError(f"Unsupported scenario: {scenario_before}")


def main():
    if len(sys.argv) not in (3, 4):
        print(
            "Usage: python drift_detector.py "
            "<before.json> <after.json> [output.json]"
        )
        sys.exit(1)

    before_path = Path(sys.argv[1])
    after_path = Path(sys.argv[2])

    before = load_json(before_path)
    after = load_json(after_path)

    result = detect_drift(before, after)

    print("=== DPMF Drift Detection ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if len(sys.argv) == 4:
        output_path = Path(sys.argv[3])
        save_json(result, output_path)
        print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
