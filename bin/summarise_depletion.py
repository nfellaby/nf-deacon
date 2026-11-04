#!/usr/bin/env python3
"""Summarise Deacon depletion results across samples into TSV tables and an HTML report.

Inputs
------
--manifest     Header-less TSV: sample, platform, layout, summary JSON filename
--summary-dir  Directory containing the Deacon --summary JSON files

Outputs
-------
<outprefix>.tsv              one row per sample and platform
<outprefix>_by_platform.tsv  totals per platform
<outprefix>.html             self-contained report
"""

import argparse
import csv
import datetime
import html
import json
import sys
from pathlib import Path

SAMPLE_COLUMNS = [
    "sample",
    "platform",
    "layout",
    "reads_in",
    "reads_removed",
    "reads_retained",
    "reads_removed_pct",
    "bp_in",
    "bp_removed",
    "bp_retained",
    "bp_removed_pct",
    "time_s",
]

PLATFORM_COLUMNS = [
    "platform",
    "samples",
    "reads_in",
    "reads_removed",
    "reads_retained",
    "reads_removed_pct",
    "min_sample_removed_pct",
    "bp_in",
    "bp_removed",
    "bp_retained",
    "bp_removed_pct",
]


def pct(part, whole):
    return 100.0 * part / whole if whole else 0.0


def read_manifest(path):
    rows = []
    with open(path, newline="") as handle:
        for line in handle:
            line = line.rstrip("\r\n")
            if not line:
                continue
            fields = line.split("\t")
            if len(fields) != 4:
                sys.exit(f"Malformed manifest line (expected 4 fields): {line!r}")
            rows.append(dict(zip(["sample", "platform", "layout", "summary"], fields)))
    if not rows:
        sys.exit("Manifest is empty: no Deacon summaries to report")
    return rows


def load_results(manifest, summary_dir):
    results = []
    run_info = None
    for entry in manifest:
        with open(Path(summary_dir) / entry["summary"]) as handle:
            summary = json.load(handle)
        if run_info is None:
            run_info = {
                key: summary.get(key)
                for key in ("version", "index", "k", "w", "abs_threshold", "rel_threshold", "prefix_length")
            }
        reads_in = summary["seqs_in"]
        reads_removed = summary["seqs_removed"]
        bp_in = summary["bp_in"]
        bp_removed = summary["bp_removed"]
        results.append(
            {
                "sample": entry["sample"],
                "platform": entry["platform"],
                "layout": entry["layout"],
                "reads_in": reads_in,
                "reads_removed": reads_removed,
                "reads_retained": summary["seqs_out"],
                "reads_removed_pct": pct(reads_removed, reads_in),
                "bp_in": bp_in,
                "bp_removed": bp_removed,
                "bp_retained": summary["bp_out"],
                "bp_removed_pct": pct(bp_removed, bp_in),
                "time_s": summary.get("time", 0.0),
            }
        )
    results.sort(key=lambda r: (r["platform"], r["sample"]))
    return results, run_info


def platform_totals(results):
    totals = []
    for platform in sorted({r["platform"] for r in results}):
        rows = [r for r in results if r["platform"] == platform]
        reads_in = sum(r["reads_in"] for r in rows)
        reads_removed = sum(r["reads_removed"] for r in rows)
        bp_in = sum(r["bp_in"] for r in rows)
        bp_removed = sum(r["bp_removed"] for r in rows)
        totals.append(
            {
                "platform": platform,
                "samples": len(rows),
                "reads_in": reads_in,
                "reads_removed": reads_removed,
                "reads_retained": sum(r["reads_retained"] for r in rows),
                "reads_removed_pct": pct(reads_removed, reads_in),
                "min_sample_removed_pct": min(r["reads_removed_pct"] for r in rows),
                "bp_in": bp_in,
                "bp_removed": bp_removed,
                "bp_retained": sum(r["bp_retained"] for r in rows),
                "bp_removed_pct": pct(bp_removed, bp_in),
            }
        )
    return totals


def write_tsv(path, columns, rows):
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {key: (f"{value:.4f}" if isinstance(value, float) else value) for key, value in row.items()}
            )


def fmt_int(value):
    return f"{value:,}"


def fmt_pct(value):
    return f"{value:.3f}%"


def bar(value):
    width = max(0.0, min(100.0, value))
    return f'<div class="bar"><span style="width:{width:.2f}%"></span></div>'


