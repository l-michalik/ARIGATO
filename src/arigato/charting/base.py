from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import pandas as pd


@dataclass(frozen=True)
class ChartContext:
    frame: pd.DataFrame
    date_column: str
    value_column: str


class ChartStrategy(Protocol):
    name: str
    title: str
    xlabel: str
    ylabel: str

    def render(self, ax: Any, context: ChartContext) -> None: ...


_STRATEGIES: dict[str, ChartStrategy] = {}


def register_strategy(strategy: ChartStrategy) -> ChartStrategy:
    _STRATEGIES[strategy.name] = strategy
    return strategy


def get_strategy(name: str) -> ChartStrategy:
    try:
        return _STRATEGIES[name]
    except KeyError as error:
        available = ", ".join(available_strategies())
        raise KeyError(f"Unknown chart strategy {name!r}. Available strategies: {available}.") from error


def available_strategies() -> tuple[str, ...]:
    return tuple(sorted(_STRATEGIES))
