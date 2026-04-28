import streamlit as st
import sqlitecloud
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
CONN_STR = "sqlitecloud://cgllukzpvk.g1.sqlite.cloud:8860/team7_sportsleague.db?apikey=n2FaqEbp5bd9b9M1k5a9raf0kzV1ZALaepJqjMynwSA"

st.set_page_config(
    page_title="Team 7 — Sports Analytics",
    page_icon="🏈",
    layout="wide"
)

# ─────────────────────────────────────────────
# SHARED HELPER FUNCTIONS
# ─────────────────────────────────────────────

@st.cache_data
def extract(table_name):
    """Connect to DB and load one raw table as a dataframe."""
    conn = sqlitecloud.connect(CONN_STR)
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df

def transform(df):
    """Clean and standardise any raw dataframe loaded from the database."""
    df = df.copy()
    df = df.drop_duplicates()
    for col in df.columns:
        if "date" in col.lower() or col.lower() in ["dob", "injury_date", "expected_return", "match_date", "transfer_date"]:
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce")
            except:
                pass
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()
    for col in ["conference", "division", "severity", "transfer_type", "status"]:
        if col in df.columns:
            df[col] = df[col].str.upper()
    return df

# ─────────────────────────────────────────────
# AGGREGATE FUNCTIONS
# ─────────────────────────────────────────────

@st.cache_data
def aggregate_injury_vs_wins():
    injuries  = transform(extract("injuries"))
    teams     = transform(extract("teams"))
    standings = transform(extract("standings"))
    standings["win_pct"] = (
        standings["wins"] /
        (standings["wins"] + standings["losses"] + standings["draws"]) * 100
    ).round(1)
    standings_avg = standings.groupby("team_id")["win_pct"].mean().reset_index()
    standings_avg.columns = ["team_id", "avg_win_pct"]
    df = injuries.merge(teams[["team_id", "name"]], on="team_id")
    df = df.merge(standings_avg, on="team_id")
    df = df.rename(columns={"name": "team_name"})
    analytical = df.groupby(["team_name", "severity", "avg_win_pct"]).agg(
        total_games_missed=("games_missed", "sum"),
        total_injuries=("injury_id", "count")
    ).reset_index()
    analytical["win_rank"] = analytical["avg_win_pct"] \
                               .rank(ascending=False, method="dense").astype(int)
    return analytical

@st.cache_data
def aggregate_win_pct():
    teams     = transform(extract("teams"))
    standings = transform(extract("standings"))
    injuries  = transform(extract("injuries"))
    mem = sqlite3.connect(":memory:")
    teams.to_sql("teams",         mem, index=False, if_exists="replace")
    standings.to_sql("standings", mem, index=False, if_exists="replace")
    injuries.to_sql("injuries",   mem, index=False, if_exists="replace")
    sql = """
        SELECT
            t.conference,
            t.division,
            ROUND(AVG(st.wins * 100.0 / (st.wins + st.losses + st.draws)), 1) AS avg_win_pct,
            ROUND(AVG(inj.total_games_missed), 1) AS avg_games_missed
        FROM teams t
        JOIN standings st ON t.team_id = st.team_id
        JOIN (
            SELECT team_id, SUM(games_missed) AS total_games_missed
            FROM injuries GROUP BY team_id
        ) inj ON t.team_id = inj.team_id
        GROUP BY t.conference, t.division
        ORDER BY avg_win_pct DESC
    """
    df = pd.read_sql(sql, mem)
    mem.close()
    return df

