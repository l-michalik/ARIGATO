from __future__ import annotations

import argparse
from pathlib import Path

from arigato.charting import render_chart
from arigato.symbols.sp500.data import (
    DEFAULT_START_DATE,
    DEFAULT_SYMBOL,
    default_chart_path,
    load_symbol_data,
)


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
