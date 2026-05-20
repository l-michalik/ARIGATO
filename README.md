# ARIGATO

Pobieranie danych indeksu S&P 500 z Yahoo Finance od `2016-01-01` i zapis do Parquet.

## Użycie

```bash
uv run arigato-download-sp500
uv run arigato-sp500-chart
uv run arigato-sp500-chart --strategy close-sma50
```

Domyślnie dane trafiają do `data/sp500.parquet`.
Wykres trafia do `data/sp500.png`.
Możesz zmieniać strategię wykresu przez `--strategy`; dostępne obecnie: `close-line`, `close-sma50`.