@st.cache_data
def aggregate_match_environment(matches, stadiums, teams, match_events):
    df = matches[matches["status"] == "COMPLETED"].copy()
    df["home_win"] = (df["home_score"] > df["away_score"]).astype(int)
    df["score_diff"] = df["home_score"] - df["away_score"]
    df = df.merge(stadiums[["stadium_id", "name", "surface", "capacity"]], on="stadium_id", how="left")
    df = df.merge(teams[["team_id", "name", "conference", "division"]],
                  left_on="home_team_id", right_on="team_id", how="left", suffixes=("", "_team"))
    df["attendance_utilization"] = np.where(
        df["capacity"] > 0, df["attendance"] / df["capacity"] * 100, np.nan)
    attacking_types = ["GOAL", "ASSIST", "SHOT", "SHOT ON TARGET"]
    me = match_events.copy()
    me["event_type"] = me["event_type"].astype(str).str.upper().str.strip()
    me = me.merge(matches[["match_id", "home_team_id"]], on="match_id", how="left")
    me_home = me[(me["team_id"] == me["home_team_id"]) & (me["event_type"].isin(attacking_types))].copy()
    attack_summary = me_home.groupby("match_id").agg(home_attacking_events=("event_id", "count")).reset_index()
    df = df.merge(attack_summary, on="match_id", how="left")
    df["home_attacking_events"] = df["home_attacking_events"].fillna(0)
    analytical = df.groupby(["season", "home_team_id", "name_team", "conference", "division", "surface"]).agg(
        total_home_games=("match_id", "count"),
        home_win_pct=("home_win", "mean"),
        avg_score_diff=("score_diff", "mean"),
        avg_attendance=("attendance", "mean"),
        avg_utilization=("attendance_utilization", "mean"),
        avg_home_attacking_events=("home_attacking_events", "mean")
    ).reset_index()
    analytical["home_win_pct"] = analytical["home_win_pct"] * 100
    analytical["attendance_tier"] = pd.qcut(
        analytical["avg_utilization"], q=3,
        labels=["Low Utilization", "Medium Utilization", "High Utilization"], duplicates="drop")
    return analytical

@st.cache_data
def aggregate_stadium_profile(matches, stadiums, teams):
    df = matches[matches["status"] == "COMPLETED"].copy()
    df["home_win"] = (df["home_score"] > df["away_score"]).astype(int)
    df["score_diff"] = df["home_score"] - df["away_score"]
    df = df.merge(stadiums[["stadium_id", "name", "capacity", "surface", "year_opened"]], on="stadium_id", how="left")
    team_stadium = teams[["team_id", "stadium_id", "conference", "division", "name"]].copy()
    team_stadium = team_stadium.rename(columns={"name": "team_name"})
    df = df.merge(team_stadium[["stadium_id", "conference", "division", "team_name"]], on="stadium_id", how="left")
    df["attendance_utilization_match"] = np.where(
        df["capacity"] > 0, df["attendance"] / df["capacity"] * 100, np.nan)
    df["season_num"] = pd.to_numeric(df["season"], errors="coerce")
    df["venue_age"] = df["season_num"] - df["year_opened"]
    analytical = df.groupby(
        ["season", "stadium_id", "name", "conference", "division", "surface", "capacity", "year_opened"]
    ).agg(
        total_games=("match_id", "count"),
        home_win_pct=("home_win", "mean"),
        avg_score_diff=("score_diff", "mean"),
        avg_attendance=("attendance", "mean"),
        avg_utilization=("attendance_utilization_match", "mean"),
        venue_age=("venue_age", "mean")
    ).reset_index()
    analytical["home_win_pct"] = analytical["home_win_pct"] * 100
    analytical["venue_age_tier"] = pd.cut(
        analytical["venue_age"], bins=[-np.inf, 15, 30, np.inf],
        labels=["Newer Venue", "Mid-Age Venue", "Older Venue"])
    return analytical

@st.cache_data
def aggregate_transfer_roi():
    conn = sqlitecloud.connect(CONN_STR)
    query = """
    SELECT
      p.position,
      t.transfer_type,
      COUNT(DISTINCT t.transfer_id) AS total_transfers,
      ROUND(AVG(t.fee), 2) AS avg_transfer_fee,
      ROUND(AVG(p.contract_salary), 2) AS avg_salary,
      ROUND(COUNT(i.injury_id) * 1.0 / NULLIF(COUNT(DISTINCT t.transfer_id), 0),2) AS injuries_per_transfer
    FROM players p
    JOIN transfers t ON p.player_id = t.player_id
    LEFT JOIN injuries i ON p.player_id = i.player_id
    WHERE t.fee >= 0
      AND t.fee IS NOT NULL
      AND t.transfer_type IN ('Free Transfer', 'Permanent', 'Loan', 'Academy Promotion')
    GROUP BY p.position, t.transfer_type
    HAVING AVG(t.fee) IS NOT NULL
    ORDER BY avg_transfer_fee DESC
    """
    cursor = conn.execute(query)
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    return pd.DataFrame(rows, columns=columns)