def render_html(results, totals, run_info):
    esc = html.escape
    generated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    cards = "\n".join(
        f"""
      <div class="card">
        <h3>{esc(t['platform'].upper())}</h3>
        <p class="big">{fmt_pct(t['reads_removed_pct'])}</p>
        <p>reads removed across {t['samples']} sample{'s' if t['samples'] != 1 else ''}</p>
        <p class="muted">{fmt_int(t['reads_retained'])} of {fmt_int(t['reads_in'])} reads retained
        · lowest sample {fmt_pct(t['min_sample_removed_pct'])}</p>
      </div>"""
        for t in totals
    )

    rows = "\n".join(
        f"""
        <tr>
          <td>{esc(r['sample'])}</td>
          <td>{esc(r['platform'])}</td>
          <td>{esc(r['layout'])}</td>
          <td class="num">{fmt_int(r['reads_in'])}</td>
          <td class="num">{fmt_int(r['reads_removed'])}</td>
          <td class="num">{fmt_int(r['reads_retained'])}</td>
          <td class="num">{fmt_pct(r['reads_removed_pct'])}</td>
          <td class="barcell">{bar(r['reads_removed_pct'])}</td>
          <td class="num">{fmt_pct(r['bp_removed_pct'])}</td>
        </tr>"""
        for r in results
    )

    params = run_info or {}
    param_items = "".join(
        f"<li><b>{esc(label)}</b> {esc(str(params.get(key)))}</li>"
        for label, key in [
            ("Deacon", "version"),
            ("Index", "index"),
            ("k", "k"),
            ("w", "w"),
            ("Absolute threshold", "abs_threshold"),
            ("Relative threshold", "rel_threshold"),
            ("Prefix length", "prefix_length"),
        ]
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Deacon depletion summary</title>
<style>
  :root {{
    --bg: #ffffff; --fg: #1d1d1f; --muted: #6b6b70; --line: #e3e3e6;
    --card: #f6f6f8; --accent: #2f6fbf; --track: #e6ebf2;
    color-scheme: light;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #17181a; --fg: #ececee; --muted: #9a9aa1; --line: #2c2d31;
      --card: #202125; --accent: #6aa3ea; --track: #2b3240;
      color-scheme: dark;
    }}
  }}
  body {{ margin: 0; background: var(--bg); color: var(--fg);
         font: 15px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }}
  main {{ max-width: 1100px; margin: 0 auto; padding: 2rem 1.25rem 3rem; }}
  h1 {{ font-size: 1.6rem; margin: 0 0 .25rem; }}
  h2 {{ font-size: 1.15rem; margin: 2rem 0 .75rem; }}
  h3 {{ margin: 0; font-size: .85rem; letter-spacing: .06em; color: var(--muted); }}
  .muted {{ color: var(--muted); font-size: .9rem; }}
  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; }}
  .card {{ background: var(--card); border-radius: 10px; padding: 1rem 1.25rem; }}
  .card p {{ margin: .2rem 0; }}
  .big {{ font-size: 2rem; font-weight: 650; }}
  .scroll {{ overflow-x: auto; }}
  table {{ border-collapse: collapse; width: 100%; font-size: .92rem; }}
  th, td {{ padding: .45rem .6rem; border-bottom: 1px solid var(--line); text-align: left; white-space: nowrap; }}
  th {{ font-weight: 600; color: var(--muted); }}
  .num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .barcell {{ width: 22%; min-width: 120px; }}
  .bar {{ background: var(--track); border-radius: 4px; height: 10px; overflow: hidden; }}
  .bar span {{ display: block; height: 100%; background: var(--accent); }}
  ul.params {{ list-style: none; padding: 0; display: flex; flex-wrap: wrap; gap: .4rem 1.5rem; }}
  .note {{ font-size: .88rem; color: var(--muted); max-width: 75ch; }}
</style>
</head>
<body>
<main>
  <h1>Deacon depletion summary</h1>
  <p class="muted">Generated {generated} · {len(results)} sample/platform combinations</p>

  <h2>By platform</h2>
  <div class="cards">{cards}
  </div>

  <h2>By sample</h2>
  <div class="scroll">
    <table>
      <thead>
        <tr>
          <th>Sample</th><th>Platform</th><th>Layout</th>
          <th class="num">Reads in</th><th class="num">Removed</th><th class="num">Retained</th>
          <th class="num">Removed (reads)</th><th></th><th class="num">Removed (bp)</th>
        </tr>
      </thead>
      <tbody>{rows}
      </tbody>
    </table>
  </div>

  <h2>Run parameters</h2>
  <ul class="params">{param_items}</ul>

  <p class="note">Read counts for paired-end data count each mate separately, so a pair contributes two
  reads. Deacon classifies pairs jointly, so both mates are always removed or retained together. Input reads
  are simulated from human assemblies, so every retained read is a human read the index failed to remove.</p>
</main>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest", required=True, help="TSV: sample, platform, layout, summary JSON filename")
    parser.add_argument("--summary-dir", default=".", help="Directory containing Deacon summary JSONs")
    parser.add_argument("--outprefix", default="depletion_summary", help="Prefix for output files")
    args = parser.parse_args()

    manifest = read_manifest(args.manifest)
    results, run_info = load_results(manifest, args.summary_dir)
    totals = platform_totals(results)

    write_tsv(f"{args.outprefix}.tsv", SAMPLE_COLUMNS, results)
    write_tsv(f"{args.outprefix}_by_platform.tsv", PLATFORM_COLUMNS, totals)
    Path(f"{args.outprefix}.html").write_text(render_html(results, totals, run_info))


if __name__ == "__main__":
    main()
