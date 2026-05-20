from __future__ import annotations

import argparse
from pathlib import Path
from typing import Final

import pandas as pd

from arigato.charting import render_chart
from arigato.symbols.sp500.data import DEFAULT_OUTPUT_PATH, load_sp500_data, normalize_columns

DEFAULT_CHART_PATH: Final[Path] = Path("data") / "sp500.png"


def render_sp500_chart(
    frame: pd.DataFrame,
    output_path: Path = DEFAULT_CHART_PATH,
) -> Path:
    return render_chart(
        normalize_columns(frame),
        output_path,
        title="S&P 500 close since 2016",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render an S&P 500 chart.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_CHART_PATH,
        help="Where to save the chart image.",
    )
    parser.add_argument(
        "--parquet",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Path to the cached parquet file.",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    frame = load_sp500_data(args.parquet)
    output_path = render_sp500_chart(frame, args.output)
    print(f"Saved chart to {output_path}")