@st.cache_data
def aggregate_payroll():
    players   = transform(extract("players"))
    standings = transform(extract("standings"))
    df = standings[standings["season"] == "2023"].copy()
    df["win_pct"] = (
        df["wins"] / (df["wins"] + df["losses"] + df["draws"]) * 100
    ).round(1)
    df = df.merge(players[["team_id", "contract_salary"]], on="team_id", how="left")
    df = df.groupby("team_id").agg(
        total_payroll=("contract_salary", "sum"),
        win_pct=("win_pct", "mean")
    ).reset_index()
    teams = transform(extract("teams"))
    df = df.merge(teams[["team_id", "name"]], on="team_id")
    return df

@st.cache_data
def aggregate_roster_age_impact():
    standings = transform(extract("standings"))
    teams     = transform(extract("teams"))
    players   = transform(extract("players"))
    injuries  = transform(extract("injuries"))
    players["age"] = 2023 - players["dob"].dt.year
    players_active = players[(players["is_active"] == 1) & players["dob"].notna()].copy()
    mem = sqlite3.connect(":memory:")
    standings.to_sql("standings",    mem, index=False, if_exists="replace")
    teams.to_sql("teams",            mem, index=False, if_exists="replace")
    players_active.to_sql("players", mem, index=False, if_exists="replace")
    injuries.to_sql("injuries",      mem, index=False, if_exists="replace")
    sql = """
        WITH roster_age AS (
            SELECT team_id,
                   ROUND(AVG(age), 1) AS avg_roster_age,
                   COUNT(player_id)   AS roster_size
            FROM players GROUP BY team_id
        ),
        injury_load AS (
            SELECT team_id,
                   SUM(games_missed) AS total_games_missed,
                   COUNT(injury_id)  AS total_injuries
            FROM injuries GROUP BY team_id
        )
        SELECT
            t.name AS team_name, t.abbreviation, t.conference, t.division,
            s.season, s.points, s.wins, s.losses, s.draws,
            r.avg_roster_age, r.roster_size,
            COALESCE(i.total_games_missed, 0) AS total_games_missed,
            COALESCE(i.total_injuries, 0) AS total_injuries,
            RANK() OVER (PARTITION BY s.season ORDER BY s.points DESC) AS season_rank,
            ROUND(AVG(s.points) OVER (PARTITION BY s.season), 1) AS season_avg_points
        FROM standings s
        JOIN teams t ON s.team_id = t.team_id
        JOIN roster_age r ON r.team_id = t.team_id
        LEFT JOIN injury_load i ON i.team_id = t.team_id
        ORDER BY s.season, s.points DESC
    """
    df = pd.read_sql(sql, mem)
    mem.close()
    return df

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.title("🏈 Team 7 — Sports Analytics Dashboard")
st.markdown("NFL-style league database &nbsp;|&nbsp; 2020–2023 &nbsp;|&nbsp; 8 tables &nbsp;|&nbsp; AD599 Group Project")
st.divider()

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
st.sidebar.title("Navigation")
st.sidebar.markdown("Select a visualization to explore.")

viz = st.sidebar.radio("", [
    "🏠 Overview",
    "Viz 1 — Injury Severity vs Win Rate",
    "Viz 2 — Win % vs Injury Burden",
    "Viz 3 — Match Environment vs Home Advantage",
    "Viz 4 — Stadium Profile vs Home Advantage",
    "Viz 5 — Transfer ROI by Position",
    "Viz 6 — Payroll vs Win %",
    "Viz 7 — Roster Age vs Points",
])

