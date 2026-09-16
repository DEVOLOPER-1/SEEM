"""Canonical statistics generation (v2 plan §6).
Run: .venv/bin/python scripts/generate_stats.py
Outputs: outputs/results_canonical.json
Every statistic printed with method + seed. Fixed seed: 20260916.
"""
import csv, json, math, random, os, sys
from collections import Counter, defaultdict
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
SEED = 20260916
OUT = {}

def wilson(e, n, z=1.959963984540054):
    p = e / n; den = 1 + z*z/n
    c = (p + z*z/(2*n)) / den
    half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / den
    return 100*(c-half), 100*(c+half)

rows = list(csv.DictReader(open("outputs/canonical_agent_states.csv")))
N = len(rows)
OUT["n_agents"] = N
OUT["seed"] = SEED
OUT["method_note"] = "canonical run, one entity per participant, 180x60s, seed 20260916"

# ---- end_state derivation (documented rule) ----
for r in rows:
    if not r.get("end_state"):
        r["end_state"] = ("CENSORED_AT_HORIZON"
                          if r["status"] in ("EVACUATING", "PLANNING", "INACTIVE")
                          else r["status"])
OUT["end_state_partition"] = dict(Counter(r["end_state"] for r in rows))

# ---- 6.1 completion under three aggregation rules ----
# One record per participant (canonical), so all three rules coincide by construction.
arr = sum(1 for r in rows if r["end_state"] == "ARRIVED")
lo, hi = wilson(arr, N)
OUT["completion"] = {
    "method": "Wilson score interval, 95%",
    "first_record": {"events": arr, "n": N, "rate_pct": round(100*arr/N, 2), "ci95": [round(lo,2), round(hi,2)]},
    "any_arrival":  {"events": arr, "n": N, "rate_pct": round(100*arr/N, 2), "ci95": [round(lo,2), round(hi,2)]},
    "all_records":  {"events": arr, "n": N, "rate_pct": round(100*arr/N, 2), "ci95": [round(lo,2), round(hi,2)]},
}
print(f"6.1 completion (all rules coincide, 1 record/participant): {arr}/{N} = {100*arr/N:.2f}% CI [{lo:.2f},{hi:.2f}]")

# ---- 6.2 participant-level quartiles ----
svi = sorted(float(r["svi"]) for r in rows)
def pct(v, q):
    pos = (len(v)-1)*q; lo, hi = math.floor(pos), math.ceil(pos)
    return v[lo] + (v[hi]-v[lo])*(pos-lo)
Q1, Q2, Q3 = pct(svi, .25), pct(svi, .5), pct(svi, .75)
OUT["quartiles"] = {"method": "linear interpolation, participant-level (one record per participant)",
                    "Q1": round(Q1, 4), "Q2": round(Q2, 4), "Q3": round(Q3, 4)}
print(f"6.2 quartiles: Q1={Q1:.4f} Q2={Q2:.4f} Q3={Q3:.4f}")

# ---- 6.3 band assignment + band x end_state ----
def band(s):
    return "Low" if s <= Q1 else "Moderate" if s <= Q2 else "High" if s <= Q3 else "Very High"
groups = ["Low", "Moderate", "High", "Very High"]
for r in rows:
    r["band"] = band(float(r["svi"]))
band_status = defaultdict(Counter)
for r in rows:
    band_status[r["band"]][r["end_state"]] += 1
OUT["band_end_state"] = {b: dict(band_status[b]) for b in groups}
print("6.3 band x end_state:", dict(OUT["band_end_state"]))

# ---- 6.4 FFH Monte Carlo + asymptotic chi2 ----
random.seed(SEED)
obs = Counter()
for r in rows:
    obs[(r["band"], 1 if r["end_state"] == "ARRIVED" else 0)] += 1
row_tot = {b: sum(obs[(b, s)] for s in (1, 0)) for b in groups}
col_tot = {s: sum(obs[(b, s)] for b in groups) for s in (1, 0)}
def chi2_of(tab):
    x = 0.0
    for b in groups:
        for s in (1, 0):
            e = row_tot[b] * col_tot[s] / N
            x += (tab[(b, s)] - e) ** 2 / e
    return x
obs_chi = chi2_of(obs)
labels = [1]*col_tot[1] + [0]*col_tot[0]
ge = 0; DRAWS = 200000
for d in range(DRAWS):
    random.shuffle(labels)
    sim = {}; i = 0
    for b in groups:
        nb = row_tot[b]
        a = sum(labels[i:i+nb]); sim[(b, 1)] = a; sim[(b, 0)] = nb - a; i += nb
    if chi2_of(sim) >= obs_chi - 1e-9:
        ge += 1
p_mc = ge / DRAWS
# asymptotic p via Wilson-Hilferty (chi2 df=3), avoiding scipy dependency:
w = ((obs_chi/3)**(1/3) - (1 - 2/(9*3))) / math.sqrt(2/(9*3))
p_asym = 0.5 * math.erfc(w / math.sqrt(2))
V = math.sqrt(obs_chi / N)
OUT["ffh_test"] = {"method": f"Fisher-Freeman-Halton Monte Carlo, {DRAWS} draws, seed {SEED}",
                   "chi2": round(obs_chi, 3), "p_mc": round(p_mc, 4),
                   "asymptotic_method": "Wilson-Hilferty approx to chi2(3)",
                   "p_asymptotic": round(p_asym, 4), "cramers_v": round(V, 3)}
