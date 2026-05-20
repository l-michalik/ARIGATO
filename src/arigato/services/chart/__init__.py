from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from tempfile import gettempdir
from typing import Final

os.environ.setdefault("MPLCONFIGDIR", str(Path(gettempdir()) / "matplotlib"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from arigato.services.fetch import DEFAULT_START_DATE, DEFAULT_SYMBOL, load_symbol_data


@dataclass(frozen=True)
class ChartContext:
    frame: pd.DataFrame
    date_column: str
    value_column: str


DEFAULT_CHART_DIR: Final[Path] = Path("results")
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


def default_chart_path(symbol: str) -> Path:
    return DEFAULT_CHART_DIR / symbol / "chart.png"


def render_symbol_chart(
    symbol: str,
    output_path: Path | None = None,
    parquet_path: Path | None = None,
    start_date: str = DEFAULT_START_DATE,
) -> Path:
    frame = load_symbol_data(symbol, parquet_path, start_date)
    path = output_path or default_chart_path(symbol)
    return render_chart(frame, path, title=f"{symbol} close since 2016")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render a chart for a symbol.")
    parser.add_argument("symbol", choices=[DEFAULT_SYMBOL], help="Supported symbol.")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Where to save the chart image.",
    )
    parser.add_argument(
        "--parquet",
        type=Path,
        default=None,
        help="Path to the cached parquet file.",
    )
    parser.add_argument(
        "--start-date",
        default=DEFAULT_START_DATE,
        help="Start date for the download if the cache is missing.",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    output_path = render_symbol_chart(args.symbol, args.output, args.parquet, args.start_date)
    print(f"Saved chart to {output_path}")

