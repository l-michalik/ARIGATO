# ARIGATO

Pobieranie danych indeksu S&P 500 z Yahoo Finance od `2016-01-01` i zapis do Parquet.

## Użycie

```bash
uv run arigato-download-sp500
uv run arigato-sp500-chart
```

Domyślnie dane trafiają do `data/sp500.parquet`.
Wykres trafia do `data/sp500.png`.
