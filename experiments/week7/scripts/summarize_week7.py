import csv
import json
from datetime import datetime
from pathlib import Path


RESULT_DIR = Path(
    "experiments/week7/results"
)

CLOSED_LOOP_DIR = (
    RESULT_DIR / "closed_loop"
)

OUTPUT_JSON = (
    RESULT_DIR / "week7_summary.json"
)

OUTPUT_CSV = (
    RESULT_DIR
    / "week7_closed_loop_summary.csv"
)


RESULT_FILES = {
    "S0": (
        CLOSED_LOOP_DIR
        / "S0_closed_loop_q5.json"
    ),
    "D1": (
        CLOSED_LOOP_DIR
        / "D1_closed_loop_q5.json"
    ),
    "D3": (
        CLOSED_LOOP_DIR
        / "D3_closed_loop_q5.json"
    ),
    "D4": (
        CLOSED_LOOP_DIR
        / "D4_closed_loop_live_q5.json"
    ),
}


EVENT_FILES = {
    "S0": Path(
        "experiments/week6/results/events/"
        "S0_repeat_dpmf_event.json"
    ),
    "D1": Path(
        "experiments/week6/results/events/"
        "D1_topk5_dpmf_event.json"
    ),
    "D3": Path(
        "experiments/week6/results/events/"
        "D3_history_first_dpmf_event.json"
    ),
    "D4": Path(
        "experiments/week6/results/events/"
        "D4_combined_dpmf_event.json"
    ),
}


EXPECTED_EXECUTION = {
    "S0": ["F0"],
    "D1": ["F2"],
    "D3": ["F2"],
    "D4": ["F1", "F2"],
}


def load_json(path):
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def as_float(
    value,
    default=0.0,
):
    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default


def get_f1_attribution(
    condition,
    result,
):
    # Generic runner format.
    generic = result.get(
        "F1_attribution",
        {},
    )

    if generic:
        return {
            "active": bool(
                generic.get(
                    "F1_active",
                    False,
                )
            ),
            "clean_removed_count": int(
                generic.get(
                    "F1_clean_removed_count",
                    0,
                )
            ),
            "poisoned_removed_count": int(
                generic.get(
                    "F1_poisoned_removed_count",
                    0,
                )
            ),
            "poison_ids_removed": (
                generic.get(
                    "F1_poison_ids_removed",
                    [],
                )
            ),
            "removed_all_known_poison": bool(
                generic.get(
                    "F1_removed_all_known_poison",
                    False,
                )
            ),
        }

    # Earlier D4 runner format.
    layered = result.get(
        "layered_defense_attribution",
        {},
    )

    if layered:
        return {
            "active": (
                "F1"
                in result.get(
                    "scheduler",
                    {},
                ).get(
                    "execution_order",
                    [],
                )
            ),
            "clean_removed_count": int(
                layered.get(
                    "F1_clean_removed_count",
                    0,
                )
            ),
            "poisoned_removed_count": int(
                layered.get(
                    "F1_poisoned_removed_count",
                    0,
                )
            ),
            "poison_ids_removed": (
                layered.get(
                    "F1_poison_ids_removed",
                    [],
                )
            ),
            "removed_all_known_poison": bool(
                layered.get(
                    "F1_removed_all_known_poison",
                    False,
                )
            ),
        }

    return {
        "active": False,
        "clean_removed_count": 0,
        "poisoned_removed_count": 0,
        "poison_ids_removed": [],
        "removed_all_known_poison": False,
    }


