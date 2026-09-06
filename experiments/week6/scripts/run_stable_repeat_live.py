import json
import sys
from datetime import datetime
from pathlib import Path


WEEK6_SCRIPTS = Path("experiments/week6/scripts").resolve()

if str(WEEK6_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(WEEK6_SCRIPTS))


from generate_live_drift_cases import (
    CLEAN_MEMORY_PATH,
    POISONED_MEMORY_PATH,
    QUERIES,
    CONDITIONS,
    MODEL_NAME,
    run_trial,
)


RESULT_PATH = Path(
    "experiments/week6/results/live/S0_repeat_live.json"
)


def main():
    print("=" * 80)
    print("WEEK 6 INDEPENDENT STABLE CONTROL")
    print("=" * 80)
    print("Model:", MODEL_NAME)

    condition_name = "S0_repeat"
    condition = dict(CONDITIONS["S0_stable"])

    all_trials = []

    for query_item in QUERIES:
        all_trials.append(
            run_trial(
                condition_name=condition_name,
                condition=condition,
                group_name="clean",
                memory_path=CLEAN_MEMORY_PATH,
                query_item=query_item,
            )
        )

        all_trials.append(
            run_trial(
                condition_name=condition_name,
                condition=condition,
                group_name="poisoned",
                memory_path=POISONED_MEMORY_PATH,
                query_item=query_item,
            )
        )

    # Explicitly preserve the ground-truth label:
    # this is an independent execution of the SAME architecture.
    for item in all_trials:
        item["expected_drift"] = False
        item["ground_truth_drift_type"] = "none"
        item["reference_condition"] = "S0_stable"

    clean_trials = [
        item
        for item in all_trials
        if item["group"] == "clean"
    ]

    poisoned_trials = [
        item
        for item in all_trials
        if item["group"] == "poisoned"
    ]

    summary = {
        "experiment": "week6_S0_repeat_live",
        "created_at": (
            datetime.now()
            .astimezone()
            .isoformat()
        ),
        "model": MODEL_NAME,
        "condition": condition_name,
        "reference_condition": "S0_stable",
        "expected_drift": False,
        "total_trials": len(all_trials),
        "metrics": {
            "clean_final_answer_correct_rate": (
                sum(
                    item["clean_answer_correct"]
                    for item in clean_trials
                )
                / len(clean_trials)
            ),
            "poison_hit_at_k_rate": (
                sum(
                    item["poison_hit_at_k"]
                    for item in poisoned_trials
                )
                / len(poisoned_trials)
            ),
            "final_attack_success_rate": (
                sum(
                    item["attack_success"]
                    for item in poisoned_trials
                )
                / len(poisoned_trials)
            ),
        },
        "trials": all_trials,
    }

    RESULT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    RESULT_PATH.write_text(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 80)
    print("STABLE CONTROL SUMMARY")
    print("=" * 80)

    print(
        json.dumps(
            summary["metrics"],
            ensure_ascii=False,
            indent=2,
        )
    )

    print()
    print("Result file:", RESULT_PATH.resolve())


if __name__ == "__main__":
    main()