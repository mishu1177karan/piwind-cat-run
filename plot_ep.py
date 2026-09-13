#!/usr/bin/env python3
"""
Build a self-contained EP curve chart (GUL + IL, AEP + OEP overlaid) from
this repo's PiWind run output.

Note: this run's oasislmf pipeline (gulmc:true -> the Python "lecpy" tool,
see RUNBOOK.md) writes combined *_ept.csv files with AEP and OEP rows in
one file (distinguished by the EPType column), not separate _aep/_oep
files. This script reads gul_S1_ept.csv and il_S1_ept.csv from
output-10samples/ and splits them into AEP/OEP series internally.

Usage:
    python3 plot_ep.py [--output-dir output-10samples] [--ep-calc 2]

Writes ep_curves.html next to this script, with plotly.js inlined
(include_plotlyjs='inline') so the page works fully offline.
"""

import argparse
import csv
import json
from pathlib import Path

import plotly.graph_objects as go

REPO_DIR = Path(__file__).resolve().parent

EPTYPE_OEP = 1
EPTYPE_AEP = 3

TABLE_RETURN_PERIODS = [10, 25, 50, 100, 200, 250, 500]

# Portfolio facts fixed by the PiWind exposure itself (same across both
# sample-count runs). Not derivable from this repo's output CSVs — sourced
# from exposure_summary_report.json / model_settings.json in the original
# OasisPiWind run, see RUNBOOK.md.
PORTFOLIO_TIV = 3_400_000
EVENT_COUNT = 1_447

# One line per (peril, ep_type): (csv stem, EPType value, trace name, color, dash)
SERIES = [
    ("gul_S1", EPTYPE_OEP, "GUL OEP (per-occurrence)", "#2563eb", "solid"),
    ("gul_S1", EPTYPE_AEP, "GUL AEP (aggregate annual)", "#2563eb", "dash"),
    ("il_S1", EPTYPE_OEP, "IL OEP (per-occurrence)", "#b45309", "solid"),
    ("il_S1", EPTYPE_AEP, "IL AEP (aggregate annual)", "#b45309", "dash"),
]


def read_ept(path: Path, ep_type: int, ep_calc: int):
    """Return (return_periods, losses) sorted by descending return period."""
    rows = []
    with path.open() as f:
        for row in csv.DictReader(f):
            if int(row["EPType"]) == ep_type and int(row["EPCalc"]) == ep_calc:
                rows.append((float(row["ReturnPeriod"]), float(row["Loss"])))
    rows.sort(key=lambda r: -r[0])
    return [r[0] for r in rows], [r[1] for r in rows]


def fmt_money(v: float) -> str:
    return f"${v:,.0f}"


def count_samples(out_dir: Path) -> int:
    """Derive the actual number of damage samples used from the data
    itself (distinct SampleId in the per-sample EP table), rather than
    trusting a config file to match what was actually run."""
    psept_path = out_dir / "gul_S1_psept.csv"
    with psept_path.open() as f:
        return len({row["SampleId"] for row in csv.DictReader(f)})


def read_model_info() -> dict:
    settings_path = REPO_DIR / "analysis_settings.json"
    with settings_path.open() as f:
        d = json.load(f)
    return {
        "model_name_id": d.get("model_name_id", "?"),
        "model_supplier_id": d.get("model_supplier_id", "?"),
    }


def build_header_html(out_dir: Path) -> str:
    model = read_model_info()
    samples = count_samples(out_dir)
    return f"""
<style>
  .run-header {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    max-width: 900px; margin: 0 auto; padding: 12px 16px; margin-bottom: 8px;
    background: #f7f7f5; border: 1px solid #e2e0db; border-radius: 8px;
    font-size: 13px; color: #2a2825; display: flex; flex-wrap: wrap; gap: 4px 24px;
  }}
  .run-header b {{ color: #6b6862; font-weight: 600; margin-right: 4px; }}
</style>
<div class="run-header">
  <span><b>Model:</b> {model['model_name_id']} ({model['model_supplier_id']})</span>
  <span><b>Portfolio TIV:</b> {fmt_money(PORTFOLIO_TIV)}</span>
  <span><b>Events:</b> {EVENT_COUNT:,}</span>
  <span><b>Samples used ({out_dir.name}):</b> {samples:,}</span>
</div>
"""


