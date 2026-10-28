"""Stage 4 — charts drawn from the measured results (never from LLM text)."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

_COLORS = ["#2563eb", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6"]


def bar_chart(results: dict, out: Path) -> Path | None:
    ch = results.get("chart")
    if not ch:  # harness_failed runs have no measured chart
        return None
    ch = results["chart"]
    labels, series = ch["labels"], ch["series"]
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=160)
    width = 0.8 / len(series)
    for i, (name, vals) in enumerate(series.items()):
        xs = [x + i * width for x in range(len(labels))]
        bars = ax.bar(xs, vals, width, label=name, color=_COLORS[i % len(_COLORS)])
        ax.bar_label(bars, fmt="%.3g", fontsize=8, padding=2)
    ax.set_xticks([x + width * (len(series) - 1) / 2 for x in range(len(labels))], labels)
    ax.set_ylabel(ch.get("ylabel", ""))
    ax.set_title(ch["title"], fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    return out


_VERDICT_COLORS = {"worked": "#22c55e", "partial": "#f59e0b", "failed": "#ef4444"}


def outcomes_chart(results: dict, out: Path) -> Path:
    """What worked / what didn't — one coloured row per case, straight from results.json."""
    rows = results["outcomes"][:8]
    fig, ax = plt.subplots(figsize=(8, 0.6 * len(rows) + 1.4), dpi=160)
    ax.axis("off")
    ax.set_title("What worked and what didn't", fontweight="bold", loc="left")
    for i, o in enumerate(rows):
        y = 1 - (i + 1) / (len(rows) + 1)
        ax.add_patch(plt.Rectangle((0, y - 0.04), 0.03, 0.08, color=_VERDICT_COLORS[o["verdict"]],
                                   transform=ax.transAxes))
        ax.text(0.05, y, f'{o["case"][:46]}  —  {o["verdict"]}', va="center", fontsize=9,
                transform=ax.transAxes)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def summary_card(results: dict, title: str, out: Path) -> Path:
    """Headline-metrics card; reused as the LinkedIn image."""
    items = list(results["summary"].items())[:4]
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=160)
    ax.axis("off")
    fig.patch.set_facecolor("#0f172a")
    ax.text(0.02, 0.92, title, color="white", fontsize=15, fontweight="bold", va="top",
            transform=ax.transAxes, wrap=True)
    for i, (k, v) in enumerate(items):
        x = 0.02 + (i % 2) * 0.5
        y = 0.55 - (i // 2) * 0.35
        val = f"{v:.4g}" if isinstance(v, (int, float)) else str(v)
        ax.text(x, y, val, color="#38bdf8", fontsize=26, fontweight="bold", transform=ax.transAxes)
        ax.text(x, y - 0.1, k.replace("_", " "), color="#cbd5e1", fontsize=10, transform=ax.transAxes)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor=fig.get_facecolor())
    plt.close(fig)
    return out
