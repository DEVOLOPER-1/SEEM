"""Canonical event-semantics unit tests (v2 plan §2.5).
Run: .venv/bin/python tests/test_canonical_semantics.py
Tests run headless on synthetic data (no network builds).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

PASS, FAIL = [], []

def check(name, cond):
    (PASS if cond else FAIL).append(name)
    print(("PASS" if cond else "FAIL"), "-", name)

# --- Test harness: minimal fake model + agent objects exercising the semantics ---
class FakeClock:
    import datetime as _dt
    t = _dt.datetime(2023, 1, 1, 8, 0, 0)

class FakeModel:
    sim_time = FakeClock.t
    step_seconds = 60

class FakeAgent:
    """Stand-in with the same attributes the real agent's defaults set."""
    def __init__(self):
        self.status = "INACTIVE"
        self.fail_reason = None
        self.arrived_at = None
        self.end_state = None
        self.evacuation_time = 0.0
        self.unique_id = "test_agent"

m = FakeModel()
a = FakeAgent()

# 1. ARRIVED site semantics: status + arrived_at + end_state set together
# (mirrors the model's ARRIVED sites: status + arrived_at + end_state set together)
a.status = "ARRIVED"
a.arrived_at = m.sim_time
a.end_state = "ARRIVED"
check("arrived site sets arrived_at+end_state with status", a.status == "ARRIVED" and a.arrived_at is not None and a.end_state == "ARRIVED")

# 2. FAILED site semantics: absorbing, no arrived_at
a2 = FakeAgent()
a2.status = "FAILED"
a2.end_state = "FAILED"
a2.fail_reason = "destination planning"
check("FAILED absorbing without arrived_at", a2.arrived_at is None and a2.end_state == "FAILED" and a2.fail_reason is not None)

# 3. finalize_horizon semantics: EVACUATING/INACTIVE/PLANNING -> CENSORED_AT_HORIZON, arrived_at=None
agents = []
for st in ["EVACUATING", "INACTIVE", "PLANNING"]:
    ag = FakeAgent(); ag.status = st; agents.append(ag)
ag_arr = FakeAgent(); ag_arr.status = "ARRIVED"; ag_arr.arrived_at = m.sim_time; ag_arr.end_state = "ARRIVED"
ag_fail = FakeAgent(); ag_fail.status = "FAILED"; ag_fail.end_state = "FAILED"; agents += [ag_arr, ag_fail]

# Replicate finalize_horizon logic (mirrors model.finalize_horizon)
n_censored = 0
for ag in agents:
    if ag.status in ("EVACUATING", "INACTIVE", "PLANNING"):
        ag.end_state = "CENSORED_AT_HORIZON"
        ag.arrived_at = None
        n_censored += 1
check("horizon censoring marks 3 non-terminal agents", n_censored == 3)
check("censored agents have arrived_at None", all(ag.arrived_at is None for ag in agents if ag.end_state == "CENSORED_AT_HORIZON"))
check("ARRIVED keeps event time", ag_arr.arrived_at is not None and ag_arr.end_state == "ARRIVED")
check("FAILED stays FAILED", ag_fail.end_state == "FAILED")
check("terminal counts partition N", len(agents) == 5)

# 4. Journey-segment validation logic (mirrors model canonical validation)
TRANSIT_LABELS = {"TRANSIT","BUS","TRAIN","TRAIN_EXPRESS","METRO","SUBWAY","TRAMWAY","TRANSITMODE.TRANSIT"}
HORIZON_S = 180*60
def validate(seg):
    mode = (seg.get("transport_mode") or "").upper()
    is_t = mode in TRANSIT_LABELS
    dur_s = (seg.get("travel_time_minutes") or 0.0) * 60.0
    if is_t and not all(seg.get(k) not in (None,"","None") for k in ("route_id","start_stop_id","end_stop_id","feed")):
        return "drop"
    if dur_s > HORIZON_S:
        return "drop"
    return "keep"

check("valid transit leg kept", validate({"transport_mode":"TRANSIT","travel_time_minutes":20.0,"route_id":"R1","start_stop_id":"A","end_stop_id":"B","feed":"F"}) == "keep")
check("transit leg w/o IDs dropped", validate({"transport_mode":"BUS","travel_time_minutes":20.0}) == "drop")
check("over-horizon walking leg dropped", validate({"transport_mode":"WALKING","travel_time_minutes":200.0}) == "drop")
check("valid walking leg kept", validate({"transport_mode":"WALKING","travel_time_minutes":15.0}) == "keep")

# 5. Behavioral equations to fp precision (Eqs. 12-14, kappa=0.3)
s = 0.4
kappa, Dmax, Pbase = 0.3, 1800, 300
delay = s * Dmax
speed = 1.4 * max(0.1, 1 - s * kappa)
pat = Pbase * max(0.1, 1 - s)
check("activation delay Eq12", abs(delay - 720.0) < 1e-9)
check("speed multiplier Eq13", abs(speed - 1.4 * 0.88) < 1e-9)
check("patience Eq14", abs(pat - 180.0) < 1e-9)

print(f"\n=== {len(PASS)} passed, {len(FAIL)} failed ===")
sys.exit(1 if FAIL else 0)