st.sidebar.divider()
st.sidebar.markdown("**Team 7**")
st.sidebar.markdown("Julie · Meera · Sarah · Antara · Simon · Haley")

# ─────────────────────────────────────────────
# OVERVIEW PAGE
# ─────────────────────────────────────────────
if viz == "🏠 Overview":
    st.subheader("Project Overview")
    st.markdown("""
    > *Sports organizations collect vast data across matches, players, injuries, and transfers,
    yet it often goes underutilized. This project analyzes an NFL-style league database across
    8 tables and 4 seasons to uncover what drives team success and failure.*

    **Key finding:** No single factor decides who wins. Roster depth, injury management,
    and team execution matter more than payroll, age, or stadium size.
    """)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Teams", "16")
    col2.metric("Players", "400")
    col3.metric("Matches", "800")
    col4.metric("Seasons", "4 (2020–2023)")

    st.divider()
    st.subheader("Visualizations in this dashboard")
    st.markdown("""
    | # | Title | Tables | Owner |
    |---|---|---|---|
    | 1 | Injury Severity vs Team Win Rate | injuries, standings, teams | Meera |
    | 2 | Win % vs Injury Burden by Division | teams, standings, injuries | Julie |
    | 3 | Match Environment vs Home Advantage | matches, stadiums, teams, match_events | Sarah |
    | 4 | Stadium Profile vs Home Advantage | matches, stadiums, teams | Sarah |
    | 5 | Transfer ROI by Position | players, transfers, injuries | Antara |
    | 6 | Total Payroll vs Win % | players, standings | Haley |
    | 7 | Roster Age vs Points | standings, players, teams, injuries | Simon |
    """)

# ─────────────────────────────────────────────
# VIZ 1
# ─────────────────────────────────────────────
elif viz == "Viz 1 — Injury Severity vs Win Rate":
    st.subheader("Viz 1 — Injury Severity vs Team Win Rate")
    st.markdown("*Does injury burden predict team success?*")
    st.markdown("""
    A heatmap showing total games missed per team broken down by severity (Minor, Moderate, Severe),
    plus a Total column. Teams are sorted from highest to lowest win rate.
    """)

    with st.spinner("Loading data..."):
        df = aggregate_injury_vs_wins()

    heatmap_data = df.pivot_table(
        index="team_name", columns="severity",
        values="total_games_missed", aggfunc="sum"
    ).fillna(0)
    heatmap_data["TOTAL"] = heatmap_data.sum(axis=1)
    team_order = df[["team_name", "avg_win_pct"]].drop_duplicates() \
                   .sort_values("avg_win_pct", ascending=False)["team_name"].tolist()
    heatmap_data = heatmap_data.reindex(team_order)
    win_pcts = df[["team_name", "avg_win_pct"]].drop_duplicates() \
                 .set_index("team_name")["avg_win_pct"].to_dict()
    heatmap_data.index = [
        f"{t}  ({round(win_pcts[t], 1)}% wins)" for t in heatmap_data.index
    ]
    fig = px.imshow(
        heatmap_data,
        color_continuous_scale="Blues",
        text_auto=True, aspect="auto",
        title="Injury Severity Heatmap — Teams Ranked by Win Rate",
        labels={"x": "Injury Severity", "y": "Team", "color": "Games Missed"}
    )
    fig.update_layout(xaxis=dict(side="bottom"), height=600)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    **Key finding:** Injury severity does not predict team success. The Cowboys (78.1% win rate)
    still suffered 101 games missed from severe injuries. Roster depth absorbs injuries
    better than avoiding them.
    """)

# ─────────────────────────────────────────────
# VIZ 2
# ─────────────────────────────────────────────
elif viz == "Viz 2 — Win % vs Injury Burden":
    st.subheader("Viz 2 — Do Heavier Injury Burdens Lead to Lower Win Rates?")
    st.markdown("*Comparing average win % and games missed due to injury by conference and division.*")

    with st.spinner("Loading data..."):
        analytical = aggregate_win_pct()

    analytical["label"] = analytical["conference"] + " " + analytical["division"]

    fig = px.scatter(
        analytical,
        x="avg_win_pct", y="avg_games_missed",
        color="conference", symbol="division", text="label",
        title="Do Heavier Injury Burdens Lead to Lower Win Rates?",
        labels={"avg_win_pct": "Avg Win %", "avg_games_missed": "Avg Games Missed Due to Injury"}
    )

    x = analytical["avg_win_pct"]
    y = analytical["avg_games_missed"]
    m, b = np.polyfit(x, y, 1)
    x_line = np.linspace(x.min(), x.max(), 100)

    fig.add_trace(go.Scatter(
        x=x_line, y=m * x_line + b,
        mode="lines", name="Trend",
        line=dict(color="gray", dash="dash", width=1.5)
    ))
    fig.update_traces(textposition="top center")
    fig.update_layout(height=550)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    **Key finding:** Weak negative correlation — divisions that miss more games to injury
    tend to win less. AFC East has the highest win % and lowest games missed.
    But it's not a perfect pattern — roster depth can override injury burden.
    """)

