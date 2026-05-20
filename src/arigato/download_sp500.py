from __future__ import annotations

from pathlib import Path
from typing import Final

import pandas as pd
import yfinance as yf

DEFAULT_TICKER: Final[str] = "^GSPC"
DEFAULT_START_DATE: Final[str] = "2016-01-01"
DEFAULT_OUTPUT_PATH: Final[Path] = Path("data") / "sp500.parquet"


def download_sp500_history(
    ticker: str = DEFAULT_TICKER,
    start_date: str = DEFAULT_START_DATE,
) -> pd.DataFrame:
    data = yf.download(
        ticker,
        start=start_date,
        auto_adjust=True,
        progress=False,
    )

    if data.empty:
        raise RuntimeError(f"No data returned for ticker {ticker!r}.")

    data = data.reset_index()
    data.columns = [str(column).lower().replace(" ", "_") for column in data.columns]
    return data


def save_to_parquet(frame: pd.DataFrame, output_path: Path = DEFAULT_OUTPUT_PATH) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output_path, index=False)
    return output_path


def main() -> None:
    frame = download_sp500_history()
    output_path = save_to_parquet(frame)
    print(f"Saved {len(frame)} rows to {output_path}")