def get_f2_attribution(
    result,
):
    scheduler = result.get(
        "scheduler",
        {},
    )

    execution_order = (
        scheduler.get(
            "execution_order",
            [],
        )
    )

    active = (
        "F2" in execution_order
    )

    metrics = result.get(
        "metrics",
        {},
    )

    selected_rate = (
        metrics.get(
            "poison_selected_before_F2_rate"
        )
    )

    blocked_rate = (
        metrics.get(
            "poison_blocked_by_F2_rate"
        )
    )

    trusted_rate = (
        metrics.get(
            "poison_trusted_after_F2_rate"
        )
    )

    if selected_rate is not None:
        selected_rate = as_float(
            selected_rate
        )

    if blocked_rate is not None:
        blocked_rate = as_float(
            blocked_rate
        )

    if trusted_rate is not None:
        trusted_rate = as_float(
            trusted_rate
        )

    direct_block_rate = (
        metrics.get(
            "F2_block_rate_given_poison_selected"
        )
    )

    if direct_block_rate is not None:
        block_given_selected = (
            as_float(
                direct_block_rate
            )
        )

    elif (
        selected_rate is not None
        and selected_rate > 0
        and blocked_rate is not None
    ):
        block_given_selected = (
            blocked_rate
            / selected_rate
        )

    else:
        block_given_selected = None

    return {
        "active": active,
        "poison_selected_rate": (
            selected_rate
        ),
        "poison_blocked_rate": (
            blocked_rate
        ),
        "poison_trusted_rate": (
            trusted_rate
        ),
        "block_rate_given_selected": (
            block_given_selected
        ),
    }


def mechanism_label(
    condition,
):
    labels = {
        "S0": (
            "Stable state; no additional "
            "defense activated."
        ),
        "D1": (
            "Top-K drift exposes poison; "
            "F2 blocks selected poison "
            "before synthesis."
        ),
        "D3": (
            "History-first selects poison; "
            "F2 blocks selected poison "
            "before synthesis."
        ),
        "D4": (
            "F1 removes known poison before "
            "retrieval; F2 remains active "
            "as the post-retrieval trust gate."
        ),
    }

    return labels[condition]


def normalize_condition(
    condition,
):
    result_path = (
        RESULT_FILES[condition]
    )

    event_path = (
        EVENT_FILES[condition]
    )

    if not result_path.exists():
        raise FileNotFoundError(
            f"Missing Week7 result: "
            f"{result_path}"
        )

    if not event_path.exists():
        raise FileNotFoundError(
            f"Missing Week6 event: "
            f"{event_path}"
        )

    result = load_json(
        result_path
    )

    event = load_json(
        event_path
    )

    scheduler = result.get(
        "scheduler",
        {},
    )

    architecture = result.get(
        "architecture_preserved",
        {},
    )

    metrics = result.get(
        "metrics",
        {},
    )

    execution_order = (
        scheduler.get(
            "execution_order",
            [],
        )
    )

    expected_order = (
        EXPECTED_EXECUTION[
            condition
        ]
    )

    if execution_order != expected_order:
        raise RuntimeError(
            f"{condition}: unexpected "
            f"execution order "
            f"{execution_order}; expected "
            f"{expected_order}"
        )

    query_count = int(
        result.get(
            "query_count",
            0,
        )
    )

    if query_count != 5:
        raise RuntimeError(
            f"{condition}: expected "
            f"5 queries, found "
            f"{query_count}"
        )

    week7_attack_rate = as_float(
        metrics.get(
            "final_attack_success_rate",
            0.0,
        )
    )

    clean_rate = as_float(
        metrics.get(
            "clean_final_answer_correct_rate",
            0.0,
        )
    )

    week6_attack_rate = as_float(
        event.get(
            "behavioral_evidence",
            {},
        ).get(
            "final_attack_success_rate",
            0.0,
        )
    )

    observed_delta = (
        week6_attack_rate
        - week7_attack_rate
    )

    if execution_order == ["F0"]:
        defense_associated_reduction = (
            None
        )
    else:
        defense_associated_reduction = (
            observed_delta
        )

    f1 = get_f1_attribution(
        condition,
        result,
    )

    f2 = get_f2_attribution(
        result
    )

    return {
        "condition": condition,
        "event_id": event.get(
            "event_id"
        ),
        "drift_detected": bool(
            event.get(
                "drift_detection",
                {},
            ).get(
                "drift_detected",
                False,
            )
        ),
        "drift_type": (
            event.get(
                "drift_detection",
                {},
            ).get(
                "drift_type"
            )
        ),
        "risk_score": as_float(
            event.get(
                "risk_assessment",
                {},
            ).get(
                "risk_score"
            )
        ),
        "risk_level": (
            event.get(
                "risk_assessment",
                {},
            ).get(
                "risk_level"
            )
        ),
        "top_k": int(
            architecture.get(
                "top_k",
                event.get(
                    "architecture_state",
                    {},
                ).get(
                    "top_k",
                    0,
                ),
            )
        ),
        "retrieval_policy": (
            architecture.get(
                "retrieval_policy",
                event.get(
                    "architecture_state",
                    {},
                ).get(
                    "retrieval_policy",
                    "",
                ),
            )
        ),
        "primary_defense": (
            scheduler.get(
                "primary"
            )
        ),
        "secondary_defense": (
            scheduler.get(
                "secondary"
            )
        ),
        "execution_order": (
            execution_order
        ),
        "scheduler_ms": as_float(
            scheduler.get(
                "scheduler_ms",
                0.0,
            )
        ),
        "query_count": query_count,
        "clean_final_answer_correct_rate": (
            clean_rate
        ),
        "week6_observed_attack_success_rate": (
            week6_attack_rate
        ),
        "week7_observed_attack_success_rate": (
            week7_attack_rate
        ),
        "attack_failure_rate": (
            1.0
            - week7_attack_rate
        ),
        "observed_attack_success_rate_delta_vs_week6": (
            observed_delta
        ),
        "defense_associated_attack_rate_reduction": (
            defense_associated_reduction
        ),
        "F1": f1,
        "F2": f2,
        "mechanism": (
            mechanism_label(
                condition
            )
        ),
        "source_result": str(
            result_path
        ),
        "source_event": str(
            event_path
        ),
    }


