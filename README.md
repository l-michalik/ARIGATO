# ARIGATO

Pobieranie danych indeksu S&P 500 z Yahoo Finance od `2016-01-01` i zapis do Parquet.

## Użycie

```bash
uv run fetch sp500
uv run chart sp500
```

Domyślnie dane trafiają do `data/sp500.parquet`.
Wykres trafia do `data/sp500.png`.
