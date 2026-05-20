# ARIGATO

Pobieranie danych indeksu S&P 500 z Yahoo Finance od `2016-01-01` i zapis do Parquet.

## Użycie

```bash
uv run fetch sp500
uv run chart sp500
uv run following sp500
uv run following sp500 --top 10
```

Domyślnie dane trafiają do `database/sp500/data.parquet`.
Wykres trafia do `results/sp500/chart.png`.

Strategia `following` skanuje domyślnie okna `5 10 13 15 20 25 30` dla szybkiej SMA oraz `40 50 75 100 150 200` dla wolnej SMA, sortuje warianty według końcowego kapitału i zapisuje jeden wykres do `results/sp500/strategies/following.png`. Na tym samym wykresie widać linię buy-and-hold S&P 500 oraz `10` najlepszych wariantów strategii startujących od `100000` PLN.

Własną siatkę można przekazać przez `--fast-windows` i `--slow-windows`, np.:

```bash
uv run following sp500 --fast-windows 5 10 13 20 --slow-windows 50 100 150 200 --top 5
```
