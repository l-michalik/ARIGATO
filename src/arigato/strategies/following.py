from __future__ import annotations

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
from matplotlib.ticker import FuncFormatter

FAST_WINDOW: Final[int] = 13
SLOW_WINDOW: Final[int] = 50
DEFAULT_STARTING_BALANCE: Final[float] = 100_000.0
DEFAULT_FIGSIZE: Final[tuple[int, int]] = (12, 7)
DEFAULT_DPI: Final[int] = 150


@dataclass(frozen=True)
class Trade:
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    entry_price: float
    exit_price: float
    shares: float
    direction: str

    @property
    def profit(self) -> float:
        return (self.exit_price - self.entry_price) * self.shares

    @property
    def return_pct(self) -> float:
        if self.direction == "short":
            return (self.entry_price / self.exit_price - 1.0) * 100
        return (self.exit_price / self.entry_price - 1.0) * 100

    @property
    def is_successful(self) -> bool:
        return self.profit > 0


@dataclass(frozen=True)
class FollowingResult:
    frame: pd.DataFrame
    trades: list[Trade]
    starting_balance: float
    fast_window: int
    slow_window: int

    @property
    def transaction_count(self) -> int:
        return len(self.trades)

    @property
    def successful_count(self) -> int:
        return sum(trade.is_successful for trade in self.trades)

    @property
    def failed_count(self) -> int:
        return self.transaction_count - self.successful_count

    @property
    def success_pct(self) -> float:
        if self.transaction_count == 0:
            return 0.0
        return self.successful_count / self.transaction_count * 100

    @property
    def failed_pct(self) -> float:
        if self.transaction_count == 0:
            return 0.0
        return self.failed_count / self.transaction_count * 100

    @property
    def final_balance(self) -> float:
        return float(self.frame["portfolio_balance"].iloc[-1])

    @property
    def buy_and_hold_balance(self) -> float:
        return float(self.frame["sp500_balance"].iloc[-1])


def run_following_strategy(
    frame: pd.DataFrame,
    starting_balance: float = DEFAULT_STARTING_BALANCE,
    fast_window: int = FAST_WINDOW,
    slow_window: int = SLOW_WINDOW,
) -> FollowingResult:
    ordered = frame.sort_values("date").copy()
    ordered["fast_sma"] = ordered["close"].rolling(fast_window).mean()
    ordered["slow_sma"] = ordered["close"].rolling(slow_window).mean()

    first_close = float(ordered["close"].iloc[0])
    ordered["sp500_balance"] = starting_balance * ordered["close"] / first_close

    cash = starting_balance
    shares = 0.0
    position = 0
    entry_date: pd.Timestamp | None = None
    entry_price = 0.0
    entry_direction = ""
    trades: list[Trade] = []
    balances: list[float] = []
    positions: list[int] = []
    events: list[str] = []

    previous_fast: float | None = None
    previous_slow: float | None = None

    for row in ordered.itertuples():
        date = pd.Timestamp(row.date)
        close = float(row.close)
        fast = row.fast_sma
        slow = row.slow_sma
        event = ""

        has_signal = pd.notna(fast) and pd.notna(slow)
        has_previous_signal = previous_fast is not None and previous_slow is not None

        if has_signal and has_previous_signal:
            crossed_up = float(fast) > float(slow) and previous_fast <= previous_slow
            crossed_down = float(fast) < float(slow) and previous_fast >= previous_slow

            if crossed_up and position != 1:
                if position == -1 and entry_date is not None:
                    cash += shares * close
                    trades.append(
                        Trade(
                            entry_date=entry_date,
                            exit_date=date,
                            entry_price=entry_price,
                            exit_price=close,
                            shares=shares,
                            direction=entry_direction,
                        )
                    )

                shares = cash / close
                cash -= shares * close
                position = 1
                entry_date = date
                entry_price = close
                entry_direction = "long"
                event = "long"
            elif crossed_down and position != -1:
                if position == 1 and entry_date is not None:
                    cash += shares * close
                    trades.append(
                        Trade(
                            entry_date=entry_date,
                            exit_date=date,
                            entry_price=entry_price,
                            exit_price=close,
                            shares=shares,
                            direction=entry_direction,
                        )
                    )

                shares = -(cash / close)
                cash -= shares * close
                position = -1
                entry_date = date
                entry_price = close
                entry_direction = "short"
                event = "short"

        balances.append(cash + shares * close)
        positions.append(position)
        events.append(event)

        if has_signal:
            previous_fast = float(fast)
            previous_slow = float(slow)

    ordered["portfolio_balance"] = balances
    ordered["position"] = positions
    ordered["event"] = events

    return FollowingResult(
        frame=ordered,
        trades=trades,
        starting_balance=starting_balance,
        fast_window=fast_window,
        slow_window=slow_window,
    )


