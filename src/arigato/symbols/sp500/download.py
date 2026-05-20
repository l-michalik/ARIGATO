from __future__ import annotations

from arigato.symbols.sp500.data import download_sp500_history, save_to_parquet


def main() -> None:
    frame = download_sp500_history()
    output_path = save_to_parquet(frame)
    print(f"Saved {len(frame)} rows to {output_path}")
