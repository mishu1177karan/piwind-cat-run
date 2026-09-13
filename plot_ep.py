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
from pathlib import Path

import plotly.graph_objects as go

REPO_DIR = Path(__file__).resolve().parent

EPTYPE_OEP = 1
EPTYPE_AEP = 3

# One line per (peril, ep_type): (csv stem, EPType value, trace name, color, dash)
SERIES = [
    ("gul_S1", EPTYPE_OEP, "GUL OEP", "#2563eb", "solid"),
    ("gul_S1", EPTYPE_AEP, "GUL AEP", "#2563eb", "dash"),
    ("il_S1", EPTYPE_OEP, "IL OEP", "#b45309", "solid"),
    ("il_S1", EPTYPE_AEP, "IL AEP", "#b45309", "dash"),
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
    for stem, ep_type, name, color, dash in SERIES:
        csv_path = out_dir / f"{stem}_ept.csv"
        if not csv_path.exists():
            parser.error(f"missing {csv_path}")
        x, y = read_ept(csv_path, ep_type, args.ep_calc)
        if not x:
            print(f"warning: no rows for {name} (EPCalc={args.ep_calc}) in {csv_path}")
            continue
        fig.add_trace(go.Scatter(
            x=x, y=y, mode="lines+markers", name=name,
            line=dict(color=color, dash=dash, width=2),
            marker=dict(size=5),
        ))

    fig.update_layout(
        title=f"PiWind EP Curves — GUL vs IL, AEP vs OEP ({args.output_dir}, EPCalc={args.ep_calc})",
        xaxis=dict(title="Return period (years)", type="log"),
        yaxis=dict(title="Loss ($)", tickformat="$,.0f"),
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )

    out_path = REPO_DIR / "ep_curves.html"
    fig.write_html(out_path, include_plotlyjs="inline", full_html=True)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