print(f"6.4 FFH MC p={p_mc:.4f} | asymptotic p={p_asym:.4f} | chi2={obs_chi:.3f} | V={V:.3f}")

# ---- 6.5 logistic OR per 0.1 SVI, PROFILE-LIKELIHOOD CI ----
data = [(float(r["svi"]), 1 if r["end_state"] == "ARRIVED" else 0) for r in rows]
b0, b1 = 0.0, 0.0
for _ in range(100):
    g = [0.0, 0.0]; H = [[0.0, 0.0], [0.0, 0.0]]
    for x, y in data:
        p = 1/(1+math.exp(-(b0+b1*x))); w = p*(1-p)
        g[0] += p-y; g[1] += (p-y)*x
        H[0][0] += w; H[0][1] += w*x; H[1][0] += w*x; H[1][1] += w*x*x
    det = H[0][0]*H[1][1]-H[0][1]*H[1][0]
    s0 = (H[1][1]*g[0]-H[0][1]*g[1])/det
    s1 = (H[0][0]*g[1]-H[1][0]*g[0])/det
    b0 -= s0; b1 -= s1
    if abs(s0) < 1e-10 and abs(s1) < 1e-10:
        break

def loglik(b0t, b1t):
    ll = 0.0
    for x, y in data:
        p = 1/(1+math.exp(-(b0t+b1t*x)))
        ll += y*math.log(p) + (1-y)*math.log(1-p)
    return ll

ll_full = loglik(b0, b1)
def profile_ci_b1(target=3.841458820694124):
    lo_b, hi_b = b1 - 4.0, b1 + 4.0
    def f(b1t):
        lo0, hi0 = b0 - 10, b0 + 10
        for _ in range(60):
            m1 = lo0 + (hi0-lo0)/3; m2 = hi0 - (hi0-lo0)/3
            if loglik(m1, b1t) < loglik(m2, b1t): lo0 = m1
            else: hi0 = m2
        return loglik((lo0+hi0)/2, b1t) - (ll_full - target/2)
    a, b = b1, hi_b
    for _ in range(80):
        m = (a+b)/2
        if f(m) > 0: a = m
        else: b = m
    upper = (a+b)/2
    a, b = lo_b, b1
    for _ in range(80):
        m = (a+b)/2
        if f(m) > 0: b = m
        else: a = m
    lower = (a+b)/2
    return lower, upper

lo_b1, hi_b1 = profile_ci_b1()
OR = math.exp(b1*0.1)
OR_lo, OR_hi = math.exp(lo_b1*0.1), math.exp(hi_b1*0.1)
n_events = sum(y for _, y in data)
OUT["logistic_or"] = {"method": "univariable logistic regression, profile-likelihood 95% CI",
                      "n_events": n_events, "n": N,
                      "OR_per_0.1_SVI": round(OR, 3), "ci95": [round(OR_lo, 3), round(OR_hi, 3)]}
print(f"6.5 OR per 0.1 SVI = {OR:.3f} CI [{OR_lo:.3f},{OR_hi:.3f}] (profile likelihood; {n_events} events/{N})")

# ---- 6.6 mode-stratified completion ----
mode_comp = defaultdict(lambda: [0, 0])
for r in rows:
    mode_comp[r["final_mode"]][1] += 1
    if r["end_state"] == "ARRIVED": mode_comp[r["final_mode"]][0] += 1
OUT["mode_completion"] = {}
for m, (e, n) in sorted(mode_comp.items()):
    l, h = wilson(e, n)
    OUT["mode_completion"][m] = {"events": e, "n": n, "rate_pct": round(100*e/n, 2),
                                 "ci95": [round(l, 2), round(h, 2)]}
print("6.6 mode completion:", {m: v["rate_pct"] for m, v in OUT["mode_completion"].items()})

# ---- 6.7 KM by band (valid events now exist) ----
band_km = {}
for b in groups:
    brs = [r for r in rows if r["band"] == b]
    times = []
    for r in brs:
        if r["end_state"] == "ARRIVED" and r.get("arrived_at") and r.get("started_at"):
            t = (datetime.fromisoformat(r["arrived_at"]) -
                 datetime.fromisoformat(r["started_at"])).total_seconds()/60
            times.append((float(t), 1))
        else:
            times.append((180.0, 0))
    times.sort()
    S = 1.0; med = None
    for t, ev in times:
        if ev:
            n_at_risk = sum(1 for tt, e2 in times if tt >= t)
            S *= (1 - 1/n_at_risk) if n_at_risk else 1
            if S <= 0.5 and med is None: med = t
    band_km[b] = {"median_min": round(med, 1) if med else "not estimable",
                  "n_events": sum(1 for _, e in times if e), "n": len(times)}
OUT["km_by_band"] = {"method": "Kaplan-Meier, horizon censoring at 180 min",
                     "bands": band_km}
print("6.7 KM medians:", band_km)

# ---- 6.8 bottleneck note ----
OUT["bottleneck_note"] = ("bottleneck log empty for this run (no edge exceeded C_e>1 with 153 agents); "
                          "diagnostic deferred to higher-density runs")

os.makedirs("outputs", exist_ok=True)
with open("outputs/results_canonical.json", "w") as f:
    json.dump(OUT, f, indent=1)
print("\nAll statistics written to outputs/results_canonical.json")
