from __future__ import annotations

from pathlib import Path
from tempfile import gettempdir
from typing import Final

import os

os.environ.setdefault("MPLCONFIGDIR", str(Path(gettempdir()) / "matplotlib"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from arigato.charting.base import ChartContext

DEFAULT_FIGSIZE: Final[tuple[int, int]] = (12, 6)
DEFAULT_DPI: Final[int] = 150


def _build_context(frame: pd.DataFrame) -> ChartContext:
    if "date" in frame.columns:
        date_column = "date"
    else:
        date_column = frame.columns[0]

    if "close" in frame.columns:
        value_column = "close"
    else:
        value_column = frame.columns[0]

    ordered = frame.sort_values(date_column).copy()
    return ChartContext(frame=ordered, date_column=date_column, value_column=value_column)


def render_chart(
    frame: pd.DataFrame,
    output_path: Path,
    title: str = "Close since 2016",
    xlabel: str = "Date",
    ylabel: str = "Close",
) -> Path:
    context = _build_context(frame)

    fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE, dpi=DEFAULT_DPI)
    ax.plot(
        context.frame[context.date_column],
        context.frame[context.value_column],
        color="#0f766e",
        linewidth=1.4,
    )
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.25)
    fig.autofmt_xdate()
    fig.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path
