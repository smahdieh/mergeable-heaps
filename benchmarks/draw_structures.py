"""Draw the illustration of the three heaps used in the report (Figure 1).

  (a) binomial heap with n = 13 = 1101 in binary: trees B_0, B_2 and B_3
  (b) Fibonacci heap: root list, min pointer and marked nodes
  (c) pairing heap: one heap-ordered tree with any number of children

Writes results/figures/structures.pdf and .png, in the same style and fonts
as plot_results.py.

Usage:
  python benchmarks/draw_structures.py [--copy-to ../report/figures] [--no-latex]
"""

import argparse
import shutil
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "benchmarks"))
from plot_results import INK, MUTED, SMALL_PT, TEXT_WIDTH, setup_style  # noqa: E402

RADIUS = 0.38         # node radius in data units (one leaf slot = 1)
LEVEL = 1.05          # vertical distance between tree levels
GAP = 0.7             # horizontal gap between trees of one heap
DEPTH = 3             # deepest level in any panel (all panels share one scale)
MARKED_FILL = "#6b6a63"

# Trees as (key, [children]); a key ending in "*" is a marked node.
BINOMIAL = [
    ("5", []),                                                     # B_0
    ("3", [("7", [("9", [])]), ("10", [])]),                       # B_2
    ("1", [("2", [("6", [("12", [])]), ("11", [])]),               # B_3
           ("4", [("13", [])]), ("15", [])]),
]
FIBONACCI = [
    ("23", []),
    ("7", []),
    ("3", [("18*", [("39", [])]), ("52", []), ("38", [("41", [])])]),
    ("17", [("30", [])]),
    ("24", [("26*", [("35", [])]), ("46", [])]),
]
PAIRING = ("2", [("6", [("8", [])]), ("4", [("7", []), ("11", [])]),
                 ("9", [("12", [])]), ("10", [])])


def width(tree) -> int:
    """Input: (key, children). Output: number of leaf slots the tree needs."""
    return max(1, sum(width(child) for child in tree[1]))


def layout(tree, left: float, depth: int, positions: list, edges: list):
    """Place a tree with its leaves on integer slots starting at `left`.

    Input: tree, leftmost slot, depth, and lists to collect
    (key, x, y) positions and (x1, y1, x2, y2) edges.
    Output: (x, y) of the tree's root.
    """
    key, children = tree
    if not children:
        x = left + 0.5
    else:
        xs, slot = [], left
        for child in children:
            cx, cy = layout(child, slot, depth + 1, positions, edges)
            xs.append((cx, cy))
            slot += width(child)
        x = (xs[0][0] + xs[-1][0]) / 2
    y = -depth * LEVEL
    for cx, cy in (xs if children else []):
        edges.append((x, y, cx, cy))
    positions.append((key, x, y))
    return x, y


def draw_forest(ax, trees, gap: float = GAP) -> list:
    """Lay out several trees side by side and draw them.

    Input: axes, list of trees, horizontal gap between trees.
    Output: list of (x, y) root positions, left to right.
    """
    positions, edges, roots, left = [], [], [], 0.0
    for tree in trees:
        roots.append(layout(tree, left, 0, positions, edges))
        left += width(tree) + gap
    for x1, y1, x2, y2 in edges:
        ax.plot([x1, x2], [y1, y2], color=MUTED, linewidth=0.9, zorder=1)
    for key, x, y in positions:
        marked = key.endswith("*")
        ax.add_patch(Circle((x, y), RADIUS, facecolor=MARKED_FILL if marked else "white",
                            edgecolor=INK, linewidth=0.9, zorder=2))
        ax.text(x, y, key.rstrip("*"), ha="center", va="center", fontsize=SMALL_PT,
                color="white" if marked else INK, zorder=3)
    return roots


