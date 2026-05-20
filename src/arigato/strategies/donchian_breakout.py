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

DEFAULT_ENTRY_WINDOW: Final[int] = 20
DEFAULT_EXIT_WINDOW: Final[int] = 10
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
class DonchianBreakoutResult:
    frame: pd.DataFrame
    trades: list[Trade]
    starting_balance: float
    entry_window: int
    exit_window: int

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

    @property
    def windows_label(self) -> str:
        return f"{self.entry_window}/{self.exit_window}"


def _add_donchian_channels(
    frame: pd.DataFrame,
    entry_window: int,
    exit_window: int,
) -> pd.DataFrame:
    ordered = frame.sort_values("date").copy()
    ordered["entry_high"] = ordered["high"].rolling(entry_window).max().shift(1)
    ordered["entry_low"] = ordered["low"].rolling(entry_window).min().shift(1)
    ordered["exit_high"] = ordered["high"].rolling(exit_window).max().shift(1)
    ordered["exit_low"] = ordered["low"].rolling(exit_window).min().shift(1)
    return ordered


def run_donchian_breakout_strategy(
    frame: pd.DataFrame,
    starting_balance: float = DEFAULT_STARTING_BALANCE,
    entry_window: int = DEFAULT_ENTRY_WINDOW,
    exit_window: int = DEFAULT_EXIT_WINDOW,
) -> DonchianBreakoutResult:
    ordered = _add_donchian_channels(frame, entry_window, exit_window)

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

    for row in ordered.itertuples():
        date = pd.Timestamp(row.date)
        close = float(row.close)
        event = ""

        has_entry_signal = pd.notna(row.entry_high) and pd.notna(row.entry_low)
        has_exit_signal = pd.notna(row.exit_high) and pd.notna(row.exit_low)
        long_entry = has_entry_signal and close > float(row.entry_high)
        short_entry = has_entry_signal and close < float(row.entry_low)
        long_exit = has_exit_signal and close < float(row.exit_low)
        short_exit = has_exit_signal and close > float(row.exit_high)

        if position == 1 and entry_date is not None and (long_exit or short_entry):
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
            shares = 0.0
            position = 0
            entry_date = None
            entry_price = 0.0
            entry_direction = ""
            event = "exit"

        if position == -1 and entry_date is not None and (short_exit or long_entry):
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
            shares = 0.0
            position = 0
            entry_date = None
            entry_price = 0.0
            entry_direction = ""
            event = "exit"

        if position == 0 and long_entry:
            shares = cash / close
            cash -= shares * close
            position = 1
            entry_date = date
            entry_price = close
            entry_direction = "long"
            event = "long"
        elif position == 0 and short_entry:
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

    ordered["portfolio_balance"] = balances
    ordered["position"] = positions
    ordered["event"] = events

    return DonchianBreakoutResult(
        frame=ordered,
        trades=trades,
        starting_balance=starting_balance,
        entry_window=entry_window,
        exit_window=exit_window,
    )


def optimize_donchian_breakout_strategy(
    frame: pd.DataFrame,
    starting_balance: float,
    entry_windows: list[int],
    exit_windows: list[int],
) -> list[DonchianBreakoutResult]:
    results: list[DonchianBreakoutResult] = []

    for entry_window in entry_windows:
        for exit_window in exit_windows:
            if exit_window >= entry_window:
                continue
            result = run_donchian_breakout_strategy(
                frame,
                starting_balance=starting_balance,
                entry_window=entry_window,
                exit_window=exit_window,
            )
            results.append(result)

    return sorted(results, key=lambda result: result.final_balance, reverse=True)


def format_summary(result: DonchianBreakoutResult) -> str:
    return "\n".join(
        [
            f"Donchian entry/exit: {result.windows_label}",
            f"Kapital poczatkowy: {result.starting_balance:,.2f} PLN",
            f"Kapital koncowy strategii: {result.final_balance:,.2f} PLN",
            f"Kapital koncowy S&P 500: {result.buy_and_hold_balance:,.2f} PLN",
            f"Transakcje: {result.transaction_count}",
            f"Sukces: {result.success_pct:.2f}%",
            f"Przegrane: {result.failed_pct:.2f}%",
        ]
    )


def format_optimization_summary(
    results: list[DonchianBreakoutResult],
    top: int,
) -> str:
    rows = [
        "Top parametry wedlug kapitalu koncowego:",
        "entry exit kapital PLN transakcje sukces przegrane",
    ]

    for result in results[:top]:
        rows.append(
            " ".join(
                [
                    f"{result.entry_window:>5}",
                    f"{result.exit_window:>4}",
                    f"{result.final_balance:>12,.2f}",
                    f"{result.transaction_count:>10}",
                    f"{result.success_pct:>6.2f}%",
                    f"{result.failed_pct:>8.2f}%",
                ]
            )
        )

    return "\n".join(rows)


def render_donchian_breakout_chart(
    result: DonchianBreakoutResult,
    output_path: Path,
    symbol: str,
) -> Path:
    frame = result.frame
    long_points = frame[frame["event"] == "long"]
    short_points = frame[frame["event"] == "short"]
    exit_points = frame[frame["event"] == "exit"]

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
        label=f"Donchian {result.windows_label}",
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
    ax.scatter(
        exit_points["date"],
        exit_points["portfolio_balance"],
        color="#f59e0b",
        marker="x",
        s=24,
        label="Exit",
        zorder=3,
    )

    ax.set_title(f"{symbol.upper()} - S&P 500 vs Donchian Breakout")
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


def render_donchian_breakout_comparison_chart(
    results: list[DonchianBreakoutResult],
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
                f"Donchian {result.windows_label} "
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

    ax.set_title(f"{symbol.upper()} - porownanie parametrow Donchian Breakout")
    ax.set_xlabel("Data")
    ax.set_ylabel("Wartosc portfela [PLN]")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.0f}"))
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper left", fontsize=9)
    ax.text(
        0.02,
        0.36,
        f"Liczba wariantow: {len(results)}\nNajlepszy: Donchian {best.windows_label}\nKapital: {best.final_balance:,.2f} PLN",
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
