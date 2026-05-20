from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Final

import pandas as pd

DEFAULT_SYMBOL: Final[str] = "sp500"
DEFAULT_TICKER: Final[str] = "^GSPC"
DEFAULT_START_DATE: Final[str] = "2016-01-01"
DEFAULT_DATA_DIR: Final[Path] = Path("data")


def _normalize_column_name(column: object) -> str:
    if isinstance(column, str):
        text = column.strip()
        if text.startswith("(") and text.endswith(")"):
            try:
                parsed = ast.literal_eval(text)
            except (SyntaxError, ValueError):
                pass
            else:
                column = parsed
        else:
            column = text

    if isinstance(column, tuple):
        parts = [str(part) for part in column if part not in ("", None)]
        column = parts[0] if parts else ""

    text = str(column).strip().lower()

    if text in {"date", "open", "high", "low", "close", "volume"}:
        return text
    if text in {"adj close", "adj_close"}:
        return "adj_close"

    text = text.replace("_", " ")
    words = re.findall(r"[a-z]+", text)
    if not words:
        return str(column).strip().lower().replace(" ", "_")
    if words[0] == "adj" and len(words) > 1 and words[1] == "close":
        return "adj_close"
    return words[0]


def normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame.columns = [_normalize_column_name(column) for column in frame.columns]
    return frame


def _symbol_stem(symbol: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", symbol.strip().lower()).strip("_")


def _symbol_to_ticker(symbol: str) -> str:
    if symbol != DEFAULT_SYMBOL:
        raise ValueError(f"Unsupported symbol {symbol!r}. Only {DEFAULT_SYMBOL!r} is supported.")
    return DEFAULT_TICKER


def default_parquet_path(symbol: str) -> Path:
    return DEFAULT_DATA_DIR / f"{_symbol_stem(symbol)}.parquet"


def default_chart_path(symbol: str) -> Path:
    return DEFAULT_DATA_DIR / f"{_symbol_stem(symbol)}.png"


def download_symbol_history(
    symbol: str,
    start_date: str = DEFAULT_START_DATE,
) -> pd.DataFrame:
    import yfinance as yf

    data = yf.download(
        _symbol_to_ticker(symbol),
        start=start_date,
        auto_adjust=True,
        progress=False,
    )

    if data.empty:
        raise RuntimeError(f"No data returned for symbol {symbol!r}.")

    return normalize_columns(data.reset_index())


def save_to_parquet(frame: pd.DataFrame, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    normalize_columns(frame).to_parquet(output_path, index=False)
    return output_path


def load_symbol_data(
    symbol: str,
    parquet_path: Path | None = None,
    start_date: str = DEFAULT_START_DATE,
) -> pd.DataFrame:
    path = parquet_path or default_parquet_path(symbol)

    try:
        frame = pd.read_parquet(path)
    except Exception:
        frame = download_symbol_history(symbol, start_date)
        save_to_parquet(frame, path)

    frame = normalize_columns(frame)

    if "date" in frame.columns:
        frame["date"] = pd.to_datetime(frame["date"])
    return frame