def root_list(ax, roots, circular: bool = False) -> None:
    """Draw the links between consecutive roots (and the wrap-around if circular)."""
    for (x1, y1), (x2, y2) in zip(roots, roots[1:]):
        ax.add_patch(FancyArrowPatch((x1 + RADIUS, y1), (x2 - RADIUS, y2),
                                     arrowstyle="<->" if circular else "->",
                                     mutation_scale=6, color=INK, linewidth=0.8))
    if circular:  # wrap-around link drawn as a bracket above the roots
        (xa, ya), (xb, yb) = roots[0], roots[-1]
        top = ya + RADIUS + 0.55
        ax.plot([xb, xb, xa], [yb + RADIUS, top, top], color=MUTED, linewidth=0.8)
        ax.add_patch(FancyArrowPatch((xa, top), (xa, ya + RADIUS), arrowstyle="->",
                                     mutation_scale=6, color=MUTED, linewidth=0.8,
                                     shrinkA=0, shrinkB=0))

def span(trees, gap: float = GAP) -> float:
    """Input: list of trees. Output: horizontal extent of the drawn forest."""
    return sum(width(t) for t in trees) + gap * (len(trees) - 1)


def finish(ax, extent: float) -> None:
    """Same vertical range in every panel, x range fitted to the content, no axes."""
    ax.set_xlim(-0.05, extent + 0.05)
    ax.set_ylim(-DEPTH * LEVEL - RADIUS - 0.05, RADIUS + 0.75)
    ax.set_aspect("equal")
    ax.axis("off")


def main() -> None:
    """Draw the three panels and save the figure."""
    parser = argparse.ArgumentParser(description="Draw the heap illustrations.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "figures")
    parser.add_argument("--copy-to", type=Path, help="also copy the PDF here")
    parser.add_argument("--no-latex", action="store_true")
    args = parser.parse_args()
    setup_style(not args.no_latex and shutil.which("latex") is not None)

    extents = [span(BINOMIAL), span(FIBONACCI), span([PAIRING])]
    pads = 1.2  # data units of white space between panels
    unit = TEXT_WIDTH / (sum(extents) + pads * 2 + 0.3)  # inches per data unit
    plot_h = (DEPTH * LEVEL + 2 * RADIUS + 0.8) * unit
    label_h = 0.22  # inches for the (a)/(b)/(c) row
    fig = plt.figure(figsize=(TEXT_WIDTH, plot_h + label_h))
    axes, left = [], 0.15 * unit
    for extent in extents:
        w = (extent + 0.1) * unit
        axes.append(fig.add_axes((left / TEXT_WIDTH, label_h / (plot_h + label_h),
                                  w / TEXT_WIDTH, plot_h / (plot_h + label_h))))
        left += w + pads * unit

    ax = axes[0]
    roots = draw_forest(ax, BINOMIAL)
    root_list(ax, roots)
    for (x, y), label in zip(roots, ["$B_0$", "$B_2$", "$B_3$"]):
        ax.text(x, y + RADIUS + 0.15, label, ha="center", va="bottom", fontsize=SMALL_PT)
    finish(ax, extents[0])

    ax = axes[1]
    roots = draw_forest(ax, FIBONACCI)
    root_list(ax, roots, circular=True)
    x, y = roots[2]
    ax.annotate("min", xy=(x - RADIUS * 0.75, y + RADIUS * 0.75), xytext=(x - 0.75, y + 0.62),
                fontsize=SMALL_PT, ha="right", va="center",
                arrowprops={"arrowstyle": "->", "color": INK, "linewidth": 0.8,
                            "shrinkA": 1, "shrinkB": 0})
    finish(ax, extents[1])

    ax = axes[2]
    draw_forest(ax, [PAIRING])
    finish(ax, extents[2])

    for ax, letter in zip(axes, "abc"):  # letters on one baseline, centred below each panel
        box = ax.get_position()
        fig.text(box.x0 + box.width / 2, 0.02, f"({letter})", ha="center", va="bottom")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out_dir / "structures.pdf")
    fig.savefig(args.out_dir / "structures.png", dpi=200)
    if args.copy_to:
        shutil.copy(args.out_dir / "structures.pdf", args.copy_to)
    print(f"Wrote {args.out_dir / 'structures.pdf'}")


if __name__ == "__main__":
    main()
