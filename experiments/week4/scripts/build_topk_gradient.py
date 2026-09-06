import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path("experiments")

RESULT_DIR = ROOT / "week4" / "results" / "topk_gradient"
KB_DIR = ROOT / "week4" / "knowledge_base"
FIG_DIR = ROOT / "week4" / "results" / "figures"

RESULT_DIR.mkdir(parents=True, exist_ok=True)
KB_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

SOURCES = {
    ("F0", 3): ROOT / "week3" / "results" / "topk3_baseline.json",
    ("F0", 4): RESULT_DIR / "F0_topk4.json",
    ("F0", 5): ROOT / "week3" / "results" / "topk5_drift.json",
    ("F0", 6): RESULT_DIR / "F0_topk6.json",

    ("F1", 3): RESULT_DIR / "F1_topk3.json",
    ("F1", 4): RESULT_DIR / "F1_topk4.json",
    ("F1", 5): ROOT / "week4" / "results" / "F1_D1_topk5.json",
    ("F1", 6): RESULT_DIR / "F1_topk6.json",

    ("F2", 3): ROOT / "week4" / "results" / "F2_topk3_baseline.json",
    ("F2", 4): RESULT_DIR / "F2_topk4.json",
    ("F2", 5): ROOT / "week4" / "results" / "F2_D1_topk5.json",
    ("F2", 6): RESULT_DIR / "F2_topk6.json",
}

DEFENSE_NAMES = {
    "F0": "No Defense",
    "F1": "Pre-Retrieval Filter",
    "F2": "Retrieval Trust Gate",
}


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def metric(data, key, default=None):
    metrics = data.get("metrics", data)

    if key in metrics:
        return metrics[key]

    if key in data:
        return data[key]

    return default


rows = []

for defense in ("F0", "F1", "F2"):
    for top_k in (3, 4, 5, 6):
        path = SOURCES[(defense, top_k)]

        if not path.exists():
            raise FileNotFoundError(path)

        data = load_json(path)

        clean_correct_rate = float(
            metric(data, "clean_correct_rate", 0.0)
        )

        attack_success_rate = float(
            metric(data, "attack_success_rate", 0.0)
        )

        if defense == "F0":
            defense_block_rate = 0.0
        else:
            defense_block_rate = float(
                metric(
                    data,
                    "defense_block_rate",
                    1.0 - attack_success_rate,
                )
            )

        if defense == "F0":
            poison_exposure_rate = metric(
                data,
                "poison_hit_at_k_rate",
                metric(
                    data,
                    "poison_hit_at_3_rate",
                    1.0,
                ),
            )
        elif defense == "F1":
            poison_exposure_rate = metric(
                data,
                "poison_hit_after_defense_rate",
                0.0,
            )
        else:
            poison_exposure_rate = metric(
                data,
                "poison_selected_before_gate_rate",
                1.0,
            )

        if defense == "F1":
            false_positive_rate = 0.0
        elif defense == "F2":
            false_positive_rate = float(
                metric(
                    data,
                    "clean_blocked_trial_rate",
                    0.0,
                )
            )
        else:
            false_positive_rate = 0.0

        rows.append(
            {
                "drift_type": "D1_topk_gradient",
                "top_k": top_k,
                "defense_id": defense,
                "defense_name": DEFENSE_NAMES[defense],
                "clean_correct_rate": clean_correct_rate,
                "attack_success_rate": attack_success_rate,
                "defense_block_rate": defense_block_rate,
                "poison_exposure_rate": float(
                    poison_exposure_rate
                ),
                "false_positive_rate": false_positive_rate,
                "source_file": str(path),
            }
        )


csv_path = KB_DIR / "topk_gradient_mapping_v0.csv"

with csv_path.open(
    "w",
    encoding="utf-8-sig",
    newline="",
) as f:
    writer = csv.DictWriter(
        f,
        fieldnames=list(rows[0].keys()),
    )
    writer.writeheader()
    writer.writerows(rows)


json_path = RESULT_DIR / "topk_gradient_summary.json"

json_path.write_text(
    json.dumps(
        {
            "experiment": "week4_D1_topk_gradient",
            "top_k_values": [3, 4, 5, 6],
            "defenses": ["F0", "F1", "F2"],
            "rows": rows,
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)


def series(defense, field):
    return [
        next(
            row[field]
            for row in rows
            if (
                row["defense_id"] == defense
                and row["top_k"] == top_k
            )
        )
        for top_k in (3, 4, 5, 6)
    ]


x = [3, 4, 5, 6]

plt.figure(figsize=(8, 5))

for defense in ("F0", "F1", "F2"):
    y = series(
        defense,
        "clean_correct_rate",
    )

    plt.plot(
        x,
        y,
        marker="o",
        linewidth=2,
        label=f"{defense} {DEFENSE_NAMES[defense]}",
    )

    for px, py in zip(x, y):
        plt.text(
            px,
            py + 0.035,
            f"{py:.1f}",
            ha="center",
            fontsize=8,
        )

plt.xticks(x)
plt.ylim(-0.05, 1.12)
plt.xlabel("Top-K")
plt.ylabel("Clean Correct Rate")
plt.title(
    "Clean-Task Utility under Increasing Top-K Drift"
)
plt.grid(
    axis="y",
    alpha=0.25,
)
plt.legend()
plt.tight_layout()

clean_fig = (
    FIG_DIR
    / "topk_gradient_clean_utility.png"
)

plt.savefig(
    clean_fig,
    dpi=220,
)

plt.close()


plt.figure(figsize=(8, 5))

for defense in ("F0", "F1", "F2"):
    y = series(
        defense,
        "attack_success_rate",
    )

    plt.plot(
        x,
        y,
        marker="o",
        linewidth=2,
        label=f"{defense} {DEFENSE_NAMES[defense]}",
    )

plt.xticks(x)
plt.ylim(-0.05, 1.12)
plt.xlabel("Top-K")
plt.ylabel("Attack Success Rate")
plt.title(
    "Defense Security under Increasing Top-K Drift"
)
plt.grid(
    axis="y",
    alpha=0.25,
)
plt.legend()
plt.tight_layout()

attack_fig = (
    FIG_DIR
    / "topk_gradient_attack_success.png"
)

plt.savefig(
    attack_fig,
    dpi=220,
)

plt.close()


print()
print("=== TOP-K GRADIENT SUMMARY ===")

for row in rows:
    print(
        f"{row['defense_id']} "
        f"K={row['top_k']} "
        f"clean={row['clean_correct_rate']} "
        f"attack={row['attack_success_rate']} "
        f"block={row['defense_block_rate']}"
    )

print()
print("CSV:", csv_path.resolve())
print("JSON:", json_path.resolve())
print("Clean curve:", clean_fig.resolve())
print("Attack curve:", attack_fig.resolve())
