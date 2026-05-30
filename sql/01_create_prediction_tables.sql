CREATE TABLE IF NOT EXISTS group_fixtures (
    match_id INTEGER PRIMARY KEY,
    group_name VARCHAR,
    home_team VARCHAR,
    away_team VARCHAR,
    date_utc TIMESTAMP,
    venue VARCHAR
);

CREATE TABLE IF NOT EXISTS team_strength_priors (
    team VARCHAR PRIMARY KEY,
    rating DOUBLE,
    rating_source VARCHAR
);

CREATE TABLE IF NOT EXISTS group_predictions (
    match_id INTEGER PRIMARY KEY,
    predicted_home_goals INTEGER,
    predicted_away_goals INTEGER,
    corners INTEGER,
    yellow_cards INTEGER,
    red_cards INTEGER,
    winning_team VARCHAR
);
