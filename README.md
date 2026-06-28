# 2026 FIFA World Cup Probabilistic Forecasting Engine

A football intelligence and forecasting platform for the 2026 FIFA World Cup.

🔗 https://fifa-world-cup-2026-prediction-syst.vercel.app/

Built on 49,000+ historical international matches, the engine combines team strength modelling, probabilistic score prediction, pre-match intelligence, and 20,000+ Monte Carlo simulations to estimate match outcomes, tournament paths, and championship probabilities.

## What it does

- Learns from a century-plus of international football data
- Builds team intelligence with Elo, attack/defense, form, squad value, and market signals
- Predicts match scorelines with Poisson and Dixon-Coles modelling
- Incorporates squad availability, tactical profile, odds drift, and motivation signals
- Simulates the full 2026 World Cup structure from group stage to final
- Outputs group, knockout, and champion probabilities
- Includes 2022 backtesting and version comparison scripts

## Core layers

### Historical Data

The model is trained on 49,000+ international matches across World Cup, qualifiers, continental tournaments, and friendlies.

### Team Intelligence

Each national team is represented through a multi-factor strength profile:

- Elo rating
- Attack and defense ratings
- Recent form
- Transfermarkt squad value
- Betting market and ranking signals

### Match Forecasting

Single matches are forecast with Poisson goal modelling and Dixon-Coles low-score correction, producing expected goals, score matrices, and win/draw/loss probabilities.

### Pre-Match Intelligence

The final match layer can absorb squad availability, injuries, suspensions, tactical style, market drift, and competitive context before simulation.

### Tournament Simulation

The engine runs 20,000+ Monte Carlo simulations of the full World Cup bracket to estimate advancement probabilities and title chances.

## Outputs

- `group_predictions.csv`
- `knockout_predictions.csv`
- `all_predictions.csv`
- `team_strength_priors.csv`
- `tournament_summary.csv`
- `match_strength_matrix_v2.csv`
- `world_cup_champion_probabilities_v2.csv`
- `final_match_intelligence_v1.csv`

## Evaluation

Backtesting scripts are included for the 2022 FIFA World Cup:

- `src/evaluation/backtest_2022_single_matches.py`
- `src/evaluation/backtest_2022_champion_ranking.py`
- `src/evaluation/backtest_2022_engine_versions.py`

## Run

```bash
pip install -r requirements.txt
python main.py
