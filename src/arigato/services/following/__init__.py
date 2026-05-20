from __future__ import annotations

import argparse
from pathlib import Path
from typing import Final

from arigato.services.fetch import DEFAULT_START_DATE, DEFAULT_SYMBOL, load_symbol_data
from arigato.strategies.following import (
    DEFAULT_STARTING_BALANCE,
    format_optimization_summary,
    optimize_following_strategy,
    render_following_comparison_chart,
)

DEFAULT_RESULTS_DIR: Final[Path] = Path("results")
DEFAULT_FAST_WINDOWS: Final[list[int]] = [5, 10, 13, 15, 20, 25, 30]
DEFAULT_SLOW_WINDOWS: Final[list[int]] = [40, 50, 75, 100, 150, 200]


def default_following_strategies_dir(symbol: str) -> Path:
    return DEFAULT_RESULTS_DIR / symbol / "strategies"


def following_strategy_chart_path(symbol: str) -> Path:
    return default_following_strategies_dir(symbol) / "following.png"


def render_symbol_following(
    symbol: str,
    parquet_path: Path | None = None,
    start_date: str = DEFAULT_START_DATE,
    starting_balance: float = DEFAULT_STARTING_BALANCE,
    fast_windows: list[int] | None = None,
    slow_windows: list[int] | None = None,
    top: int = 10,
) -> Path:
    frame = load_symbol_data(symbol, parquet_path, start_date)
    results = optimize_following_strategy(
        frame,
        starting_balance=starting_balance,
        fast_windows=fast_windows or DEFAULT_FAST_WINDOWS,
        slow_windows=slow_windows or DEFAULT_SLOW_WINDOWS,
    )
    selected_results = results[:top]
    print(format_optimization_summary(results, top))

    path = following_strategy_chart_path(symbol)
    render_following_comparison_chart(selected_results, path, symbol, highlighted_count=top)
    return path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render trend following strategy results.")
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
        "--fast-windows",
        nargs="+",
        type=int,
        default=DEFAULT_FAST_WINDOWS,
        help="Fast SMA windows used in the optimization scan.",
    )
    parser.add_argument(
        "--slow-windows",
        nargs="+",
        type=int,
        default=DEFAULT_SLOW_WINDOWS,
        help="Slow SMA windows used in the optimization scan.",
    )
    parser.epilog = "Saved charts are written to results/<symbol>/strategies/."
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    output_path = render_symbol_following(
        args.symbol,
        args.parquet,
        args.start_date,
        args.starting_balance,
        args.fast_windows,
        args.slow_windows,
        args.top,
    )
    print(f"Saved chart to {output_path}")
