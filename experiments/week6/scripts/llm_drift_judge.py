import json
import os
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv(override=True)

API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL_NAME = os.getenv("DEFAULT_MODEL")

if not API_KEY or not BASE_URL or not MODEL_NAME:
    raise RuntimeError(
        "Missing API configuration in .env"
    )


client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
)


INPUT_PATH = Path(
    "experiments/week6/results/dpmf_end_to_end.json"
)

RESULT_PATH = Path(
    "experiments/week6/results/llm_judge_reports.json"
)


def call_llm(messages):
    last_error = None

    for attempt in range(1, 4):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0,
            )

            return (
                response
                .choices[0]
                .message
                .content
                or ""
            )

        except Exception as exc:
            last_error = exc

            print(
                f"[Retry {attempt}/3] "
                f"{type(exc).__name__}: {exc}"
            )

            if attempt < 3:
                time.sleep(attempt * 2)

    raise RuntimeError(
        f"LLM call failed: {last_error}"
    )


def build_prompt(event):
    data = {
        "condition": event["condition"],
        "reference_architecture": (
            event["reference_architecture"]
        ),
        "architecture_state": (
            event["architecture_state"]
        ),
        "drift_detection": (
            event["drift_detection"]
        ),
        "behavioral_evidence": (
            event["behavioral_evidence"]
        ),
        "risk_assessment": (
            event["risk_assessment"]
        ),
        "defense_recommendation": (
            event["defense_recommendation"]
        ),
        "evidence": event["evidence"],
    }

    return (
        "You are the explanation module of a "
        "memory-architecture drift monitoring system.\n\n"

        "IMPORTANT RULES:\n"
        "1. Do NOT independently decide whether drift occurred.\n"
        "2. Do NOT change the supplied drift type.\n"
        "3. Do NOT change the supplied risk score or risk level.\n"
        "4. Do NOT invent a new defense recommendation.\n"
        "5. Your task is only to explain the structured DPMF result.\n"
        "6. Distinguish structural architecture drift from ordinary "
        "retrieval behavioral fluctuation.\n"
        "7. Keep the explanation concise and technically grounded.\n\n"

        "Return valid JSON only, using this schema:\n"
        "{\n"
        '  "summary": "...",\n'
        '  "structural_explanation": "...",\n'
        '  "behavioral_explanation": "...",\n'
        '  "risk_explanation": "...",\n'
        '  "defense_explanation": "...",\n'
        '  "confidence_note": "..."\n'
        "}\n\n"

        "DPMF structured result:\n"
        + json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        )
    )


def parse_json_response(text):
    cleaned = text.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        cleaned = "\n".join(lines).strip()

        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

    try:
        return json.loads(cleaned)

    except json.JSONDecodeError:
        return {
            "parse_success": False,
            "raw_response": text,
        }


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(INPUT_PATH)

    pipeline = json.loads(
        INPUT_PATH.read_text(
            encoding="utf-8"
        )
    )

    events = pipeline["events"]

    reports = []

    print("=" * 80)
    print("WEEK 6 LLM-AS-JUDGE EXPLANATION")
    print("=" * 80)
    print("Model:", MODEL_NAME)
    print("Events:", len(events))

    for event in events:
        condition = event["condition"]

        print()
        print("-" * 80)
        print("Condition:", condition)

        messages = [
            {
                "role": "system",
                "content": (
                    "You explain DPMF drift-detection "
                    "results. You are not the drift "
                    "detector itself."
                ),
            },
            {
                "role": "user",
                "content": build_prompt(event),
            },
        ]

        raw_response = call_llm(messages)

        parsed = parse_json_response(
            raw_response
        )

        report = {
            "condition": condition,
            "event_id": event["event_id"],
            "model": MODEL_NAME,
            "source_drift_detected": (
                event[
                    "drift_detection"
                ]["drift_detected"]
            ),
            "source_drift_type": (
                event[
                    "drift_detection"
                ]["drift_type"]
            ),
            "source_risk_score": (
                event[
                    "risk_assessment"
                ]["risk_score"]
            ),
            "source_risk_level": (
                event[
                    "risk_assessment"
                ]["risk_level"]
            ),
            "source_primary_defense": (
                event[
                    "defense_recommendation"
                ]["primary"]
            ),
            "llm_explanation": parsed,
            "raw_response": raw_response,
        }

        reports.append(report)

        print(
            "Drift:",
            report["source_drift_detected"],
        )

        print(
            "Type:",
            report["source_drift_type"],
        )

        print(
            "Risk:",
            report["source_risk_score"],
            report["source_risk_level"],
        )

        if isinstance(parsed, dict):
            print(
                "LLM summary:",
                parsed.get(
                    "summary",
                    parsed.get(
                        "raw_response",
                        "",
                    ),
                ),
            )

    result = {
        "experiment": (
            "week6_llm_as_judge_explanation"
        ),
        "created_at": (
            datetime.now()
            .astimezone()
            .isoformat()
        ),
        "model": MODEL_NAME,
        "role": (
            "post-hoc explanation only; "
            "not drift decision"
        ),
        "event_count": len(reports),
        "reports": reports,
    }

    RESULT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    RESULT_PATH.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 80)
    print("LLM EXPLANATION COMPLETE")
    print("=" * 80)
    print(
        "Result:",
        RESULT_PATH.resolve(),
    )


if __name__ == "__main__":
    main()