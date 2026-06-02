import time
import pandas as pd
import streamlit as st

from src.data_loader import load_datasets, build_lookups
from src.prediction import predict_match, get_h2h_score
from src.tournament import simulate_tournament
from src.styling import (
    apply_global_styles,
    team_label,
    format_probability,
)


st.set_page_config(
    page_title="World Cup 2026 Predictor",
    page_icon="⚽",
    layout="wide",
)

apply_global_styles()

data = load_datasets()
lookups = build_lookups()

df_probs = data["probabilities"]
df_groups = data["groups"]

team_to_elo = lookups["team_to_elo"]
team_to_form = lookups["team_to_form"]
team_to_fifa_rank = lookups["team_to_fifa_rank"]
team_to_fifa_rank_change = lookups["team_to_fifa_rank_change"]


def show_header():
    st.markdown(
        """
        <div class="main-title">⚽ World Cup 2026 Predictor</div>
        <div class="sub-title">
        Poisson goal model + Monte Carlo simulation + interactive tournament demo.
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_probability_table(df):
    """Format probability columns for display."""

    display_df = df.copy()

    probability_cols = [
        "r32_prob",
        "r16_prob",
        "qf_prob",
        "sf_prob",
        "final_prob",
        "winner_prob",
    ]

    for col in probability_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].map(lambda x: f"{x * 100:.1f}%")

    if "team" in display_df.columns:
        display_df["team"] = display_df["team"].apply(team_label)

    return display_df


def page_probabilities():
    show_header()

    st.subheader("🏆 Precomputed tournament probabilities")

    st.write(
        "This page loads the saved Monte Carlo results from CSV, so it is fast."
    )

    col1, col2, col3 = st.columns(3)

    top_team = df_probs.sort_values("winner_prob", ascending=False).iloc[0]

    with col1:
        st.metric("Most likely winner", team_label(top_team["team"]))

    with col2:
        st.metric("Win probability", format_probability(top_team["winner_prob"]))

    with col3:
        st.metric("FIFA rank", int(top_team["fifa_rank"]))

    st.markdown("### Top winner probabilities")

    top_n = st.slider("How many teams to show?", min_value=5, max_value=48, value=15)

    chart_df = (
        df_probs
        .sort_values("winner_prob", ascending=False)
        .head(top_n)
        .copy()
    )

    chart_df["team_label"] = chart_df["team"].apply(team_label)

    st.bar_chart(
        chart_df.set_index("team_label")["winner_prob"]
    )

    st.markdown("### Full probability table")

    table_cols = [
        "team",
        "confederation",
        "fifa_rank",
        "rank_change",
        "elo",
        "form_score",
        "r32_prob",
        "r16_prob",
        "qf_prob",
        "sf_prob",
        "final_prob",
        "winner_prob",
    ]

    st.dataframe(
        style_probability_table(df_probs[table_cols]),
        use_container_width=True,
        height=620,
    )


def render_group_table(group_table):
    """Render a group table with top 2 highlighted."""

    table = group_table.copy()
    table["team"] = table["team"].apply(team_label)

    display_cols = [
        "group_rank",
        "team",
        "played",
        "wins",
        "draws",
        "losses",
        "goals_for",
        "goals_against",
        "goal_difference",
        "points",
    ]

    def highlight_qualified(row):
        if row["group_rank"] <= 2:
            return ["background-color: rgba(48, 209, 88, 0.25); color: white;"] * len(row)
        if row["group_rank"] == 3:
            return ["background-color: rgba(255, 214, 10, 0.18); color: white;"] * len(row)
        return [""] * len(row)

    styled = table[display_cols].style.apply(highlight_qualified, axis=1)

    st.dataframe(styled, use_container_width=True, hide_index=True)


def page_live_simulation():
    show_header()

    st.subheader("🎮 Live tournament simulation")

    st.write(
        "Click the button below to simulate one full World Cup path from groups to final."
    )

    run_button = st.button("▶️ Run one full tournament simulation", type="primary")

    if run_button:
        with st.spinner("Simulating tournament..."):
            tournament = simulate_tournament()

        summary = tournament["summary"]
        group_tables = tournament["group_tables"]
        group_matches = tournament["group_matches"]
        knockout_results = tournament["knockout_results"]

        st.markdown("## Group stage")

        for group_name in sorted(group_tables["group"].unique()):
            st.markdown(f"### Group {group_name}")

            group_matches_view = group_matches[
                group_matches["home_team"].isin(
                    group_tables[group_tables["group"] == group_name]["team"]
                )
            ].copy()

            for _, match in group_matches_view.iterrows():
                st.write(
                    f"{team_label(match['home_team'])} "
                    f"**{match['home_goals']} - {match['away_goals']}** "
                    f"{team_label(match['away_team'])}"
                )
                time.sleep(0.08)

            group_table = group_tables[group_tables["group"] == group_name]
            render_group_table(group_table)

        st.markdown("## Knockout stage")

        for round_name in ["R32", "R16", "QF", "SF", "Final"]:
            round_results = knockout_results[knockout_results["round"] == round_name]

            st.markdown(f'<div class="round-title">{round_name}</div>', unsafe_allow_html=True)

            cols = st.columns(2)

            for idx, (_, match) in enumerate(round_results.iterrows()):
                with cols[idx % 2]:
                    st.markdown(
                        f"""
                        <div class="team-card">
                            {team_label(match['home_team'])} 
                            <strong>{match['home_goals']} - {match['away_goals']}</strong> 
                            {team_label(match['away_team'])}
                            <br>
                            <span class="small-muted">
                            Winner: {team_label(match['winner'])}
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    time.sleep(0.08)

        st.markdown(
            f"""
            <div class="winner-card">
                🏆 Winner: {team_label(summary["winner"])} 🏆
                <br>
                <span style="font-size:18px;">Runner-up: {team_label(summary["runner_up"])}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.balloons()


def page_match_explorer():
    show_header()

    st.subheader("🔎 Match explorer")

    teams = sorted(df_groups["nation"].unique())

    col1, col2 = st.columns(2)

    with col1:
        home_team = st.selectbox("Team A", teams, index=teams.index("Argentina") if "Argentina" in teams else 0)

    with col2:
        away_team = st.selectbox("Team B", teams, index=teams.index("Brazil") if "Brazil" in teams else 1)

    if home_team == away_team:
        st.warning("Please select two different teams.")
        return

    pred = predict_match(home_team, away_team)

    st.markdown("### Model probabilities")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(f"{team_label(home_team)} xG", f"{pred['home_xg']:.2f}")

    with col2:
        st.metric(f"{team_label(away_team)} xG", f"{pred['away_xg']:.2f}")

    with col3:
        st.metric("Team A win", format_probability(pred["home_win_prob"]))

    with col4:
        st.metric("Draw", format_probability(pred["draw_prob"]))

    with col5:
        st.metric("Team B win", format_probability(pred["away_win_prob"]))

    st.markdown("### Most likely scorelines")

    scorelines = (
        pred["score_probs"]
        .sort_values("probability", ascending=False)
        .head(10)
        .copy()
    )

    scorelines["scoreline"] = (
        scorelines["home_goals"].astype(str)
        + " - "
        + scorelines["away_goals"].astype(str)
    )

    scorelines["probability"] = scorelines["probability"].map(lambda x: f"{x * 100:.1f}%")

    st.dataframe(
        scorelines[["scoreline", "probability"]],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Team context")

    context_data = pd.DataFrame([
        {
            "team": team_label(home_team),
            "elo": team_to_elo.get(home_team),
            "fifa_rank": team_to_fifa_rank.get(home_team),
            "rank_change": team_to_fifa_rank_change.get(home_team),
            "form_score": team_to_form.get(home_team),
            "h2h_score_vs_opponent": get_h2h_score(home_team, away_team),
        },
        {
            "team": team_label(away_team),
            "elo": team_to_elo.get(away_team),
            "fifa_rank": team_to_fifa_rank.get(away_team),
            "rank_change": team_to_fifa_rank_change.get(away_team),
            "form_score": team_to_form.get(away_team),
            "h2h_score_vs_opponent": get_h2h_score(away_team, home_team),
        },
    ])

    st.dataframe(context_data, use_container_width=True, hide_index=True)


def main():
    page = st.sidebar.radio(
        "Choose page",
        [
            "🏆 Precomputed probabilities",
            "🎮 Live simulation",
            "🔎 Match explorer",
        ],
    )

    if page == "🏆 Precomputed probabilities":
        page_probabilities()

    elif page == "🎮 Live simulation":
        page_live_simulation()

    elif page == "🔎 Match explorer":
        page_match_explorer()


if __name__ == "__main__":
    main()