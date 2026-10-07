"""Standalone StoreBench composite scorer.

The composite score is a pure function of a graded terminal ledger, so it can be
recomputed without the simulation environment. This module contains the entire
scoring definition used in the paper.

    composite = 0.7 * business + 0.2 * reliability + 0.1 * continuity

  - business:    normalized net-asset growth, clipped to [0, 1], scaled by the
                 per-task-seed calibration constants (zero, scale).
  - reliability: mean of the on-time shipment rate and the return-handled rate.
  - continuity:  fraction of task windows in which the agent acted (<= 1).
"""


def composite(business, reliability, continuity):
    """The weighted composite. Continuity is clipped at 1.0 by definition."""
    return 0.7 * business + 0.2 * reliability + 0.1 * min(1.0, continuity)


def business_from_ledger(business_raw, zero, scale):
    """Normalized business term from raw net-asset growth and the task-seed
    calibration constants: `zero` is the higher raw business result of the
    do-nothing and absentee anchors. `scale` is the gap from `zero` to the
    higher raw business result of rule-based and smart-triage, divided by 0.70
    (rounded to two decimal places). This maps the better judgment anchor to
    approximately 0.70. The normalized business term is clipped to [0, 1]."""
    return max(0.0, min(1.0, (business_raw - zero) / scale))


def reliability_from_rates(on_time_rate, return_handled_rate):
    """Mean of the two service rates, ignoring any that are undefined (no
    shipments or no returns in the episode)."""
    rates = [r for r in (on_time_rate, return_handled_rate) if r is not None]
    return sum(rates) / len(rates) if rates else 0.0
