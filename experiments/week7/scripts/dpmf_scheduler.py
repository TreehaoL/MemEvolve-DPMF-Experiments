import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


VALID_DEFENSES = {
    "F0",
    "F1",
    "F2",
}


def normalize_defense_id(
    defense_id: Optional[str],
) -> Optional[str]:
    if defense_id is None:
        return None

    normalized = str(defense_id).strip().upper()

    if normalized in {
        "NONE",
        "NO_DEFENSE",
        "NULL",
        "",
    }:
        return "F0"

    if normalized not in VALID_DEFENSES:
        return None

    return normalized


def infer_drift_id(
    condition: str,
) -> Optional[str]:
    condition = condition.strip().upper()

    for drift_id in (
        "D1",
        "D2",
        "D3",
        "D4",
    ):
        if condition.startswith(drift_id):
            return drift_id

    return None


def load_json(
    path: Path,
) -> Dict[str, Any]:
    return json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )


def load_mapping_rows(
    mapping_path: Path,
) -> List[Dict[str, str]]:
    if not mapping_path.exists():
        return []

    with mapping_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as f:
        return list(
            csv.DictReader(f)
        )


def find_mapping_rows(
    rows: List[Dict[str, str]],
    drift_id: Optional[str],
    drift_type: str,
) -> List[Dict[str, str]]:
    matched = []

    for row in rows:
        row_drift_id = (
            row.get(
                "drift_id",
                "",
            )
            .strip()
            .upper()
        )

        row_drift_type = (
            row.get(
                "drift_type",
                "",
            )
            .strip()
            .lower()
        )

        id_match = (
            drift_id is not None
            and row_drift_id == drift_id
        )

        type_match = (
            drift_type
            and row_drift_type
            == drift_type.strip().lower()
        )

        if id_match or type_match:
            matched.append(row)

    return matched


def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default


def choose_mapping_fallback(
    mapping_rows: List[Dict[str, str]],
) -> Optional[str]:
    """
    Used only when the DPMF event does not provide a valid
    defense recommendation.

    Preference:
    1. effective security
    2. lower attack success
    3. higher clean correctness
    """

    candidates = []

    for row in mapping_rows:
        defense_id = normalize_defense_id(
            row.get("defense_id")
        )

        if defense_id is None:
            continue

        security_status = (
            row.get(
                "security_status",
                "",
            )
            .strip()
            .lower()
        )

        effective = (
            1
            if security_status == "effective"
            else 0
        )

        attack_success = safe_float(
            row.get(
                "attack_success_rate"
            ),
            1.0,
        )

        clean_correct = safe_float(
            row.get(
                "clean_correct_rate"
            ),
            0.0,
        )

        candidates.append(
            (
                effective,
                -attack_success,
                clean_correct,
                defense_id,
            )
        )

    if not candidates:
        return None

    candidates.sort(
        reverse=True
    )

    return candidates[0][3]


def build_mapping_evidence(
    mapping_rows: List[Dict[str, str]],
) -> List[Dict[str, Any]]:
    evidence = []

    for row in mapping_rows:
        evidence.append(
            {
                "drift_id": (
                    row.get("drift_id")
                ),
                "drift_type": (
                    row.get("drift_type")
                ),
                "defense_id": (
                    row.get("defense_id")
                ),
                "clean_correct_rate": (
                    safe_float(
                        row.get(
                            "clean_correct_rate"
                        )
                    )
                ),
                "attack_success_rate": (
                    safe_float(
                        row.get(
                            "attack_success_rate"
                        )
                    )
                ),
                "defense_block_rate": (
                    safe_float(
                        row.get(
                            "defense_block_rate"
                        )
                    )
                ),
                "security_status": (
                    row.get(
                        "security_status"
                    )
                ),
                "utility_status": (
                    row.get(
                        "utility_status"
                    )
                ),
                "mapping_note": (
                    row.get(
                        "mapping_note"
                    )
                ),
            }
        )

    return evidence


