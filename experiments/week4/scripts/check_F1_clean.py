import json
from pathlib import Path

USAGE_THRESHOLD = 10
SUCCESS_RATE_THRESHOLD = 0.95

def is_suspicious(memory):
    usage_count = memory.get("usage_count", 0)
    success_count = memory.get("success_count", 0)

    success_rate = (
        success_count / usage_count
        if usage_count > 0
        else 0.0
    )

    return (
        usage_count >= USAGE_THRESHOLD
        and success_rate >= SUCCESS_RATE_THRESHOLD
    )

source_path = Path(
    "experiments/week2/baseline/longterm_memory_clean.json"
)

result_path = Path(
    "experiments/week4/results/F1_clean_filter_check.json"
)

with source_path.open("r", encoding="utf-8") as f:
    data = json.load(f)

all_memories = []

for memory_type in ("strategic", "operational"):
    for memory in data.get(memory_type, []):
        all_memories.append(
            {
                "memory_type": memory_type,
                **memory,
            }
        )

removed = [
    memory
    for memory in all_memories
    if is_suspicious(memory)
]

total = len(all_memories)
false_positive_count = len(removed)

false_positive_rate = (
    false_positive_count / total
    if total > 0
    else 0.0
)

result = {
    "experiment": "Week4_F1_clean_filter_check",
    "total_clean_memories": total,
    "false_positive_count": false_positive_count,
    "false_positive_rate": false_positive_rate,
    "removed_memories": removed,
    "defense": {
        "usage_threshold": USAGE_THRESHOLD,
        "success_rate_threshold": SUCCESS_RATE_THRESHOLD,
    },
}

with result_path.open("w", encoding="utf-8") as f:
    json.dump(
        result,
        f,
        ensure_ascii=False,
        indent=2,
    )

print("=== WEEK 4 / F1 CLEAN FILTER CHECK ===")
print("Total clean memories:", total)
print("False positive count:", false_positive_count)
print("False positive rate:", false_positive_rate)

if removed:
    for index, item in enumerate(removed, start=1):
        print(f"\nFalse positive {index}:")
        print(item["content"])

print("\nResult saved to:")
print(result_path)
