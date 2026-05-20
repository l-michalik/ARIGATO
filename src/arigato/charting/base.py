from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ChartContext:
    frame: pd.DataFrame
    date_column: str
    value_column: str