# ─────────────────────────────────────────────
# VIZ 3
# ─────────────────────────────────────────────
elif viz == "Viz 3 — Match Environment vs Home Advantage":
    st.subheader("Viz 3 — Which Match Environments Drive Home Advantage?")
    st.markdown("*Attendance, surface, or attacking play — what creates home advantage?*")

    with st.spinner("Loading data..."):
        matches     = transform(extract("matches"))
        stadiums    = transform(extract("stadiums"))
        teams       = transform(extract("teams"))
        match_events = transform(extract("match_events"))
        df = aggregate_match_environment(matches, stadiums, teams, match_events)

    conferences = [c for c in df["conference"].dropna().unique()]

    fig = px.scatter(
        df,
        x="avg_utilization", y="home_win_pct",
        size="avg_home_attacking_events", size_max=22,
        color="attendance_tier", symbol="surface",
        facet_col="conference",
        hover_name="name_team",
        hover_data=["season", "division", "surface", "avg_attendance",
                    "avg_score_diff", "total_home_games", "avg_home_attacking_events"],
        title="Which Match Environments Drive Home Advantage: Attendance, Surface, or Attacking Play?",
        labels={"avg_utilization": "Avg Attendance Utilization (%)",
                "home_win_pct": "Home Win %",
                "avg_home_attacking_events": "Avg Home Attacking Events",
                "attendance_tier": "Attendance Tier", "surface": "Surface"}
    )

    for i, conf in enumerate(conferences, start=1):
        sub = df[df["conference"] == conf].dropna(subset=["avg_utilization", "home_win_pct"]).copy()
        if len(sub) >= 2:
            x = sub["avg_utilization"]
            y = sub["home_win_pct"]
            m, b = np.polyfit(x, y, 1)
            x_line = np.linspace(x.min(), x.max(), 100)
            fig.add_trace(go.Scatter(
                x=x_line, y=m * x_line + b, mode="lines",
                name=f"{conf} Trend", line=dict(color="gray", dash="dash", width=1.5)
            ), row=1, col=i)

    top_df = (df.sort_values(["conference", "home_win_pct", "avg_score_diff"],
                              ascending=[True, False, False])
                .groupby("conference").head(3).copy())
    for _, row in top_df.iterrows():
        conf_index = conferences.index(row["conference"]) + 1
        fig.add_annotation(
            x=row["avg_utilization"], y=row["home_win_pct"],
            text=f"{row['name_team']} ({row['season']})",
            showarrow=True, arrowhead=1, ax=18, ay=-18,
            font=dict(size=10), row=1, col=conf_index)

    fig.update_layout(legend_title_text="Environment", height=550)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    **Key finding:** Attendance utilization alone does not predict home win rates.
    Attacking activity is a stronger signal — teams with more home attacking events
    tend to appear in stronger win percentage areas.
    """)

# ─────────────────────────────────────────────
# VIZ 4
# ─────────────────────────────────────────────
elif viz == "Viz 4 — Stadium Profile vs Home Advantage":
    st.subheader("Viz 4 — Which Stadium Profiles Create the Strongest Home Advantage?")
    st.markdown("*Capacity, utilization, venue age, or surface — which matters most?*")

    with st.spinner("Loading data..."):
        matches  = transform(extract("matches"))
        stadiums = transform(extract("stadiums"))
        teams    = transform(extract("teams"))
        df = aggregate_stadium_profile(matches, stadiums, teams)

    conferences = [c for c in df["conference"].dropna().unique()]

    fig = px.scatter(
        df,
        x="avg_utilization", y="home_win_pct",
        size="capacity", size_max=26,
        color="surface", symbol="venue_age_tier",
        facet_col="conference",
        hover_name="name",
        hover_data=["season", "division", "avg_attendance",
                    "avg_score_diff", "total_games", "venue_age", "capacity"],
        title="Which Stadium Profiles Create the Strongest Home Advantage?",
        labels={"avg_utilization": "Avg Attendance Utilization (%)",
                "home_win_pct": "Home Win %", "surface": "Surface",
                "venue_age_tier": "Venue Age Tier", "name": "Stadium"}
    )

    for i, conf in enumerate(conferences, start=1):
        sub = df[df["conference"] == conf].dropna(subset=["avg_utilization", "home_win_pct"])
        if len(sub) >= 2:
            x = sub["avg_utilization"]
            y = sub["home_win_pct"]
            m, b = np.polyfit(x, y, 1)
            x_line = np.linspace(x.min(), x.max(), 100)
            fig.add_trace(go.Scatter(
                x=x_line, y=m * x_line + b, mode="lines",
                name=f"{conf} Trend", line=dict(color="gray", dash="dash", width=1.5)
            ), row=1, col=i)

    top_df = (df.sort_values(["conference", "home_win_pct", "avg_score_diff"],
                              ascending=[True, False, False])
                .groupby("conference").head(2))
    for _, row in top_df.iterrows():
        conf_index = conferences.index(row["conference"]) + 1
        fig.add_annotation(
            x=row["avg_utilization"], y=row["home_win_pct"],
            text=f"{row['name']} ({row['season']})",
            showarrow=True, arrowhead=1, ax=18, ay=-18,
            font=dict(size=10), row=1, col=conf_index)

    fig.update_layout(height=550)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    **Key finding:** Stadium capacity, surface type, and venue age do not consistently
    predict home win rates. Attendance utilization has a slight positive relationship
    but the pattern is weak — team quality remains the stronger driver.
    """)

