#!/usr/bin/env python3
"""Reproduce each released trajectory's official composite score from its exported
ledger, using only the released scorer and the per-task-seed calibration
constants --- no simulation environment required.

This demonstrates the paper's determinism/audit claim at the scoring layer: given
a trajectory's terminal ledger and the task-seed calibration, the graded score is
fully reproducible.

Usage:
    python3 regrade.py [path/to/trajectories]

Exit code 0 iff every trajectory reproduces.
"""
import json
import glob
import os
import sys

from composite import composite, business_from_ledger, reliability_from_rates

HERE = os.path.dirname(os.path.abspath(__file__))
CAL = json.load(open(os.path.join(HERE, "calibration.train.json")))["tasks"]


def regrade(tdir):
    score = json.load(open(os.path.join(tdir, "score.json")))
    task = os.path.basename(tdir).split("__")[0]
    seed = str(int(score["seed"]))
    c = CAL[task][seed]

    # Recompute the business term from the raw net-asset growth + calibration,
    # then the composite from all three components.
    biz = business_from_ledger(score["business_raw"], c["business_zero_raw"], c["business_scale"])
    rel = reliability_from_rates(score.get("on_time_rate"), score.get("return_handled_rate"))
    comp = composite(biz, rel, score["continuity"])
    passed = comp >= c["threshold"]

    biz_ok = abs(biz - score["business"]) < 1e-3
    comp_ok = abs(comp - score["reward_composite"]) < 1e-3
    return round(comp, 4), score["reward_composite"], passed, (biz_ok and comp_ok)


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "trajectories")
    dirs = [d.rstrip("/") for d in sorted(glob.glob(os.path.join(root, "*", "")))
            if os.path.exists(os.path.join(d, "score.json"))]
    ok = 0
    print(f"{'trajectory':36}{'recomputed':>11}{'stored':>9}{'pass':>6}  check")
    for d in dirs:
        recomp, stored, passed, match = regrade(d)
        ok += match
        print(f"{os.path.basename(d):36}{recomp:>11.4f}{stored:>9.4f}{'  Y' if passed else '  N':>6}"
              f"  {'OK' if match else 'MISMATCH'}")
    print(f"\n{ok}/{len(dirs)} trajectories reproduced from ledger + calibration.")
    sys.exit(0 if ok == len(dirs) else 1)


if __name__ == "__main__":
    main()
