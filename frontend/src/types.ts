export type ChampionRow = {
  team: string;
  champion_prob: number;
  titles: number;
};

export type GroupRow = {
  team: string;
  group_winner_prob: number;
  group_top2_prob: number;
  advance_prob: number;
};

export type IntelligenceRow = {
  team: string;
  elo: number;
  market_value_eur: number;
  market_champion_prob: number;
  intelligence_score_v2: number;
  attack_rating: number;
  defense_rating: number;
};

export type PathDifficultyRow = {
  team: string;
  expected_path_difficulty: number;
  path_difficulty_percentile?: number;
  path_efficiency?: number;
  champion_prob?: number;
};

export type MatchMatrixRow = {
  home_team: string;
  away_team: string;
  expected_home_goals: number;
  expected_away_goals: number;
  home_win_prob: number;
  draw_prob: number;
  away_win_prob: number;
  pred_home_score: number;
  pred_away_score: number;
  score_probability: number;
  top_5_scorelines: string;
};

export type FinalIntelRow = {
  home_team: string;
  away_team: string;
  final_home_xg: number;
  final_away_xg: number;
  injury_effect?: number;
  squad_effect?: number;
  upset_effect?: number;
  odds_effect?: number;
};

export type ReachProbRow = {
  team: string;
  reach_r32: number;
  reach_r16: number;
  reach_qf: number;
  reach_sf: number;
  reach_final: number;
  reach_win: number;
};

export type FixtureRow = {
  match_id: number;
  group: string;
  home_team: string;
  away_team: string;
};

export type Meta = {
  engine: string;
  simulations: number;
  historical_matches: string;
  team_count: number;
};

export type BracketMatch = {
  match_id: number;
  round: string;
  side: string;
  home: string;
  away: string;
  winner: string;
  p_home: number;
  p_away: number;
  x: number;
  y: number;
};

export type BracketLink = {
  to: number;
  from_a: number;
  from_b: number;
};

export type BracketData = {
  matches: BracketMatch[];
  links: BracketLink[];
  champion_probs: Record<string, number>;
  path_difficulty: Record<string, number>;
  flags?: Record<string, string>;
};

export type DashboardData = {
  meta: Meta;
  champions: ChampionRow[];
  groups: GroupRow[];
  fixtures: FixtureRow[];
  intelligence: IntelligenceRow[];
  pathDifficulty: PathDifficultyRow[];
  matchMatrix: MatchMatrixRow[];
  finalIntel: FinalIntelRow[];
  reachProbs: ReachProbRow[];
  bracket: BracketData;
};