# ─────────────────────────────────────────────
# VIZ 5
# ─────────────────────────────────────────────
elif viz == "Viz 5 — Transfer ROI by Position":
    st.subheader("Viz 5 — Transfer ROI by Position")
    st.markdown("*Are expensive players worth it?*")
    st.markdown("""
    Two heatmaps side by side: average transfer fee by position and transfer type (left),
    and injury rate per transfer (right).
    """)

    with st.spinner("Loading data..."):
        df = aggregate_transfer_roi()

    def make_pivot(df, value):
        return df.pivot_table(
            index="transfer_type", columns="position",
            values=value, aggfunc="mean"
        )

    fee_pivot    = make_pivot(df, "avg_transfer_fee").fillna(0) / 1_000_000
    injury_pivot = make_pivot(df, "injuries_per_transfer").fillna(0)
    fee_pivot    = fee_pivot.loc[fee_pivot.mean(axis=1).sort_values(ascending=False).index]
    injury_pivot = injury_pivot.loc[fee_pivot.index]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
    im1 = ax1.imshow(fee_pivot.values, cmap="Blues", aspect="auto")
    ax1.set_xticks(range(len(fee_pivot.columns)))
    ax1.set_yticks(range(len(fee_pivot.index)))
    ax1.set_xticklabels(fee_pivot.columns)
    ax1.set_yticklabels(fee_pivot.index)
    ax1.set_title("Avg Transfer Fee ($M) by Position & Transfer Type")
    plt.colorbar(im1, ax=ax1, label="Avg Fee ($M)")

    im2 = ax2.imshow(injury_pivot.values, cmap="Reds", aspect="auto")
    ax2.set_xticks(range(len(injury_pivot.columns)))
    ax2.set_yticks(range(len(injury_pivot.index)))
    ax2.set_xticklabels(injury_pivot.columns)
    ax2.set_yticklabels(injury_pivot.index)
    ax2.set_title("Injury Rate by Position & Transfer Type")
    plt.colorbar(im2, ax=ax2, label="Injuries per Transfer")

    position_labels = {
        "CB": "Cornerback", "DL": "Defensive Lineman", "K": "Kicker",
        "LB": "Linebacker", "OL": "Offensive Lineman", "P": "Punter",
        "QB": "Quarterback", "RB": "Running Back", "S": "Safety",
        "TE": "Tight End", "WR": "Wide Receiver"
    }
    legend_elements = [Line2D([0], [0], color="w", label=f"{k}: {v}") for k, v in position_labels.items()]
    fig.legend(handles=legend_elements, loc="center left", bbox_to_anchor=(0.98, 0.95),
               title="Position Key", title_fontsize=10, prop={"size": 8},
               frameon=True, handlelength=0, handletextpad=0, borderpad=0.5, ncol=1)
    fig.suptitle("Transfer ROI by Position", fontsize=18, y=1.03)
    fig.text(0.5, 0.93, "Are Expensive Players Worth It?", ha="center", fontsize=13, color="gray")
    plt.tight_layout(rect=[0, 0, 0.92, 0.90])
    st.pyplot(fig)

    st.markdown("""
    **Key finding:** The most expensive acquisitions carry the highest injury risk.
    True ROI = cost + player availability. High fee does not mean low injury risk.
    """)