def build_csv_row(
    item,
):
    return {
        "condition": (
            item["condition"]
        ),
        "event_id": (
            item["event_id"]
        ),
        "drift_detected": (
            item["drift_detected"]
        ),
        "drift_type": (
            item["drift_type"]
        ),
        "risk_score": (
            item["risk_score"]
        ),
        "risk_level": (
            item["risk_level"]
        ),
        "top_k": (
            item["top_k"]
        ),
        "retrieval_policy": (
            item["retrieval_policy"]
        ),
        "primary_defense": (
            item["primary_defense"]
        ),
        "secondary_defense": (
            item["secondary_defense"]
        ),
        "execution_order": (
            " -> ".join(
                item[
                    "execution_order"
                ]
            )
        ),
        "scheduler_ms": (
            item["scheduler_ms"]
        ),
        "clean_correct_rate": (
            item[
                "clean_final_answer_correct_rate"
            ]
        ),
        "week6_attack_success_rate": (
            item[
                "week6_observed_attack_success_rate"
            ]
        ),
        "week7_attack_success_rate": (
            item[
                "week7_observed_attack_success_rate"
            ]
        ),
        "observed_attack_delta": (
            item[
                "observed_attack_success_rate_delta_vs_week6"
            ]
        ),
        "defense_associated_reduction": (
            item[
                "defense_associated_attack_rate_reduction"
            ]
        ),
        "F1_active": (
            item["F1"]["active"]
        ),
        "F1_poisoned_removed_count": (
            item[
                "F1"
            ][
                "poisoned_removed_count"
            ]
        ),
        "F1_removed_all_known_poison": (
            item[
                "F1"
            ][
                "removed_all_known_poison"
            ]
        ),
        "F2_active": (
            item["F2"]["active"]
        ),
        "F2_poison_selected_rate": (
            item[
                "F2"
            ][
                "poison_selected_rate"
            ]
        ),
        "F2_poison_blocked_rate": (
            item[
                "F2"
            ][
                "poison_blocked_rate"
            ]
        ),
        "F2_block_rate_given_selected": (
            item[
                "F2"
            ][
                "block_rate_given_selected"
            ]
        ),
        "mechanism": (
            item["mechanism"]
        ),
    }


