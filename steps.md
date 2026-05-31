# World Cup 2026 ML Project — Feature Engineering Steps

## Starting data
- `df_games` (49,287 × 9) — all international matches 1872–2026
- `df_ranking` (48 × 4) — qualified teams + FIFA rank 2022, 2026, change
- `df_group_stage` (48 × 3) — group assignments
- `df_knockout_fixtures` (32 × 8) — bracket structure

---

## Step 1 — Elo ratings

**Goal:** compute each team's Elo strength at every point in history, joinable to any match.

**Inputs:** `df_games`

**Process:**
1. use historical_matches.csv (this one excludes WC2026 upcoming fixtures)
2. Sort by date ascending.
3. Initialize every team at Elo = 1500.
4. Walk through matches in order. For each match:
   - Look up both teams' current Elo.
   - Compute expected score for home team.
   - Compute actual score (1 = win, 0.5 = draw, 0 = loss).
   - Update both teams: `new_elo = old_elo + K × (actual − expected)`.
   - Use K = 30 for friendlies, 40 for qualifiers, 60 for World Cup matches.
   - Record both teams' Elo *after* the match into a log.

**Output:** `df_elo` — columns: `date`, `team`, `elo_after`.

**Sanity check before moving on:**
- Top 10 teams by current Elo should look roughly sensible (France, Spain, Argentina, Brazil, etc., in some order).
- No team should be missing.
- Plot Brazil's Elo over time — should be smooth, no wild spikes.

---

## Step 2 — Match-level metadata

**Goal:** enrich `df_match_features` (Elo already attached from Step 1) with
the remaining features needed for model training.

**Inputs:** `df_match_features.csv` from Step 1, `FIFA_confederations.csv`
from `data/reference/`.

**Process — in order of increasing complexity:**

1. **`tournament_weight`** — map tournament name to 1-5 using the same
   tier system as the Elo K-factor (World Cup=5, Continental=4, etc.).
2. **`is_competitive`** — boolean: True if tournament != 'Friendly'.
3. **Confederation merge** — join `FIFA_confederations.csv` twice to get
   `home_confederation` and `away_confederation`.
4. **`home_recent_gd_10`** / **`away_recent_gd_10`** — for each team, sum
   of (goals_for − goals_against) over their previous 10 matches before
   this match date. Must use only *prior* matches (no leakage).
5. **`h2h_home_advantage`** — for the (home_team, away_team) pair, count
   of home wins minus away wins in their last 5 prior meetings.

**Output:** updated `df_match_features.csv` (overwrites Step 1 version).

**Sanity checks:**
- Row count unchanged (still 49,048).
- `tournament_weight` distribution: bulk of matches should sit in weights 1-3.
- `home_confederation` / `away_confederation` have no NaN for the 48 WC2026 teams.
- `home_recent_gd_10` should be NaN only for very early matches in each team's
  history (where they haven't played 10 prior games yet) — fill with 0.
- `h2h_home_advantage` will be NaN for first meetings — fill with 0.

---

## Step 3 — Confederation lookup

**Goal:** add the team-to-confederation mapping as a categorical feature.

**Inputs:** none — built by hand from FIFA's official assignments.

**Process:**
1. Create a CSV: `df_confederations.csv` with two columns — `nation`, `confederation`.
2. Six valid values: `UEFA`, `CONMEBOL`, `CAF`, `AFC`, `CONCACAF`, `OFC`.
3. Match `nation` spellings to `df_games.home_team` / `df_group_stage.nation`.
4. Cover every team in `df_group_stage` at minimum (48 teams).
5. Ideally cover every team in `df_games` (~330 unique names) so historical matches also get the feature.

**Output:** `df_confederations.csv`.

**Sanity check before moving on:**
- All 48 qualified teams have a confederation assigned.
- No typos: `set(df_confederations['confederation']) ⊆ {UEFA, CONMEBOL, CAF, AFC, CONCACAF, OFC}`.
- Counts roughly match reality: UEFA ~55, CAF ~55, AFC ~46, CONCACAF ~35, CONMEBOL = 10, OFC ~11.

---

## Final assembly

Once steps 1–3 are done, join everything into a single training table:
df_train = df_match_features
.merge(df_confederations, left_on='home_team', right_on='nation')
.merge(df_confederations, left_on='away_team', right_on='nation', suffixes=('_home', '_away'))

This is what feeds the model.

---

## Notes

- Skip fatigue features for v1. Reconsider only for the tournament-specific layer if there's time.
- Use Elo for training; treat FIFA rank as a 2026-only sanity check, not a training feature (avoids time-leakage).
- Don't bring in any new raw datasets at this stage. Build features from what you have.