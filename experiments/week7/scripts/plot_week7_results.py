import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


# ============================================================
# Paths
# ============================================================

SUMMARY_PATH = Path(
    "experiments/week7/results/week7_summary.json"
)

FIGURE_DIR = Path(
    "experiments/week7/results/figures"
)

FIGURE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# Load
# ============================================================

summary = json.loads(
    SUMMARY_PATH.read_text(
        encoding="utf-8"
    )
)

conditions = summary["conditions"]

labels = [
    item["condition"]
    for item in conditions
]

week6_asr = [
    item[
        "week6_observed_attack_success_rate"
    ]
    for item in conditions
]

week7_asr = [
    item[
        "week7_observed_attack_success_rate"
    ]
    for item in conditions
]

clean_rates = [
    item[
        "clean_final_answer_correct_rate"
    ]
    for item in conditions
]

risk_scores = [
    item["risk_score"]
    for item in conditions
]


# ============================================================
# Figure 1
# Attack success before / after dynamic defense
# ============================================================

x = np.arange(
    len(labels)
)

width = 0.34

fig, ax = plt.subplots(
    figsize=(9.5, 5.8)
)

bars_week6 = ax.bar(
    x - width / 2,
    week6_asr,
    width,
    label="Week 6 observed ASR",
)

bars_week7 = ax.bar(
    x + width / 2,
    week7_asr,
    width,
    label="Week 7 closed-loop ASR",
)

ax.set_title(
    "Attack Success Rate Before and After Dynamic Defense"
)

ax.set_xlabel(
    "Architecture Condition"
)

ax.set_ylabel(
    "Attack Success Rate"
)

ax.set_xticks(
    x
)

ax.set_xticklabels(
    labels
)

ax.set_ylim(
    0,
    1.05,
)

ax.legend()

ax.grid(
    axis="y",
    alpha=0.25,
)

for bars in (
    bars_week6,
    bars_week7,
):
    for bar in bars:
        height = (
            bar.get_height()
        )

        ax.annotate(
            f"{height:.2f}",
            xy=(
                bar.get_x()
                + bar.get_width() / 2,
                height,
            ),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )

# S0 difference is not attributable to defense.
ax.annotate(
    "observational difference\n(no defense activated)",
    xy=(
        x[0],
        max(
            week6_asr[0],
            0.05,
        ),
    ),
    xytext=(25, 45),
    textcoords="offset points",
    ha="left",
    fontsize=8,
    arrowprops={
        "arrowstyle": "->",
    },
)

fig.tight_layout()

figure1_path = (
    FIGURE_DIR
    / "week7_attack_success_comparison.png"
)

fig.savefig(
    figure1_path,
    dpi=220,
    bbox_inches="tight",
)

plt.close(fig)


# ============================================================
# Figure 2
# DPMF risk score and dynamic defense adaptation
# ============================================================

defense_labels = [
    "F0",
    "F2",
    "F2",
    "F1 -> F2",
]

drift_labels = [
    "Stable",
    "Top-K drift",
    "Policy drift",
    "Combined drift",
]

fig, ax = plt.subplots(
    figsize=(9.5, 5.8)
)

bars = ax.bar(
    x,
    risk_scores,
    width=0.55,
)

ax.set_title(
    "DPMF Risk Score and Dynamic Defense Adaptation"
)

ax.set_xlabel(
    "Architecture Condition"
)

ax.set_ylabel(
    "DPMF Risk Score"
)

ax.set_xticks(
    x
)

ax.set_xticklabels(
    labels
)

ax.set_ylim(
    0,
    0.75,
)

ax.grid(
    axis="y",
    alpha=0.25,
)


# ------------------------------------------------------------
# Risk-level reference bands
# These labels reflect the actual Week6 risk classification.
# ------------------------------------------------------------

ax.axhline(
    0.3,
    linestyle="--",
    linewidth=1,
    alpha=0.6,
)

ax.axhline(
    0.6,
    linestyle="--",
    linewidth=1,
    alpha=0.6,
)

ax.text(
    3.45,
    0.15,
    "LOW",
    ha="right",
    va="center",
    fontsize=9,
)

ax.text(
    3.45,
    0.45,
    "MEDIUM",
    ha="right",
    va="center",
    fontsize=9,
)

ax.text(
    3.45,
    0.675,
    "HIGH",
    ha="right",
    va="center",
    fontsize=9,
)


# ------------------------------------------------------------
# Annotate risk score, drift type and scheduler decision
# ------------------------------------------------------------

for index, bar in enumerate(
    bars
):
    height = bar.get_height()

    ax.annotate(
        f"Risk = {height:.4f}",
        xy=(
            bar.get_x()
            + bar.get_width() / 2,
            height,
        ),
        xytext=(0, 5),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=9,
    )

    ax.text(
        bar.get_x()
        + bar.get_width() / 2,
        max(
            height * 0.50,
            0.07,
        ),
        (
            f"{drift_labels[index]}\n"
            f"Defense: {defense_labels[index]}"
        ),
        ha="center",
        va="center",
        fontsize=9,
    )


fig.tight_layout()

figure2_path = (
    FIGURE_DIR
    / "week7_dynamic_defense_adaptation.png"
)

fig.savefig(
    figure2_path,
    dpi=220,
    bbox_inches="tight",
)

plt.close(fig)


# ============================================================
# Console summary
# ============================================================

print()
print("=" * 72)
print("WEEK 7 FIGURES")
print("=" * 72)

print(
    "Attack comparison:"
)

print(
    figure1_path.resolve()
)

print()

print(
    "Dynamic defense adaptation:"
)

print(
    figure2_path.resolve()
)