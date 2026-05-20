from __future__ import annotations

import argparse
from pathlib import Path

from arigato.symbols.sp500.data import (
    DEFAULT_START_DATE,
    DEFAULT_SYMBOL,
    default_parquet_path,
    download_symbol_history,
    save_to_parquet,
)


def fetch_symbol(symbol: str, output_path: Path | None = None, start_date: str = DEFAULT_START_DATE) -> Path:
    frame = download_symbol_history(symbol, start_date)
    path = output_path or default_parquet_path(symbol)
    return save_to_parquet(frame, path)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch market data for a symbol.")
    parser.add_argument("symbol", choices=[DEFAULT_SYMBOL], help="Supported symbol.")
    parser.add_argument(
        "--start-date",
        default=DEFAULT_START_DATE,
        help="Start date for the download.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Where to save the parquet file.",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    output_path = fetch_symbol(args.symbol, args.output, args.start_date)
    print(f"Saved data to {output_path}")
