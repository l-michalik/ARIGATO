from __future__ import annotations

import argparse
from pathlib import Path
from typing import Final
import pandas as pd

from arigato.charting import DEFAULT_CHART_PATH, available_strategies, get_strategy, render_chart
from arigato.sp500_data import DEFAULT_OUTPUT_PATH, load_sp500_data, normalize_columns

DEFAULT_STRATEGY_NAME: Final[str] = "close-line"


def _normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    return normalize_columns(frame)


def render_sp500_chart(
    frame: pd.DataFrame,
    output_path: Path = DEFAULT_CHART_PATH,
    strategy_name: str = DEFAULT_STRATEGY_NAME,
) -> Path:
    strategy = get_strategy(strategy_name)
    return render_chart(_normalize_columns(frame), strategy, output_path)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render an S&P 500 chart.")
    parser.add_argument(
        "--strategy",
        default=DEFAULT_STRATEGY_NAME,
        choices=available_strategies(),
        help="Chart strategy to render.",
    )
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
    output_path = render_sp500_chart(frame, args.output, args.strategy)
    print(f"Saved chart to {output_path}")
