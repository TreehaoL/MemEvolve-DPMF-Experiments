import csv
from pathlib import Path

import matplotlib.pyplot as plt

CSV_PATH = Path(
    "experiments/week4/knowledge_base/"
    "architecture_defense_mapping_v0.csv"
)

FIG_DIR = Path(
    "experiments/week4/results/figures"
)

FIG_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

with CSV_PATH.open(
    "r",
    encoding="utf-8-sig",
) as f:
    rows = list(csv.DictReader(f))

drifts = ["D1", "D2"]
defenses = ["F0", "F1", "F2"]

labels = {
    "F0": "F0 No Defense",
    "F1": "F1 Pre-Retrieval Filter",
    "F2": "F2 Retrieval Trust Gate",
}


def value(drift, defense, field):
    for row in rows:
        if (
            row["drift_id"] == drift
            and row["defense_id"] == defense
        ):
            return float(row[field])

    raise KeyError(
        f"Missing {drift}/{defense}/{field}"
    )


x = list(range(len(drifts)))
width = 0.22


# --------------------------------------------------
# Figure 1: Clean-task utility
# --------------------------------------------------

plt.figure(figsize=(8, 5))

for i, defense in enumerate(defenses):
    values = [
        value(
            drift,
            defense,
            "clean_correct_rate",
        )
        for drift in drifts
    ]

    positions = [
        p + (i - 1) * width
        for p in x
    ]

    bars = plt.bar(
        positions,
        values,
        width=width,
        label=labels[defense],
    )

    for bar, metric in zip(bars, values):
        plt.text(
            bar.get_x()
            + bar.get_width() / 2,
            metric + 0.025,
            f"{metric:.1f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

plt.xticks(
    x,
    [
        "D1: Top-K 3→5",
        "D2: History-First",
    ],
)

plt.ylim(0, 1.12)
plt.ylabel("Clean Correct Rate")
plt.title(
    "Clean-Task Utility under Architecture Drift"
)
plt.legend()
plt.tight_layout()

utility_path = (
    FIG_DIR
    / "clean_utility_comparison.png"
)

plt.savefig(
    utility_path,
    dpi=200,
)

plt.close()


# --------------------------------------------------
# Figure 2: Attack success
# --------------------------------------------------

plt.figure(figsize=(8, 5))

for i, defense in enumerate(defenses):
    values = [
        value(
            drift,
            defense,
            "attack_success_rate",
        )
        for drift in drifts
    ]

    positions = [
        p + (i - 1) * width
        for p in x
    ]

    bars = plt.bar(
        positions,
        values,
        width=width,
        label=labels[defense],
    )

    for bar, metric in zip(bars, values):
        plt.text(
            bar.get_x()
            + bar.get_width() / 2,
            metric + 0.025,
            f"{metric:.1f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

plt.xticks(
    x,
    [
        "D1: Top-K 3→5",
        "D2: History-First",
    ],
)

plt.ylim(0, 1.12)
plt.ylabel("Attack Success Rate")
plt.title(
    "Poisoning Attack Success under Architecture Drift"
)
plt.legend()
plt.tight_layout()

security_path = (
    FIG_DIR
    / "attack_success_comparison.png"
)

plt.savefig(
    security_path,
    dpi=200,
)

plt.close()


print("Generated figures:")
print(utility_path.resolve())
print(security_path.resolve())
