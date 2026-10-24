"""Make the report figures and summary table from the benchmark CSVs (seaborn).

Reads results/results_*.csv (n = 10^7 rows from results_10M_sequential.csv
replace the parallel run's, see results/README.md) and writes to
results/figures/:
  runtime.pdf         heapsort, worst-case decrease-key and extract_min: time and cost / theory
  dijkstra_memory.pdf Dijkstra time vs graph size, and memory per item
  input_order.pdf     extract_min cost for random, sorted and reverse input
  summary_table.tex   LaTeX table of the n = 10^7 / V = 10^6 results
  summary.csv         the same numbers as CSV
(.png copies of each figure are written too, for the README / quick viewing.)

The figures are drawn at the exact text width of the ACM small template and
typeset by LaTeX with the template's fonts (Linux Libertine, 10 pt), so they
match the report when included with width=\\linewidth. Use --no-latex if no
LaTeX installation is available (falls back to matplotlib's own fonts).

Usage:
  python benchmarks/plot_results.py
  python benchmarks/plot_results.py --copy-to ../report/figures
"""

import argparse
import csv
import math
import shutil
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # no window needed
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "benchmarks"))
from check_results import load  # noqa: E402

HEAPS = ["binomial", "fibonacci", "pairing"]
LABELS = {"binomial": "Binomial", "fibonacci": "Fibonacci", "pairing": "Pairing"}
ORDER = [LABELS[h] for h in HEAPS]
# Fixed colour per heap (categorical slots 1-3, validated for colour-blind
# separation) plus a distinct marker, so the plots also work in greyscale.
PALETTE = {"Binomial": "#2a78d6", "Fibonacci": "#eb6834", "Pairing": "#1baf7a"}
MARKERS = {"Binomial": "o", "Fibonacci": "s", "Pairing": "^"}
INK, MUTED = "#2b2b2a", "#6b6a63"

TEXT_WIDTH = 395.8225 / 72.27  # \textwidth of acmsmall in inches
BODY_PT, SMALL_PT = 10, 9  # \normalsize and \small of acmsmall
LATEX_PREAMBLE = (  # the same fonts acmart loads
    r"\usepackage[T1]{fontenc}"
    r"\usepackage[tt=false, type1=true]{libertine}"
    r"\usepackage[varqu]{zi4}"
    r"\usepackage[libertine]{newtxmath}"
)


def setup_style(use_latex: bool) -> None:
    """Seaborn theme with the report's fonts and sizes.

    Input: whether to typeset text with LaTeX. Output: None (sets rcParams).
    """
    sns.set_theme(context="paper", style="whitegrid", font="serif", rc={
        "font.size": BODY_PT, "axes.titlesize": BODY_PT, "axes.labelsize": BODY_PT,
        "legend.fontsize": BODY_PT, "xtick.labelsize": SMALL_PT, "ytick.labelsize": SMALL_PT,
        "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK,
        "xtick.color": INK, "ytick.color": INK, "grid.color": "#e4e3dd",
        "axes.spines.top": False, "axes.spines.right": False,
        "lines.linewidth": 1.5, "lines.markersize": 5,
        "pdf.fonttype": 42,
    })
    if use_latex:
        plt.rcParams.update({"text.usetex": True, "text.latex.preamble": LATEX_PREAMBLE})


def ident(name: str, use_latex: bool) -> str:
    """Write an identifier like extract_min in the normal text font.

    Input: identifier, whether LaTeX is on. Output: label text (the
    underscore is escaped for LaTeX, which would otherwise read it as math).
    """
    return name.replace("_", r"\_") if use_latex else name


def to_frame(rows) -> pd.DataFrame:
    """Turn timing rows into a DataFrame with per-operation columns.

    Input: CSV rows. Output: DataFrame with heap, workload, phase, n, seconds,
    ns_per_op and ns_per_op_log (ns per op divided by log2 n).
    """
    records = []
    for r in rows:
        if not r["seconds"]:
            continue
        n, seconds, ops = int(r["n"]), float(r["seconds"]), int(r["ops"])
        ns_per_op = seconds / ops * 1e9
        records.append({
            "heap": LABELS[r["heap"]], "workload": r["workload"], "phase": r["phase"],
            "n": n, "repeat": int(r["repeat"]), "seconds": seconds,
            "ns_per_op": ns_per_op, "ns_per_op_log": ns_per_op / math.log2(n),
        })
    return pd.DataFrame(records)


