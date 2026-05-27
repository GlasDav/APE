# easyauto123 Inventory Tracker

This repository tracks the number of used cars listed on:

- https://easyauto123.com.au/buy/used-cars?page=1&limit=20

The parser looks for text matching:

- `#### used cars for sale`

## Historical backfill (Wayback Machine)

Run:

```bash
python scripts/fetch_inventory.py
```

The script attempts to:

1. Query Wayback CDX for historical snapshots.
2. Parse historical inventory values.
3. Fetch today's live page and append today's inventory.
4. Save output to:
   - `data/inventory.csv`
   - `data/inventory.json`

## Weekly automation

GitHub Actions workflow:

- `.github/workflows/inventory-tracker.yml`

Runs every Monday (UTC), updates the data files, and commits changes.

## GitHub Pages chart

`index.html` renders a line chart from `data/inventory.json`.

Enable GitHub Pages from the repository root branch, then open the Pages URL to view the chart.