# ─────────────────────────────────────────────
# VIZ 6
# ─────────────────────────────────────────────
elif viz == "Viz 6 — Payroll vs Win %":
    st.subheader("Viz 6 — Total Team Payroll vs Win % (2023)")
    st.markdown("*Does paying for more expensive talent result in more wins?*")

    with st.spinner("Loading data..."):
        df = aggregate_payroll()

    fig = px.scatter(
        df, x="win_pct", y="total_payroll",
        hover_name="name",
        hover_data=["win_pct"],
        title="Total Team Payroll vs. Win %",
        labels={"win_pct": "Win %", "total_payroll": "Total Payroll ($)"}
    )

    x = df["win_pct"]
    y = df["total_payroll"]
    m, b = np.polyfit(x, y, 1)
    x_line = np.linspace(x.min(), x.max(), 100)
    fig.add_trace(go.Scatter(
        x=x_line, y=m * x_line + b,
        mode="lines", name="Trend",
        line=dict(color="gray", dash="dash", width=1.5)
    ))
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    **Key finding:** Higher payroll does not consistently lead to higher win rates.
    The trendline is weak and outliers are everywhere — what you spend matters less
    than how strategically you spend it.
    """)

# ─────────────────────────────────────────────
# VIZ 7
# ─────────────────────────────────────────────
elif viz == "Viz 7 — Roster Age vs Points":
    st.subheader("Viz 7 — Does Roster Age Decide Who Wins?")
    st.markdown("*Young players or older ones — which approach wins?*")

    with st.spinner("Loading data..."):
        df = aggregate_roster_age_impact()

    fig = px.scatter(
        df,
        x="avg_roster_age", y="points",
        size="total_games_missed", color="season",
        hover_name="team_name",
        hover_data={"season": True, "wins": True, "season_rank": True,
                    "roster_size": True, "total_games_missed": True, "avg_roster_age": ":.1f"},
        title="Does Roster Age Decide Who Wins? (2020–2023)",
        labels={"avg_roster_age": "Average Roster Age (years)", "points": "Points Earned",
                "total_games_missed": "Games Missed (Injuries)", "season": "Season"},
        trendline="ols", trendline_scope="overall", trendline_color_override="gray"
    )
    fig.update_layout(height=550, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    **Key finding:** The trendline is flat. Roster age does not predict standings success
    in this dataset. Top and bottom performing teams land at similar average ages —
    strategy and execution matter more than demographics.
    """)
