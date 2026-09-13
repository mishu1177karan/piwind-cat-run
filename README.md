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
- **Outputs**: `output-10samples/` — ground-up (`gul_S1_*`), insured/net
  (`il_S1_*`), and net-of-reinsurance (`ri_S1_*`) loss tables, from the
  default 10-damage-sample run. `output-1000samples/` holds the same run
  repeated with `number_of_samples: 1000` (see `analysis_settings_1000samples.json`
  and the sampling convergence section below)

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

## Sampling convergence: 10 vs 1000 samples

`analysis_settings_1000samples.json` is the same analysis settings with
`number_of_samples` raised from 10 to 1000, run into `output-1000samples/`.
Comparing the GUL OEP curve (full-uncertainty, `EPCalc=2`) between the two
runs at the standard return periods (`comparison/gul_oep_10_vs_1000samples.csv`):

| Return Period | OEP, 10 samples | OEP, 1000 samples | % diff |
|---:|---:|---:|---:|
| 10  | $689,655  | $696,467  | +0.99% |
| 25  | $1,451,253 | $1,495,937 | +3.08% |
| 50  | $2,549,346 | $2,580,060 | +1.20% |
| 100 | $3,385,139 | $3,385,008 | -0.00% |
| 200 | $3,400,000 | $3,400,000 | 0.00% |
| 250 | $3,400,000 | $3,400,000 | 0.00% |

**What this means for tail estimates.** The `EPCalc=2` OEP curve treats each
damage sample as its own independent trial, so 10 samples × 1,000 simulated
years gives 10,000 trials, while 1000 samples gives 1,000,000. More trials
means the tail of the loss distribution — the region these return periods
are drawn from — is resolved with less Monte Carlo noise: with only 10
samples, a single unlucky/lucky draw at a given location can shift an
estimated return-period loss by a few percent purely by chance, not because
the underlying risk changed. That's exactly the pattern above: the biggest
differences (+3.08% at RP 25, +1.20% at RP 50) sit in the *mid* curve, where
loss varies continuously between "no damage" and "capped at TIV" and so is
most sensitive to how well the 10-sample run happened to cover that range.

At RP 100 and above, both runs converge to the same number (essentially
$3.4M — the full portfolio TIV) because at that severity the model is
saturated: enough locations are being maxed out that the number of damage
samples barely matters, there's no more variance left for extra samples to
resolve. In general, low-severity/high-frequency parts of a loss curve
converge fast (they're built from many observations), while rare/extreme
outcomes converge slowly and need more samples (or more simulated years) to
pin down with confidence — the classic Monte Carlo tradeoff between runtime
and tail precision. A 10-sample PiWind run is fine for a quick smoke test;
a real capital or pricing decision resting on a specific return-period
number should use enough samples (and/or enough simulated years) that
re-running with more of either doesn't move the answer.

## EP curve viewer

`ep_viewer.html` is a self-contained, offline viewer — open it directly in
a browser (`file://.../ep_viewer.html`, no server needed). Drag in one or
more `*_ept.csv` files (e.g. both `gul_S1_ept.csv` from
`output-10samples/` and `output-1000samples/`), pick the exceedance type
(OEP/AEP) and calculation basis, and it plots the loss-vs-return-period
curve with a hover tooltip and a table of exact values. Loading exactly
two files adds a "% diff" column to that table, reproducing the
sampling-convergence comparison above for any pair of runs. Nothing is
uploaded anywhere — files are parsed entirely client-side.

## Other output files

- `_melt`/`_selt`/`_qelt`: event loss tables (moment / sample / quantile)
- `_mplt`/`_splt`/`_qplt`: period loss tables (moment / sample / quantile)
- `_palt`: per-sample portfolio loss (mean/SD loss across the 10 samples)
- `_psept`: per-sample EP table
- `_summary-info.csv`: summary-level mapping metadata