def memory_frame(rows) -> pd.DataFrame:
    """Input: CSV rows. Output: DataFrame of heap, n, bytes_per_item."""
    return pd.DataFrame([
        {"heap": LABELS[r["heap"]], "n": int(r["n"]), "bytes_per_item": float(r["bytes_per_item"])}
        for r in rows if r["bytes_per_item"]
    ])


def lines(ax, data: pd.DataFrame, y: str) -> None:
    """Median line per heap with a min-max band over the repeats."""
    sns.lineplot(data=data, x="n", y=y, hue="heap", style="heap", hue_order=ORDER,
                 style_order=ORDER, palette=PALETTE, markers=MARKERS, dashes=False,
                 estimator="median", errorbar=("pi", 100), err_kws={"alpha": 0.18},
                 markeredgecolor="white", markeredgewidth=0.6, ax=ax, legend=False)
    ax.set_xscale("log")


def reference(ax, data: pd.DataFrame, cost, label: str) -> None:
    """Dashed guide proportional to cost(n), placed at half the lowest first point."""
    sizes = sorted(data["n"].unique())
    first = data[data["n"] == sizes[0]].groupby("heap")["seconds"].median().min() / 2
    ax.plot(sizes, [first * cost(n) / cost(sizes[0]) for n in sizes],
            color=MUTED, linestyle="--", linewidth=1, label=label)


LEGEND_HEIGHT = 0.3  # inches reserved at the top of each figure for the shared legend


def heap_legend(fig, extra=None, bars=False) -> None:
    """One shared legend above the panels (always present; colour + marker, or
    colour swatches for bar charts)."""
    if bars:
        handles = [plt.Rectangle((0, 0), 1, 1, color=PALETTE[h], label=h) for h in ORDER]
    else:
        handles = [plt.Line2D([], [], color=PALETTE[h], marker=MARKERS[h], label=h,
                              markeredgecolor="white", markeredgewidth=0.6) for h in ORDER]
    if extra:
        handles.append(extra)
    fig.legend(handles=handles, loc="upper center", ncol=len(handles), frameon=False,
               bbox_to_anchor=(0.5, 1.0), handlelength=1.8, columnspacing=1.4,
               borderaxespad=0.1)


def layout(fig, **pads) -> None:
    """tight_layout that leaves the top strip free for the shared legend."""
    top = 1 - LEGEND_HEIGHT / fig.get_figheight()
    fig.tight_layout(rect=(0, 0, 1, top), pad=0.3, **pads)


def panel(ax, letter: str) -> None:
    """Label a subplot (a), (b), ... centred below it, under the x-axis label."""
    ax.annotate(f"({letter})", xy=(0.5, 0), xycoords=ax.xaxis.label, xytext=(0, -4),
                textcoords="offset points", ha="center", va="top", fontsize=BODY_PT)


def save(fig, out_dir: Path, name: str) -> None:
    """Write the figure as PDF (for LaTeX) and PNG (for quick viewing).

    No bbox_inches="tight": that would trim the page below the text width and
    LaTeX would then scale the figure (and its fonts) up to \\linewidth.
    """
    fig.savefig(out_dir / f"{name}.pdf")
    fig.savefig(out_dir / f"{name}.png", dpi=200)
    plt.close(fig)


def plot_runtime(df: pd.DataFrame, out_dir: Path, tex: bool) -> None:
    """2x2 figure: heapsort and decrease-key workloads, raw time and normalized cost."""
    fig, axes = plt.subplots(2, 2, figsize=(TEXT_WIDTH, 4.7))

    heapsort = df[df["workload"] == "heapsort"]
    total = heapsort.groupby(["heap", "n", "repeat"], as_index=False)["seconds"].sum()
    ax = axes[0, 0]
    lines(ax, total, "seconds")
    nlogn = (lambda n: n * math.log2(n))
    reference(ax, total, nlogn, "")
    ax.set(yscale="log", xlabel="$n$", ylabel="seconds")
    panel(ax, "a")

    ax = axes[0, 1]
    lines(ax, heapsort[heapsort["phase"] == "extract_min"], "ns_per_op_log")
    ax.set(xlabel="$n$", ylabel=r"ns per op $/ \log_2 n$")
    panel(ax, "b")
    ax.set_ylim(bottom=0)

    decrease = df[df["workload"] == "decrease"]
    ax = axes[1, 0]
    lines(ax, df[df["workload"] == "decrease_min"], "ns_per_op")
    ax.set(xlabel="$n$", ylabel="ns per op")
    panel(ax, "c")
    ax.set_ylim(bottom=0)

    ax = axes[1, 1]
    lines(ax, decrease[decrease["phase"] == "extract_after_decrease"], "ns_per_op_log")
    ax.set(xlabel="$n$", ylabel=r"ns per op $/ \log_2 n$")
    panel(ax, "d")
    ax.set_ylim(bottom=0)

    guide = plt.Line2D([], [], color=MUTED, linestyle="--", linewidth=1, label=r"$\propto n \log n$")
    layout(fig, h_pad=1.2, w_pad=1.5)
    heap_legend(fig, guide)
    save(fig, out_dir, "runtime")


