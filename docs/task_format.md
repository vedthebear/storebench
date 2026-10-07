# Task format and scoring

## `task.toml`

Each task is a single file with the following blocks:

- **`[task]`** — `id`, `title`, and `prompt` (the full operator instruction shown
  to the agent).
- **`[shift]`** — `horizon_days`, `window_hours` (the length of one operation
  window), `ops_per_window` (the tool-operation budget per window), `listing_cap`,
  and the `start` timestamp.
- **`[setup]`** — the opening-inventory configuration (e.g. `trim_stock_days`,
  `trim_stock_floor`).
- **`[economics]`** — task-specific overrides of the store's economics and
  platform terms (e.g. `starting_cash`, `deposit`, `return_escalate_days`).
- **`[competition]`** (optional) — scripted rival stores that compete for
  demand share.
- **`[[events]]`** — the scripted disruptions. Each event has a `kind`
  (e.g. `demand_multiplier`, `supply_shock_country`, `market_crash`,
  `quality_shift`), a fire time `at_days`, magnitude parameters, and an
  **information channel** determined by its fields:
  - default → **announced** (a platform alert names the change),
  - a `rumor` string → **rumored** (vague trade-press wording, no numbers),
  - `announce = false` → **silent** (the world changes; only the agent's own
    sales reveal it).

Simulated time is metered in operations: each tool call spends one operation, and
spending a window's last operation (or calling `end_window`) advances the world.
Time is therefore a pure function of the action sequence, independent of model or
harness latency.

## Trajectory artifacts

Each trajectory directory contains:

- **`score.json`** — the graded terminal ledger:
  - `business_raw` — net-asset growth over the shift.
  - `business` — `business_raw` normalized against calibration, clipped to [0, 1].
  - `on_time_rate`, `return_handled_rate` — the two service rates.
  - `reliability` — mean of the two service rates.
  - `continuity` — fraction of task windows the agent acted in.
  - `net_assets`, `windows_played`, `bankrupt`, `seed`.
  - `reward_composite` — the official composite score.
- **`summary.json`** — a redacted run summary (model identifier, turn count,
  termination class, aggregate metrics).

## Composite score

```
reward_composite = 0.7 * business + 0.2 * reliability + 0.1 * continuity
```

- **business** = `clip_[0,1]( (business_raw - zero) / scale )`, where `zero` and
  `scale` are the per-task-seed calibration constants. `zero` is the higher raw
  business result of the do-nothing and absentee anchors. `scale` is the gap
  from `zero` to the higher raw business result of rule-based and smart-triage,
  divided by 0.70 and rounded to two decimal places. This maps the better
  judgment anchor to approximately 0.70, leaving room for stronger policies.
- **reliability** = mean of `on_time_rate` and `return_handled_rate`.
- **continuity** = windows acted in / windows in the task (<= 1).

A trajectory **passes** if its composite clears the task-seed `threshold` in the
calibration file (comparison uses `>=`). `scoring/regrade.py` recomputes business,
reliability, the composite, and pass/fail from `score.json` and
`scoring/calibration.train.json`. It uses the supplied continuity value; the
underlying attendance records are not included.