def build_execution_order(
    primary: str,
    secondary: Optional[str],
) -> List[str]:
    """
    Recommendation priority and physical execution order are
    intentionally different.

    F1 = pre-retrieval filtering
    F2 = post-retrieval / pre-synthesis trust gate

    Therefore F1 must execute before F2 when both are active.
    """

    active = {
        item
        for item in (
            primary,
            secondary,
        )
        if item
        and item != "F0"
    }

    order = []

    if "F1" in active:
        order.append("F1")

    if "F2" in active:
        order.append("F2")

    if not order:
        order.append("F0")

    return order


def schedule_defense(
    event: Dict[str, Any],
    mapping_rows: List[Dict[str, str]],
    event_path: Path,
    mapping_path: Path,
) -> Dict[str, Any]:
    condition = event.get(
        "condition",
        "unknown",
    )

    drift_detection = event.get(
        "drift_detection",
        {},
    )

    risk_assessment = event.get(
        "risk_assessment",
        {},
    )

    recommendation = event.get(
        "defense_recommendation",
        {},
    )

    drift_detected = bool(
        drift_detection.get(
            "drift_detected",
            False,
        )
    )

    drift_type = str(
        drift_detection.get(
            "drift_type",
            "none",
        )
    )

    drift_id = infer_drift_id(
        condition
    )

    matched_mapping_rows = (
        find_mapping_rows(
            mapping_rows,
            drift_id,
            drift_type,
        )
    )

    event_primary = normalize_defense_id(
        recommendation.get(
            "primary"
        )
    )

    event_secondary = normalize_defense_id(
        recommendation.get(
            "secondary"
        )
    )

    decision_source = None
    decision_reason = None

    # --------------------------------------------------
    # Rule 1:
    # Stable state always remains F0.
    # --------------------------------------------------

    if not drift_detected:
        primary = "F0"
        secondary = None

        decision_source = (
            "dpmf_stable_state"
        )

        decision_reason = (
            "No architectural drift was detected; "
            "keep the current architecture and "
            "activate no additional defense."
        )

    # --------------------------------------------------
    # Rule 2:
    # Prefer the recommendation produced directly by
    # the DPMF event.
    # --------------------------------------------------

    elif (
        event_primary is not None
        and event_primary != "F0"
    ):
        primary = event_primary

        if (
            event_secondary
            and event_secondary != "F0"
            and event_secondary
            != primary
        ):
            secondary = (
                event_secondary
            )
        else:
            secondary = None

        decision_source = (
            "dpmf_event_recommendation"
        )

        decision_reason = (
            "The DPMF event contains an explicit "
            "defense recommendation."
        )

    # --------------------------------------------------
    # Rule 3:
    # If recommendation is missing or invalid, query the
    # architecture-defense mapping knowledge base.
    # --------------------------------------------------

    else:
        fallback = (
            choose_mapping_fallback(
                matched_mapping_rows
            )
        )

        if fallback is not None:
            primary = fallback
            secondary = None

            decision_source = (
                "architecture_defense_mapping"
            )

            decision_reason = (
                "The DPMF event did not contain "
                "a usable recommendation; defense "
                "was selected from the mapping "
                "knowledge base."
            )

        else:
            # Conservative fallback.
            primary = "F2"
            secondary = None

            decision_source = (
                "scheduler_safe_fallback"
            )

            decision_reason = (
                "Neither the DPMF recommendation "
                "nor the mapping knowledge base "
                "provided a usable defense. "
                "F2 was selected as the conservative "
                "retrieval-time fallback."
            )

    execution_order = (
        build_execution_order(
            primary,
            secondary,
        )
    )

    selected_defenses = [
        primary
    ]

    if secondary:
        selected_defenses.append(
            secondary
        )

    mapping_primary_match = False

    for row in matched_mapping_rows:
        row_defense = (
            normalize_defense_id(
                row.get(
                    "defense_id"
                )
            )
        )

        if row_defense == primary:
            mapping_primary_match = True
            break

    if not matched_mapping_rows:
        mapping_validation = (
            "mapping_not_available"
        )
    elif mapping_primary_match:
        mapping_validation = (
            "recommendation_supported"
        )
    else:
        mapping_validation = (
            "recommendation_not_in_mapping"
        )

    decision = {
        "scheduler_version": (
            "week7_dpmf_scheduler_v1"
        ),
        "created_at": (
            datetime.now()
            .astimezone()
            .isoformat()
        ),
        "source_event": {
            "path": str(
                event_path
            ),
            "event_id": event.get(
                "event_id"
            ),
            "condition": condition,
        },
        "dpmf_state": {
            "drift_detected": (
                drift_detected
            ),
            "drift_id": drift_id,
            "drift_type": (
                drift_type
            ),
            "structural_score": (
                safe_float(
                    drift_detection.get(
                        "structural_score"
                    )
                )
            ),
            "risk_score": (
                safe_float(
                    risk_assessment.get(
                        "risk_score"
                    )
                )
            ),
            "risk_level": (
                risk_assessment.get(
                    "risk_level"
                )
            ),
        },
        "event_recommendation": {
            "primary": (
                recommendation.get(
                    "primary"
                )
            ),
            "secondary": (
                recommendation.get(
                    "secondary"
                )
            ),
            "action": (
                recommendation.get(
                    "action"
                )
            ),
        },
        "scheduler_decision": {
            "primary": primary,
            "secondary": secondary,
            "selected_defenses": (
                selected_defenses
            ),
            "execution_order": (
                execution_order
            ),
            "decision_source": (
                decision_source
            ),
            "decision_reason": (
                decision_reason
            ),
        },
        "mapping_validation": {
            "mapping_path": (
                str(mapping_path)
            ),
            "matched_row_count": (
                len(
                    matched_mapping_rows
                )
            ),
            "status": (
                mapping_validation
            ),
            "evidence": (
                build_mapping_evidence(
                    matched_mapping_rows
                )
            ),
        },
        "dpmf_evidence": event.get(
            "evidence",
            [],
        ),
    }

    return decision


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Week7 DPMF dynamic defense scheduler"
        )
    )

    parser.add_argument(
        "--event",
        required=True,
        help=(
            "Path to a Week6 DPMF event JSON"
        ),
    )

    parser.add_argument(
        "--mapping",
        default=(
            "experiments/week4/"
            "knowledge_base/"
            "architecture_defense_mapping_v0.csv"
        ),
        help=(
            "Architecture-defense mapping CSV"
        ),
    )

    parser.add_argument(
        "--output",
        required=True,
        help=(
            "Output scheduler decision JSON"
        ),
    )

    args = parser.parse_args()

    event_path = Path(
        args.event
    )

    mapping_path = Path(
        args.mapping
    )

    output_path = Path(
        args.output
    )

    if not event_path.exists():
        raise FileNotFoundError(
            f"DPMF event not found: "
            f"{event_path}"
        )

    event = load_json(
        event_path
    )

    mapping_rows = (
        load_mapping_rows(
            mapping_path
        )
    )

    decision = schedule_defense(
        event=event,
        mapping_rows=mapping_rows,
        event_path=event_path,
        mapping_path=mapping_path,
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            decision,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    scheduler_decision = (
        decision[
            "scheduler_decision"
        ]
    )

    state = decision[
        "dpmf_state"
    ]

    validation = decision[
        "mapping_validation"
    ]

    print()
    print("=" * 72)
    print(
        "WEEK 7 DPMF DEFENSE SCHEDULER"
    )
    print("=" * 72)

    print(
        "Event:",
        decision[
            "source_event"
        ]["event_id"],
    )

    print(
        "Condition:",
        decision[
            "source_event"
        ]["condition"],
    )

    print(
        "Drift detected:",
        state["drift_detected"],
    )

    print(
        "Drift type:",
        state["drift_type"],
    )

    print(
        "Risk:",
        state["risk_score"],
        state["risk_level"],
    )

    print(
        "Primary defense:",
        scheduler_decision[
            "primary"
        ],
    )

    print(
        "Secondary defense:",
        scheduler_decision[
            "secondary"
        ],
    )

    print(
        "Execution order:",
        " -> ".join(
            scheduler_decision[
                "execution_order"
            ]
        ),
    )

    print(
        "Decision source:",
        scheduler_decision[
            "decision_source"
        ],
    )

    print(
        "Mapping validation:",
        validation["status"],
    )

    print()
    print(
        "Decision saved to:"
    )
    print(
        output_path.resolve()
    )


if __name__ == "__main__":
    main()