def build_table_html(series_points: list) -> str:
    """series_points: list of (name, {return_period: loss}) in display order."""
    header_cells = "".join(f"<th>{name}</th>" for name, _ in series_points)
    thead = f"<thead><tr><th>Return Period</th>{header_cells}</tr></thead>"

    body_rows = []
    for rp in TABLE_RETURN_PERIODS:
        cells = ""
        for _, by_rp in series_points:
            loss = by_rp.get(rp)
            cells += f"<td>{fmt_money(loss) if loss is not None else '&mdash;'}</td>"
        body_rows.append(f"<tr><td>{rp}</td>{cells}</tr>")
    tbody = f"<tbody>{''.join(body_rows)}</tbody>"

    return f"""
<style>
  .ep-table-wrap {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; max-width: 900px; margin: 24px auto 0; }}
  .ep-table-wrap h2 {{ font-size: 16px; color: #2a2825; margin: 0 0 6px; }}
  .ep-table-wrap p.legend-note {{ font-size: 12.5px; color: #6b6862; margin: 0 0 14px; }}
  .ep-table-wrap table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  .ep-table-wrap th, .ep-table-wrap td {{ text-align: right; padding: 7px 10px; border-bottom: 1px solid #e2e0db; }}
  .ep-table-wrap th:first-child, .ep-table-wrap td:first-child {{ text-align: left; }}
  .ep-table-wrap th {{ color: #6b6862; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: .02em; }}
  .ep-table-wrap tbody tr:hover {{ background: #f7f7f5; }}
</style>
<div class="ep-table-wrap">
  <h2>Losses at standard return periods</h2>
  <p class="legend-note">
    <b>OEP</b> (Occurrence Exceedance Probability, per-occurrence) &mdash;
    loss from the single worst event in a year.
    <b>AEP</b> (Aggregate Exceedance Probability, aggregate annual) &mdash;
    summed loss from every event in a year. AEP &ge; OEP at every return period.
  </p>
  <table>{thead}{tbody}</table>
</div>
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", default="output-10samples",
        help="Run output folder (relative to this script) containing "
             "gul_S1_ept.csv / il_S1_ept.csv. Default: output-10samples",
    )
    parser.add_argument(
        "--ep-calc", type=int, default=2,
        help="EPCalc to plot: 1=mean damage ratio, 2=full uncertainty "
             "(default), 3=per-sample mean, 4=mean sample.",
    )
    args = parser.parse_args()

    out_dir = REPO_DIR / args.output_dir
    if not out_dir.is_dir():
        parser.error(f"output dir not found: {out_dir}")

    fig = go.Figure()
    series_points = []
    for stem, ep_type, name, color, dash in SERIES:
        csv_path = out_dir / f"{stem}_ept.csv"
        if not csv_path.exists():
            parser.error(f"missing {csv_path}")
        x, y = read_ept(csv_path, ep_type, args.ep_calc)
        if not x:
            print(f"warning: no rows for {name} (EPCalc={args.ep_calc}) in {csv_path}")
            series_points.append((name, {}))
            continue
        fig.add_trace(go.Scatter(
            x=x, y=y, mode="lines+markers", name=name,
            line=dict(color=color, dash=dash, width=2),
            marker=dict(size=5),
        ))
        series_points.append((name, dict(zip(x, y))))

    fig.update_layout(
        title=f"PiWind EP Curves — GUL vs IL, AEP vs OEP ({args.output_dir}, EPCalc={args.ep_calc})",
        xaxis=dict(title="Return period (years)", type="log"),
        yaxis=dict(title="Loss ($)", tickformat="$,.0f"),
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )

    header_html = build_header_html(out_dir)
    chart_html = fig.to_html(include_plotlyjs="inline", full_html=False)
    table_html = build_table_html(series_points)

    out_path = REPO_DIR / "ep_curves.html"
    out_path.write_text(
        f"<!doctype html>\n<html><head><meta charset='utf-8'></head>"
        f"<body>{header_html}{chart_html}{table_html}</body></html>"
    )
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
