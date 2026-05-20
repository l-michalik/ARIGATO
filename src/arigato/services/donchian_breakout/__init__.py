from __future__ import annotations

import argparse
from pathlib import Path
from typing import Final

from arigato.services.fetch import DEFAULT_START_DATE, DEFAULT_SYMBOL, load_symbol_data
from arigato.strategies.donchian_breakout import (
    DEFAULT_STARTING_BALANCE,
    format_optimization_summary,
    optimize_donchian_breakout_strategy,
    render_donchian_breakout_comparison_chart,
)

DEFAULT_RESULTS_DIR: Final[Path] = Path("results")
DEFAULT_ENTRY_WINDOWS: Final[list[int]] = [20, 25, 30, 35, 40, 45, 50, 55, 60, 70]
DEFAULT_EXIT_WINDOWS: Final[list[int]] = [5, 10, 15, 20, 25, 30, 35, 40]


def default_donchian_breakout_strategies_dir(symbol: str) -> Path:
    return DEFAULT_RESULTS_DIR / symbol / "strategies"


def donchian_breakout_strategy_chart_path(symbol: str) -> Path:
    return default_donchian_breakout_strategies_dir(symbol) / "donchian_breakout.png"


def render_symbol_donchian_breakout(
    symbol: str,
    parquet_path: Path | None = None,
    start_date: str = DEFAULT_START_DATE,
    starting_balance: float = DEFAULT_STARTING_BALANCE,
    entry_windows: list[int] | None = None,
    exit_windows: list[int] | None = None,
    top: int = 10,
) -> Path:
    frame = load_symbol_data(symbol, parquet_path, start_date)
    results = optimize_donchian_breakout_strategy(
        frame,
        starting_balance=starting_balance,
        entry_windows=entry_windows or DEFAULT_ENTRY_WINDOWS,
        exit_windows=exit_windows or DEFAULT_EXIT_WINDOWS,
    )
    selected_results = results[:top]
    print(format_optimization_summary(results, top))

    path = donchian_breakout_strategy_chart_path(symbol)
    render_donchian_breakout_comparison_chart(
        selected_results,
        path,
        symbol,
        highlighted_count=top,
    )
    return path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render Donchian Breakout strategy results.")
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
        "--entry-windows",
        nargs="+",
        type=int,
        default=DEFAULT_ENTRY_WINDOWS,
        help="Entry channel windows used in the optimization scan.",
    )
    parser.add_argument(
        "--exit-windows",
        nargs="+",
        type=int,
        default=DEFAULT_EXIT_WINDOWS,
        help="Exit channel windows used in the optimization scan.",
    )
    parser.epilog = "Saved charts are written to results/<symbol>/strategies/."
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    output_path = render_symbol_donchian_breakout(
        args.symbol,
        args.parquet,
        args.start_date,
        args.starting_balance,
        args.entry_windows,
        args.exit_windows,
        args.top,
    )
    print(f"Saved chart to {output_path}")
