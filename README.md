# 2026 FIFA World Cup Probabilistic Forecasting Engine

Phase 1 professional baseline for the DataCamp FIFA World Cup 2026 prediction competition.

## What this version does

- Loads the DataCamp `group_fixtures.csv` and `knockout_slots.csv`
- Uses a curated prior strength table as an Elo-style baseline
- Generates probabilistic scorelines with a Poisson model
- Simulates group standings and resolves knockout slots
- Predicts all 104 matches
- Outputs DataCamp-ready CSV files

## Run

```bash
pip install -r requirements.txt
python main.py
```

Outputs are written to `data/predictions/`:

- `group_predictions.csv`
- `knockout_predictions.csv`
- `all_predictions.csv`
- `team_strength_priors.csv`
- `tournament_summary.csv`

## Why this is only Phase 1

This is a working baseline engine. Next phases should add:

- Historical match result ingestion
- True dynamic Elo updates
- Dixon-Coles / bivariate Poisson
- LightGBM/XGBoost outcome models
- Odds calibration
- Player availability / injury / squad intelligence
- MLflow experiment tracking
- Delta Lake snapshots
