"""Regenerate svi_boxplot_analysis_no_title.png with participant-level (n=3,320) annotations.
fix_plan final round — Figure 12 population debt.
Run: .venv/bin/python scripts/regen_svi_boxplot.py
"""
import polars as pl
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pl.read_csv("data/agents_svi_scores.csv").unique(subset=["ID"])
data = df["SVI_normalized"].drop_nulls().to_numpy()
n = len(data)
q1, med, q3 = np.percentile(data, [25, 50, 75])
mean_val = float(np.mean(data))
print(f"n={n} median={med:.3f} Q1={q1:.3f} Q3={q3:.3f} mean={mean_val:.3f}")

PRIMARY = "#2E86AB"; SECONDARY = "#A23B72"; ACCENT = "#F18F01"
zones = [(0.0, 0.25, "#27AE60", "Low\nVulnerability"),
         (0.25, 0.50, "#F39C12", "Moderate\nVulnerability"),
         (0.50, 0.75, "#E67E22", "High\nVulnerability"),
         (0.75, 1.00, "#E74C3C", "Very High\nVulnerability")]

fig, ax = plt.subplots(figsize=(6.685, 6.25))
for x0, x1, c, _ in zones:
    ax.axvspan(x0, x1, color=c, alpha=0.15)
for x_pos, (_, _, c, label) in zip([0.125, 0.375, 0.625, 0.875], zones):
    ax.text(x_pos, 1.42, label, ha="center", va="center", fontsize=12, color=c, fontweight="bold")

bp = ax.boxplot(data, vert=False, patch_artist=True, whis=1.5,
    boxprops=dict(facecolor=PRIMARY, alpha=0.8, linewidth=1.5),
    medianprops=dict(color="white", linewidth=2.5),
    whiskerprops=dict(color=PRIMARY, linewidth=1.5),
    capprops=dict(color=PRIMARY, linewidth=1.5),
    flierprops=dict(marker="o", markerfacecolor=SECONDARY, markeredgecolor=SECONDARY,
                    markersize=4, alpha=0.7))

ax.text(med, 1.25, f"Median: {med:.3f}", ha="center", va="bottom", fontsize=17,
        fontweight="bold", color=PRIMARY,
        bbox=dict(boxstyle="round,pad=0.15", facecolor="white", alpha=0.8, edgecolor=PRIMARY))
ax.text(q1, 0.78, f"Q1: {q1:.3f}", ha="right", va="top", fontsize=14,
        color=PRIMARY, fontweight="semibold")
ax.text(q3, 0.72, f"Q3: {q3:.3f}", ha="left", va="top", fontsize=14,
        color=PRIMARY, fontweight="semibold")
ax.text(mean_val, 0.6, f"Mean: {mean_val:.3f}", ha="center", va="top", fontsize=14,
        color=ACCENT, fontweight="semibold")
ax.text(0.0, -0.32, f"n = {n:,} (participant-level, one SVI per participant)",
        transform=ax.get_xaxis_transform(), fontsize=12, color="#444444", clip_on=False)

ax.set_yticks([])
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.4, 1.5)
ax.set_xlabel("Social Vulnerability Index (SVI) scores", fontsize=15)
for lbl in ax.get_xticklabels(): lbl.set_fontsize(13)
ax.grid(axis="x", color="#E5E5E5", linewidth=0.8)
ax.set_axisbelow(True)
fig.subplots_adjust(bottom=0.18)
fig.tight_layout()
fig.savefig("outputs/figures/svi_analysis/svi_boxplot_analysis_no_title.png", dpi=300,
            bbox_inches="tight")
print("saved outputs/figures/svi_analysis/svi_boxplot_analysis_no_title.png")
