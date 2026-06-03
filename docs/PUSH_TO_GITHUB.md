# Push dashboard to GitHub (for Streamlit Cloud)

Remote: `https://github.com/LinLyra/fifa-world-cup-2026-prediction-system.git`

## 1. Check files are trackable

```bash
cd "/Users/lynnlong/Library/Mobile Documents/com~apple~CloudDocs/dev/worldcup_2026_prediction_engine"

git check-ignore -v data/predictions/world_cup_champion_probabilities_v2.csv
# Should print nothing (file is NOT ignored)
```

## 2. Stage deploy files

```bash
git add requirements.txt .gitignore .streamlit/
git add src/dashboard/
git add docs/DEPLOY_PUBLIC_AND_ANALYTICS.md docs/PUSH_TO_GITHUB.md

git add data/predictions/world_cup_champion_probabilities_v2.csv
git add data/predictions/group_stage_simulation_v3_summary.csv
git add data/predictions/match_strength_matrix_v2.csv
git add data/predictions/world_cup_brackets_v1.csv
git add data/predictions/path_difficulty_v1.csv
git add data/features/team_intelligence_v2.csv
git add data/intelligence/final_match_intelligence_v1.csv
git add data/raw/group_fixtures_final.csv

git status
```

Confirm you see the 8 CSV paths under “Changes to be committed” (~45 MB total).

## 3. Commit

```bash
git commit -m "$(cat <<'EOF'
Add Streamlit dashboard and prediction outputs for public deploy.

Includes calibrated V2 sim outputs and whitelisted data CSVs for Streamlit Cloud.
EOF
)"
```

## 4. Push

```bash
git push origin main
```

First push of large files may take a few minutes.

## 5. Streamlit Cloud

1. https://share.streamlit.io → Sign in with GitHub  
2. **New app** → repo `fifa-world-cup-2026-prediction-system`  
3. **Main file:** `src/dashboard/app.py`  
4. Deploy → copy `https://….streamlit.app`  
5. **Analytics** tab for visitor counts  

Optional Secrets:

```toml
PLAUSIBLE_DOMAIN = "your-app-name.streamlit.app"
```

## Do not commit

- `.streamlit/secrets.toml` (real keys)
- `site_deploy/` (local copy only)
- `.env`
