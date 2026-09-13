# PiWind Cat Run

Results from a local run of the [OasisLMF](https://github.com/OasisLMF/OasisLMF)
PiWind demo model (`oasislmf==2.5.7`), kept here for reference/write-up
purposes. See `RUNBOOK.md` for the full install/reproduction steps.

## The run

- **Model**: PiWind (toy UK windstorm model), perils WSS (storm surge) and
  WTC (tropical cyclone)
- **Portfolio**: 10 locations, $3,400,000 total insured value (TIV), all
  matched successfully to both perils
- **Event set**: 1,447 stochastic events, simulated across a 1,000-year
  catalog (`occurrence_lt.csv`), with 10 Monte Carlo damage samples per
  event
- **Command**: `oasislmf model run -C oasislmf.json` (config and analysis
  settings included in this repo)
- **Outputs**: `output/` — ground-up (`gul_S1_*`), insured/net (`il_S1_*`),
  and net-of-reinsurance (`ri_S1_*`) loss tables

## What the AEP/OEP numbers mean

The `*_ept.csv` files (Exceedance Probability Tables) hold both AEP and
OEP curves in one file, distinguished by two columns:

- **`EPType`**: `1` = OEP, `2` = OEP TVaR, `3` = AEP, `4` = AEP TVaR
- **`EPCalc`**: `1` = mean damage ratio (based on the 1,000 simulated
  years directly, max return period 1000), `2` = full uncertainty
  (treats each of the 10 damage samples per year as its own trial —
  10,000 effective trials — resolving return periods up to 5000),
  `3` = per-sample mean, `4` = mean sample

**OEP (Occurrence Exceedance Probability)**: for each simulated year, take
only the single worst event's loss (max, not sum), then rank all years.
Answers *"how bad can the single worst storm of the year get?"*

**AEP (Aggregate Exceedance Probability)**: for each simulated year, sum
every event's loss that occurred that year, then rank all years. Answers
*"how bad can the whole year's storm activity get, combined?"*

Because AEP sums (potentially) multiple events per year while OEP takes
just the max, AEP ≥ OEP at every return period for the same book. E.g. at
the 1-in-1000 return period, GUL OEP = $3.4M (the worst single event maxes
out the portfolio) while GUL AEP = $6.48M (the worst *year* had more than
one damaging event).

## Other output files

- `_melt`/`_selt`/`_qelt`: event loss tables (moment / sample / quantile)
- `_mplt`/`_splt`/`_qplt`: period loss tables (moment / sample / quantile)
- `_palt`: per-sample portfolio loss (mean/SD loss across the 10 samples)
- `_psept`: per-sample EP table
- `_summary-info.csv`: summary-level mapping metadata