def plot_dijkstra_memory(df: pd.DataFrame, mem: pd.DataFrame, out_dir: Path, tex: bool) -> None:
    """1x2 figure: Dijkstra total time vs V, and bytes per item."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(TEXT_WIDTH, 2.5))
    dijkstra = df[df["workload"] == "dijkstra"]
    lines(ax1, dijkstra, "seconds")
    # m = 10 V, so (n + m) log n is proportional to V log V.
    reference(ax1, dijkstra, lambda v: v * math.log2(v), "")
    ax1.set(yscale="log", xlabel="nodes $V$ (edges $= 10V$)", ylabel="seconds")
    panel(ax1, "a")

    n_mem = mem["n"].max()
    at_n = mem[mem["n"] == n_mem]
    sns.barplot(data=at_n, x="heap", y="bytes_per_item", hue="heap", order=ORDER,
                hue_order=ORDER, palette=PALETTE, saturation=1, width=0.55, edgecolor="white",
                linewidth=1.5, legend=False, ax=ax2)
    for container in ax2.containers:
        ax2.bar_label(container, fmt="%.0f B", padding=2, fontsize=SMALL_PT, color=INK)
    ax2.set(xlabel=r"\phantom{nodes}" if plt.rcParams["text.usetex"] else " ",
            ylabel="bytes per item")
    panel(ax2, "b")
    ax2.set_ylim(0, at_n["bytes_per_item"].max() * 1.2)
    ax2.grid(axis="x", visible=False)

    guide = plt.Line2D([], [], color=MUTED, linestyle="--", linewidth=1, label=r"$\propto V \log V$")
    layout(fig, w_pad=2)
    heap_legend(fig, guide)
    save(fig, out_dir, "dijkstra_memory")


def plot_input_order(df: pd.DataFrame, out_dir: Path, tex: bool) -> None:
    """Grouped bars: extract_min ns per op at the largest n with all three input orders."""
    names = {"heapsort": "random keys", "sorted": "ascending keys", "reverse": "descending keys"}
    n = df[df["workload"] == "sorted"]["n"].max()
    data = df[(df["n"] == n) & (df["phase"] == "extract_min") & df["workload"].isin(names)].copy()
    data["input"] = data["workload"].map(names)

    fig, ax = plt.subplots(figsize=(TEXT_WIDTH, 2.4))
    sns.barplot(data=data, x="input", y="ns_per_op", hue="heap", order=list(names.values()),
                hue_order=ORDER, palette=PALETTE, saturation=1, estimator="median", errorbar=None,
                edgecolor="white", linewidth=1.2, ax=ax)
    for container in ax.containers:
        ax.bar_label(container, fmt="{:,.0f}", padding=2, fontsize=SMALL_PT - 1, color=INK)
    ax.set(xlabel="", ylabel=f"time per {ident('extract_min', tex)} (ns)")
    ax.set_ylim(0, data["ns_per_op"].max() * 1.18)
    ax.grid(axis="x", visible=False)
    ax.get_legend().remove()
    layout(fig)
    heap_legend(fig, bars=True)
    save(fig, out_dir, "input_order")


def collect(rows):
    """Group timings for the summary table.

    Input: CSV rows. Output: (times, ops, memory) where
    times[(workload, phase, heap)][n] = list of seconds,
    ops[(workload, phase, heap)][n] = operation count,
    memory[heap][n] = bytes per item.
    """
    times = defaultdict(lambda: defaultdict(list))
    ops = defaultdict(dict)
    memory = defaultdict(dict)
    for r in rows:
        n = int(r["n"])
        if r["seconds"]:
            key = (r["workload"], r["phase"], r["heap"])
            times[key][n].append(float(r["seconds"]))
            ops[key][n] = int(r["ops"])
        elif r["bytes_per_item"]:
            memory[r["heap"]][n] = float(r["bytes_per_item"])
    return times, ops, memory


def summary(times, ops, memory, out_dir):
    """Write the summary table (LaTeX + CSV) for the largest sizes."""
    def per_op(workload, phase, heap, unit=1e9):
        key = (workload, phase, heap)
        n = max(times[key])
        return statistics.median(times[key][n]) / ops[key][n] * unit, n

    rows = [
        ("insert (ns/op)", lambda h: per_op("heapsort", "insert", h)),
        ("extract\\_min (ns/op)", lambda h: per_op("heapsort", "extract_min", h)),
        ("decrease\\_key, random (ns/op)", lambda h: per_op("decrease", "decrease_key", h)),
        ("decrease\\_key to new minimum (ns/op)",
         lambda h: per_op("decrease_min", "decrease_key_to_min", h)),
        ("extract\\_min after decrease (ns/op)",
         lambda h: per_op("decrease", "extract_after_decrease", h)),
        ("heapsort total (s)", lambda h: (
            statistics.median(times[("heapsort", "insert", h)][10**7])
            + statistics.median(times[("heapsort", "extract_min", h)][10**7]), 10**7)),
        ("Dijkstra, V=$10^6$, E=$10^7$ (s)", lambda h: (
            statistics.median(times[("dijkstra", "dijkstra", h)][10**6]), 10**6)),
        ("memory (bytes/item, $n=10^6$)", lambda h: (memory[h][10**6], 10**6)),
    ]
    table = []
    for label, fn in rows:
        values = [fn(h)[0] for h in HEAPS]
        table.append((label, values))

    with (out_dir / "summary.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["measure"] + HEAPS)
        for label, values in table:
            writer.writerow([label.replace("\\", "").replace("$", "")] + [f"{v:.4g}" for v in values])

    lines_tex = [
        "% Generated by benchmarks/plot_results.py -- do not edit by hand.",
        "\\begin{tabular}{lrrr}",
        "\\toprule",
        "Measure ($n = 10^7$ unless stated) & Binomial & Fibonacci & Pairing \\\\",
        "\\midrule",
    ]
    for label, values in table:
        best = min(values)
        cells = [f"\\textbf{{{v:,.0f}}}" if v == best else f"{v:,.0f}" for v in values]
        if "(s)" in label:
            cells = [f"\\textbf{{{v:.1f}}}" if v == best else f"{v:.1f}" for v in values]
        lines_tex.append(f"{label} & " + " & ".join(cells) + " \\\\")
    lines_tex += ["\\bottomrule", "\\end{tabular}"]
    (out_dir / "summary_table.tex").write_text("\n".join(lines_tex) + "\n")
    return table


def main() -> None:
    """Load the CSVs, draw every figure, write the table, optionally copy to the report."""
    parser = argparse.ArgumentParser(description="Plot the benchmark results.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "figures")
    parser.add_argument("--copy-to", type=Path, help="also copy PDFs and the table here")
    parser.add_argument("--no-latex", action="store_true",
                        help="do not typeset text with LaTeX (if it is not installed)")
    args = parser.parse_args()

    use_latex = not args.no_latex and shutil.which("latex") is not None
    if not args.no_latex and not use_latex:
        print("latex not found: using matplotlib fonts (figures will not match the report font)")
    setup_style(use_latex)

    paths = sorted(str(p) for p in (ROOT / "results").glob("results_*.csv"))
    rows = load(paths)
    df, mem = to_frame(rows), memory_frame(rows)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    plot_runtime(df, args.out_dir, use_latex)
    plot_dijkstra_memory(df, mem, args.out_dir, use_latex)
    plot_input_order(df, args.out_dir, use_latex)
    table = summary(*collect(rows), args.out_dir)

    for label, values in table:
        print(f"{label.replace(chr(92), ''):40s}" + "".join(f"{v:>12,.1f}" for v in values))
    if args.copy_to:
        args.copy_to.mkdir(parents=True, exist_ok=True)
        for path in args.out_dir.glob("*.pdf"):
            shutil.copy(path, args.copy_to)
        shutil.copy(args.out_dir / "summary_table.tex", args.copy_to)
    print(f"Figures and table written to {args.out_dir}")


if __name__ == "__main__":
    main()
