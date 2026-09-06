import json
import sys

from jsonschema import Draft202012Validator


def load_json(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def main():
    if len(sys.argv) != 3:
        print("Usage: python validate_event.py <schema.json> <event.json>")
        sys.exit(1)

    schema = load_json(sys.argv[1])
    event = load_json(sys.argv[2])

    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(event),
        key=lambda e: list(e.path)
    )

    if errors:
        print("=== DPMF Schema Validation ===")
        print("VALID: False")

        for error in errors:
            path = ".".join(str(x) for x in error.path) or "<root>"
            print(f"- {path}: {error.message}")

        sys.exit(1)

    print("=== DPMF Schema Validation ===")
    print("VALID: True")
    print(f"Event ID: {event.get('event_id')}")
    print(f"Drift type: {event.get('drift_type')}")
    print(f"Risk score: {event.get('risk_score')}")
    print(f"Risk level: {event.get('risk_level')}")


if __name__ == "__main__":
    main()