def optimize_following_strategy(
    frame: pd.DataFrame,
    starting_balance: float,
    fast_windows: list[int],
    slow_windows: list[int],
) -> list[FollowingResult]:
    results: list[FollowingResult] = []

    for fast_window in fast_windows:
        for slow_window in slow_windows:
            if fast_window >= slow_window:
                continue
            result = run_following_strategy(
                frame,
                starting_balance=starting_balance,
                fast_window=fast_window,
                slow_window=slow_window,
            )
            results.append(result)

    return sorted(results, key=lambda result: result.final_balance, reverse=True)


def format_summary(result: FollowingResult) -> str:
    return "\n".join(
        [
            f"SMA fast/slow: {result.fast_window}/{result.slow_window}",
            f"Kapital poczatkowy: {result.starting_balance:,.2f} PLN",
            f"Kapital koncowy strategii: {result.final_balance:,.2f} PLN",
            f"Kapital koncowy S&P 500: {result.buy_and_hold_balance:,.2f} PLN",
            f"Transakcje: {result.transaction_count}",
            f"Sukces: {result.success_pct:.2f}%",
            f"Przegrane: {result.failed_pct:.2f}%",
        ]
    )


def format_optimization_summary(results: list[FollowingResult], top: int) -> str:
    rows = [
        "Top parametry wedlug kapitalu koncowego:",
        "fast slow kapital PLN transakcje sukces przegrane",
    ]

    for result in results[:top]:
        rows.append(
            " ".join(
                [
                    f"{result.fast_window:>4}",
                    f"{result.slow_window:>4}",
                    f"{result.final_balance:>12,.2f}",
                    f"{result.transaction_count:>10}",
                    f"{result.success_pct:>6.2f}%",
                    f"{result.failed_pct:>8.2f}%",
                ]
            )
        )

    return "\n".join(rows)


def render_following_chart(
    result: FollowingResult,
    output_path: Path,
    symbol: str,
) -> Path:
    frame = result.frame
    long_points = frame[frame["event"] == "long"]
    short_points = frame[frame["event"] == "short"]

    fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE, dpi=DEFAULT_DPI)
    ax.plot(
        frame["date"],
        frame["sp500_balance"],
        color="#64748b",
        linewidth=1.2,
        label="S&P 500 buy-and-hold od 100 000 PLN",
    )
    ax.plot(
        frame["date"],
        frame["portfolio_balance"],
        color="#0f766e",
        linewidth=1.5,
        label=f"Trend following {result.fast_window}/{result.slow_window} SMA",
    )
    ax.scatter(
        long_points["date"],
        long_points["portfolio_balance"],
        color="#16a34a",
        marker="^",
        s=28,
        label="Long",
        zorder=3,
    )
    ax.scatter(
        short_points["date"],
        short_points["portfolio_balance"],
        color="#dc2626",
        marker="v",
        s=28,
        label="Short",
        zorder=3,
    )

    ax.set_title(f"{symbol.upper()} - S&P 500 vs trend following")
    ax.set_xlabel("Data")
    ax.set_ylabel("Wartosc portfela [PLN]")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.0f}"))
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper left")
    ax.text(
        0.02,
        0.72,
        format_summary(result),
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        bbox={"boxstyle": "round,pad=0.45", "facecolor": "white", "alpha": 0.9},
    )

    fig.autofmt_xdate()
    fig.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


def render_following_comparison_chart(
    results: list[FollowingResult],
    output_path: Path,
    symbol: str,
    highlighted_count: int = 5,
) -> Path:
    best = results[0]
    fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE, dpi=DEFAULT_DPI)
    colors = plt.get_cmap("tab20")

    ax.plot(
        best.frame["date"],
        best.frame["sp500_balance"],
        color="#111827",
        linewidth=2.0,
        label="S&P 500 buy-and-hold",
        zorder=4,
    )

    for index, result in enumerate(results):
        is_highlighted = index < highlighted_count
        label = None
        if is_highlighted:
            label = (
                f"SMA {result.fast_window}/{result.slow_window} "
                f"({result.final_balance:,.0f} PLN)"
            )

        ax.plot(
            result.frame["date"],
            result.frame["portfolio_balance"],
            color=colors(index % 20),
            linewidth=1.7 if is_highlighted else 0.7,
            alpha=0.95 if is_highlighted else 0.18,
            label=label,
            zorder=3 if is_highlighted else 2,
        )

    ax.set_title(f"{symbol.upper()} - porownanie parametrow trend following")
    ax.set_xlabel("Data")
    ax.set_ylabel("Wartosc portfela [PLN]")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.0f}"))
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper left", fontsize=9)
    ax.text(
        0.02,
        0.36,
        f"Liczba wariantow: {len(results)}\nNajlepszy: SMA {best.fast_window}/{best.slow_window}\nKapital: {best.final_balance:,.2f} PLN",
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        bbox={"boxstyle": "round,pad=0.45", "facecolor": "white", "alpha": 0.9},
    )

    fig.autofmt_xdate()
    fig.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path