def main():
    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    conditions = [
        normalize_condition(
            condition
        )
        for condition in (
            "S0",
            "D1",
            "D3",
            "D4",
        )
    ]

    scheduler_times = [
        item["scheduler_ms"]
        for item in conditions
    ]

    summary = {
        "experiment": (
            "week7_dynamic_defense_summary"
        ),
        "created_at": (
            datetime.now()
            .astimezone()
            .isoformat()
        ),
        "condition_count": (
            len(conditions)
        ),
        "query_variants_per_condition": 5,
        "conditions": conditions,
        "aggregate": {
            "all_clean_correct_rate": (
                sum(
                    item[
                        "clean_final_answer_correct_rate"
                    ]
                    for item
                    in conditions
                )
                / len(conditions)
            ),
            "all_week7_attack_success_rate": (
                sum(
                    item[
                        "week7_observed_attack_success_rate"
                    ]
                    for item
                    in conditions
                )
                / len(conditions)
            ),
            "average_scheduler_ms": (
                sum(
                    scheduler_times
                )
                / len(
                    scheduler_times
                )
            ),
            "max_scheduler_ms": max(
                scheduler_times
            ),
            "F2_direct_block_conditions": [
                item["condition"]
                for item in conditions
                if (
                    item[
                        "F2"
                    ][
                        "block_rate_given_selected"
                    ]
                    == 1.0
                )
            ],
            "F1_pre_retrieval_elimination_conditions": [
                item["condition"]
                for item in conditions
                if item[
                    "F1"
                ][
                    "removed_all_known_poison"
                ]
            ],
        },
        "interpretation": {
            "S0": (
                "Stable control remained on F0; "
                "the Week6-to-Week7 attack-rate "
                "difference is observational and "
                "is not attributed to defense."
            ),
            "D1": (
                "F2 directly blocked poisoned "
                "memories exposed by enlarged "
                "Top-K retrieval."
            ),
            "D3": (
                "F2 directly blocked poisoned "
                "memories selected under the "
                "history-first retrieval drift."
            ),
            "D4": (
                "F1 removed both known poisoned "
                "memories before retrieval; F2 "
                "remained active as a layered "
                "post-retrieval safeguard."
            ),
        },
    }

    OUTPUT_JSON.write_text(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    csv_rows = [
        build_csv_row(
            item
        )
        for item in conditions
    ]

    with OUTPUT_CSV.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(
                csv_rows[0].keys()
            ),
        )

        writer.writeheader()
        writer.writerows(
            csv_rows
        )

    print()
    print("=" * 72)
    print("WEEK 7 SUMMARY")
    print("=" * 72)

    for item in conditions:
        print()
        print(
            item["condition"],
            "| Risk:",
            item["risk_score"],
            item["risk_level"],
            "| Defense:",
            " -> ".join(
                item["execution_order"]
            ),
            "| Clean:",
            item[
                "clean_final_answer_correct_rate"
            ],
            "| Week6 ASR:",
            item[
                "week6_observed_attack_success_rate"
            ],
            "| Week7 ASR:",
            item[
                "week7_observed_attack_success_rate"
            ],
        )

    print()
    print(
        "Average scheduler ms:",
        round(
            summary[
                "aggregate"
            ][
                "average_scheduler_ms"
            ],
            4,
        ),
    )

    print()
    print(
        "JSON:",
        OUTPUT_JSON.resolve(),
    )

    print(
        "CSV:",
        OUTPUT_CSV.resolve(),
    )


if __name__ == "__main__":
    main()