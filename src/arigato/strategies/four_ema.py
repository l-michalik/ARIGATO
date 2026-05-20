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

DEFAULT_SHORT_WINDOW: Final[int] = 5
DEFAULT_MEDIUM_WINDOW: Final[int] = 20
DEFAULT_LONG_WINDOW: Final[int] = 50
DEFAULT_VERY_LONG_WINDOW: Final[int] = 200
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
class FourEmaResult:
    frame: pd.DataFrame
    trades: list[Trade]
    starting_balance: float
    short_window: int
    medium_window: int
    long_window: int
    very_long_window: int

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
        return (
            f"{self.short_window}/"
            f"{self.medium_window}/"
            f"{self.long_window}/"
            f"{self.very_long_window}"
        )


def _ema(series: pd.Series, window: int) -> pd.Series:
    return series.ewm(span=window, adjust=False, min_periods=window).mean()


def _alignment(row: object) -> int:
    short = float(row.short_ema)
    medium = float(row.medium_ema)
    long = float(row.long_ema)
    very_long = float(row.very_long_ema)

    if short > medium > long > very_long:
        return 1
    if short < medium < long < very_long:
        return -1
    return 0


def run_four_ema_strategy(
    frame: pd.DataFrame,
    starting_balance: float = DEFAULT_STARTING_BALANCE,
    short_window: int = DEFAULT_SHORT_WINDOW,
    medium_window: int = DEFAULT_MEDIUM_WINDOW,
    long_window: int = DEFAULT_LONG_WINDOW,
    very_long_window: int = DEFAULT_VERY_LONG_WINDOW,
) -> FourEmaResult:
    ordered = frame.sort_values("date").copy()
    ordered["short_ema"] = _ema(ordered["close"], short_window)
    ordered["medium_ema"] = _ema(ordered["close"], medium_window)
    ordered["long_ema"] = _ema(ordered["close"], long_window)
    ordered["very_long_ema"] = _ema(ordered["close"], very_long_window)

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

        has_signal = (
            pd.notna(row.short_ema)
            and pd.notna(row.medium_ema)
            and pd.notna(row.long_ema)
            and pd.notna(row.very_long_ema)
        )
        signal = _alignment(row) if has_signal else 0

        if signal != 0 and signal != position:
            if position != 0 and entry_date is not None:
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

            shares = signal * (cash / close)
            cash -= shares * close
            position = signal
            entry_date = date
            entry_price = close
            entry_direction = "long" if signal == 1 else "short"
            event = entry_direction
        elif signal == 0 and position != 0 and entry_date is not None:
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

        balances.append(cash + shares * close)
        positions.append(position)
        events.append(event)

    ordered["portfolio_balance"] = balances
    ordered["position"] = positions
    ordered["event"] = events

    return FourEmaResult(
        frame=ordered,
        trades=trades,
        starting_balance=starting_balance,
        short_window=short_window,
        medium_window=medium_window,
        long_window=long_window,
        very_long_window=very_long_window,
    )


def optimize_four_ema_strategy(
    frame: pd.DataFrame,
    starting_balance: float,
    short_windows: list[int],
    medium_windows: list[int],
    long_windows: list[int],
    very_long_windows: list[int],
) -> list[FourEmaResult]:
    results: list[FourEmaResult] = []

    for short_window in short_windows:
        for medium_window in medium_windows:
            for long_window in long_windows:
                for very_long_window in very_long_windows:
                    if not short_window < medium_window < long_window < very_long_window:
                        continue
                    result = run_four_ema_strategy(
                        frame,
                        starting_balance=starting_balance,
                        short_window=short_window,
                        medium_window=medium_window,
                        long_window=long_window,
                        very_long_window=very_long_window,
                    )
                    results.append(result)

    return sorted(results, key=lambda result: result.final_balance, reverse=True)


def format_summary(result: FourEmaResult) -> str:
    return "\n".join(
        [
            f"EMA: {result.windows_label}",
            f"Kapital poczatkowy: {result.starting_balance:,.2f} PLN",
            f"Kapital koncowy strategii: {result.final_balance:,.2f} PLN",
            f"Kapital koncowy S&P 500: {result.buy_and_hold_balance:,.2f} PLN",
            f"Transakcje: {result.transaction_count}",
            f"Sukces: {result.success_pct:.2f}%",
            f"Przegrane: {result.failed_pct:.2f}%",
        ]
    )


def format_optimization_summary(results: list[FourEmaResult], top: int) -> str:
    rows = [
        "Top parametry wedlug kapitalu koncowego:",
        "short medium long very_long kapital PLN transakcje sukces przegrane",
    ]

    for result in results[:top]:
        rows.append(
            " ".join(
                [
                    f"{result.short_window:>5}",
                    f"{result.medium_window:>6}",
                    f"{result.long_window:>4}",
                    f"{result.very_long_window:>9}",
                    f"{result.final_balance:>12,.2f}",
                    f"{result.transaction_count:>10}",
                    f"{result.success_pct:>6.2f}%",
                    f"{result.failed_pct:>8.2f}%",
                ]
            )
        )

    return "\n".join(rows)


def render_four_ema_chart(
    result: FourEmaResult,
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
        label=f"4 EMA {result.windows_label}",
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

    ax.set_title(f"{symbol.upper()} - S&P 500 vs 4 EMA")
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


def render_four_ema_comparison_chart(
    results: list[FourEmaResult],
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
            label = f"EMA {result.windows_label} ({result.final_balance:,.0f} PLN)"

        ax.plot(
            result.frame["date"],
            result.frame["portfolio_balance"],
            color=colors(index % 20),
            linewidth=1.7 if is_highlighted else 0.7,
            alpha=0.95 if is_highlighted else 0.18,
            label=label,
            zorder=3 if is_highlighted else 2,
        )

    ax.set_title(f"{symbol.upper()} - porownanie parametrow 4 EMA")
    ax.set_xlabel("Data")
    ax.set_ylabel("Wartosc portfela [PLN]")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.0f}"))
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper left", fontsize=9)
    ax.text(
        0.02,
        0.36,
        f"Liczba wariantow: {len(results)}\nNajlepszy: EMA {best.windows_label}\nKapital: {best.final_balance:,.2f} PLN",
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
