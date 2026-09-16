"""Regenerate Figures 31-32 from canonical results (fix_plan_v3 §1.1).
Run: .venv/bin/python scripts/generate_figures_31_32.py
Reads ONLY outputs/results_canonical.json + outputs/canonical_agent_states.csv.
"""
import json, csv, math, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
res = json.load(open("outputs/results_canonical.json"))
rows = list(csv.DictReader(open("outputs/canonical_agent_states.csv")))

def wilson(e, n, z=1.959963984540054):
    p = e/n; den = 1 + z*z/n
    c = (p + z*z/(2*n))/den
    half = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/den
    return 100*(c-half), 100*(c+half)

FIGDIR = "/home/youssef/projects/SEEM-Paper"

# --- Figure 31: aggregation-rule sensitivity (rules coincide at 1:1) ---
c = res["completion"]["any_arrival"]
e, n = c["events"], c["n"]
lo, hi = c["ci95"]
fig, ax = plt.subplots(figsize=(7, 5))
ax.errorbar([1], [e/n*100], yerr=[[e/n*100-lo], [hi-e/n*100]],
            fmt="o", color="#1f77b4", markersize=10, capsize=6, linewidth=2)
ax.annotate(f"{e}/{n}", (1, e/n*100), textcoords="offset points", xytext=(12, 8), fontsize=12)
ax.set_xlim(0.5, 1.5)
ax.set_xticks([1])
ax.set_xticklabels(["All three rules coincide\n(one record per participant)"], fontsize=11)
ax.set_ylabel("Participant-level completion (%)", fontsize=12)
ax.set_title("Completion estimate: canonical run (153 participants)\n95% Wilson intervals; three aggregation rules coincide", fontsize=12)
ax.set_ylim(0, 20)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(f"{FIGDIR}/canonical_completion_rules_coincide.png", dpi=200)
plt.close(fig)
print("Fig 31 saved: canonical_completion_rules_coincide.png")

# --- Figure 32: participant quartile completion ---
# Recompute band assignment exactly as generate_stats.py (empirical quartiles)
svi = sorted(float(r["svi"]) for r in rows)
def pct(v, q):
    pos = (len(v)-1)*q; lo, hi = math.floor(pos), math.ceil(pos)
    return v[lo] + (v[hi]-v[lo])*(pos-lo)
Q1, Q2, Q3 = pct(svi,.25), pct(svi,.5), pct(svi,.75)
def band(s):
    return "Low" if s <= Q1 else "Moderate" if s <= Q2 else "High" if s <= Q3 else "Very High"
from collections import defaultdict
bt = defaultdict(lambda: [0, 0])
for r in rows:
    b = band(float(r["svi"]))
    bt[b][1] += 1
    if r["end_state"] == "ARRIVED": bt[b][0] += 1
order = ["Low", "Moderate", "High", "Very High"]
xs = list(range(1, 5))
rates, yerr_lo, yerr_hi, labels = [], [], [], []
for i, b in enumerate(order):
    e, n = bt[b]
    lo, hi = wilson(e, n)
    rates.append(100*e/n)
    yerr_lo.append(100*e/n - lo)
    yerr_hi.append(hi - 100*e/n)
    labels.append(f"{b}\n{e}/{n}")
fig, ax = plt.subplots(figsize=(8, 5.5))
ax.errorbar(xs, rates, yerr=[yerr_lo, yerr_hi], fmt="o", color="#1f77b4",
            markersize=10, capsize=6, linewidth=2)
for x, r in zip(xs, rates):
    ax.annotate(f"{r:.1f}%", (x, r), textcoords="offset points", xytext=(0, 14),
                ha="center", fontsize=11)
ax.set_xticks(xs)
ax.set_xticklabels(labels, fontsize=11)
ax.set_ylabel("Participants with at least one ARRIVED record (%)", fontsize=11)
ax.set_xlabel("Empirical participant-level SVI quartile", fontsize=12)
ax.set_title("Participant-level any-arrival completion by empirical SVI quartile\ncanonical run (153 participants); 95% Wilson intervals", fontsize=12)
ax.set_ylim(0, 30)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(f"{FIGDIR}/canonical_participant_quartiles.png", dpi=200)
plt.close(fig)
print("Fig 32 saved: canonical_participant_quartiles.png")
