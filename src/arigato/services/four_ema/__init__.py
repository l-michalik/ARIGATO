from __future__ import annotations

import argparse
from pathlib import Path
from typing import Final

from arigato.services.fetch import DEFAULT_START_DATE, DEFAULT_SYMBOL, load_symbol_data
from arigato.strategies.four_ema import (
    DEFAULT_STARTING_BALANCE,
    format_optimization_summary,
    optimize_four_ema_strategy,
    render_four_ema_comparison_chart,
)

DEFAULT_RESULTS_DIR: Final[Path] = Path("results")
DEFAULT_SHORT_WINDOWS: Final[list[int]] = [5, 8, 10]
DEFAULT_MEDIUM_WINDOWS: Final[list[int]] = [20, 30]
DEFAULT_LONG_WINDOWS: Final[list[int]] = [50, 75, 100]
DEFAULT_VERY_LONG_WINDOWS: Final[list[int]] = [150, 200]


def default_four_ema_strategies_dir(symbol: str) -> Path:
    return DEFAULT_RESULTS_DIR / symbol / "strategies"


def four_ema_strategy_chart_path(symbol: str) -> Path:
    return default_four_ema_strategies_dir(symbol) / "four_ema.png"


def render_symbol_four_ema(
    symbol: str,
    parquet_path: Path | None = None,
    start_date: str = DEFAULT_START_DATE,
    starting_balance: float = DEFAULT_STARTING_BALANCE,
    short_windows: list[int] | None = None,
    medium_windows: list[int] | None = None,
    long_windows: list[int] | None = None,
    very_long_windows: list[int] | None = None,
    top: int = 10,
) -> Path:
    frame = load_symbol_data(symbol, parquet_path, start_date)
    results = optimize_four_ema_strategy(
        frame,
        starting_balance=starting_balance,
        short_windows=short_windows or DEFAULT_SHORT_WINDOWS,
        medium_windows=medium_windows or DEFAULT_MEDIUM_WINDOWS,
        long_windows=long_windows or DEFAULT_LONG_WINDOWS,
        very_long_windows=very_long_windows or DEFAULT_VERY_LONG_WINDOWS,
    )
    selected_results = results[:top]
    print(format_optimization_summary(results, top))

    path = four_ema_strategy_chart_path(symbol)
    render_four_ema_comparison_chart(selected_results, path, symbol, highlighted_count=top)
    return path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render 4 EMA strategy results.")
    parser.add_argument("symbol", choices=[DEFAULT_SYMBOL], help="Supported symbol.")
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
    parser.add_argument(
        "--starting-balance",
        type=float,
        default=DEFAULT_STARTING_BALANCE,
        help="Starting portfolio balance in PLN.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="How many top optimization rows to print and save.",
    )
    parser.add_argument(
        "--short-windows",
        nargs="+",
        type=int,
        default=DEFAULT_SHORT_WINDOWS,
        help="Short EMA windows used in the optimization scan.",
    )
    parser.add_argument(
        "--medium-windows",
        nargs="+",
        type=int,
        default=DEFAULT_MEDIUM_WINDOWS,
        help="Medium EMA windows used in the optimization scan.",
    )
    parser.add_argument(
        "--long-windows",
        nargs="+",
        type=int,
        default=DEFAULT_LONG_WINDOWS,
        help="Long EMA windows used in the optimization scan.",
    )
    parser.add_argument(
        "--very-long-windows",
        nargs="+",
        type=int,
        default=DEFAULT_VERY_LONG_WINDOWS,
        help="Very long EMA windows used in the optimization scan.",
    )
    parser.epilog = "Saved charts are written to results/<symbol>/strategies/."
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    output_path = render_symbol_four_ema(
        args.symbol,
        args.parquet,
        args.start_date,
        args.starting_balance,
        args.short_windows,
        args.medium_windows,
        args.long_windows,
        args.very_long_windows,
        args.top,
    )
    print(f"Saved chart to {output_path}")
