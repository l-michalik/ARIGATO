from __future__ import annotations

from dataclasses import dataclass

from arigato.charting.base import ChartContext, register_strategy


@dataclass(frozen=True)
class CloseLineStrategy:
    name: str = "close-line"
    title: str = "S&P 500 close since 2016"
    xlabel: str = "Date"
    ylabel: str = "Close"
    color: str = "#0f766e"
    linewidth: float = 1.4

    def render(self, ax, context: ChartContext) -> None:
        ax.plot(
            context.frame[context.date_column],
            context.frame[context.value_column],
            color=self.color,
            linewidth=self.linewidth,
        )


@dataclass(frozen=True)
class CloseWithSmaStrategy:
    window: int = 50
    name: str = "close-sma50"
    title: str = "S&P 500 close with 50-day SMA"
    xlabel: str = "Date"
    ylabel: str = "Close"
    close_color: str = "#155e75"
    sma_color: str = "#ea580c"
    close_linewidth: float = 1.2
    sma_linewidth: float = 1.5

    def render(self, ax, context: ChartContext) -> None:
        close = context.frame[context.value_column]
        sma = close.rolling(self.window).mean()

        ax.plot(
            context.frame[context.date_column],
            close,
            color=self.close_color,
            linewidth=self.close_linewidth,
            label="Close",
        )
        ax.plot(
            context.frame[context.date_column],
            sma,
            color=self.sma_color,
            linewidth=self.sma_linewidth,
            label=f"{self.window}-day SMA",
        )
        ax.legend(frameon=False)


def register_sp500_strategies() -> None:
    register_strategy(CloseLineStrategy())
    register_strategy(CloseWithSmaStrategy())
