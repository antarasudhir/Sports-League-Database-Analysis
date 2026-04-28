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
CONN_STR = f"sqlitecloud://cgllukzpvk.g1.sqlite.cloud:8860/team7_sportsleague.db?apikey={st.secrets['SQLITECLOUD_API_KEY']}"

st.set_page_config(
    page_title="Sports League DB Analysis — Team 7",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# GLOBAL CSS — Bold Sporty Theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800&family=Barlow:wght@400;500;600&display=swap');

/* ── Root & background ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0a0a0f !important;
    font-family: 'Barlow', sans-serif;
}

[data-testid="stAppViewContainer"] > .main {
    background-color: #0a0a0f;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #0a0a0f 100%) !important;
    border-right: 2px solid #e63946 !important;
    padding-top: 0 !important;
}

[data-testid="stSidebar"] * {
    color: #ffffff !important;
    font-family: 'Barlow Condensed', sans-serif !important;
}

[data-testid="stSidebar"] .stRadio label {
    font-size: 15px !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px !important;
    color: #ffffff !important;
    padding: 6px 0 !important;
}

[data-testid="stSidebar"] .stRadio > div {
    gap: 4px !important;
}

/* Sidebar radio selected state */
[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {
    color: #ffffff !important;
    font-size: 15px !important;
}

/* ── Sidebar header ── */
.sidebar-logo {
    background: linear-gradient(135deg, #e63946 0%, #c1121f 100%);
    margin: -1rem -1rem 1.5rem -1rem;
    padding: 1.5rem 1rem;
    text-align: center;
}

.sidebar-logo h1 {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-size: 22px !important;
    font-weight: 800 !important;
    color: #ffffff !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    margin: 0 !important;
    line-height: 1.2 !important;
}

.sidebar-logo p {
    color: rgba(255,255,255,0.8) !important;
    font-size: 11px !important;
    letter-spacing: 1px !important;
    margin: 4px 0 0 0 !important;
    text-transform: uppercase !important;
}

.sidebar-team {
    background: rgba(230, 57, 70, 0.1);
    border: 1px solid rgba(230, 57, 70, 0.3);
    border-radius: 8px;
    padding: 10px 12px;
    margin-top: 12px;
}

.sidebar-team p {
    color: #e63946 !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    margin: 0 0 4px 0 !important;
}

.sidebar-team span {
    color: #ffffff !important;
    font-size: 13px !important;
}

/* ── Main content ── */
.main .block-container {
    padding: 1.5rem 2rem 2rem 2rem !important;
    max-width: 1400px !important;
}

/* ── Hero banner ── */
.hero-banner {
    background: linear-gradient(135deg, #e63946 0%, #c1121f 50%, #7b0d1e 100%);
    border-radius: 16px;
    padding: 2.5rem 2.5rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}

.hero-banner::before {
    content: '🏈';
    position: absolute;
    right: 2rem;
    top: 50%;
    transform: translateY(-50%);
    font-size: 100px;
    opacity: 0.15;
}

.hero-banner::after {
    content: '';
    position: absolute;
    top: 0; right: 0; bottom: 0;
    width: 40%;
    background: repeating-linear-gradient(
        45deg,
        transparent,
        transparent 10px,
        rgba(255,255,255,0.03) 10px,
        rgba(255,255,255,0.03) 20px
    );
}

.hero-eyebrow {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: rgba(255,255,255,0.7);
    margin-bottom: 8px;
}

.hero-title {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 52px;
    font-weight: 800;
    color: #ffffff;
    line-height: 1.0;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.hero-subtitle {
    font-size: 16px;
    color: rgba(255,255,255,0.8);
    margin-bottom: 1.5rem;
    font-weight: 400;
}

.stat-pills {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.stat-pill {
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 100px;
    padding: 6px 16px;
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 14px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: 0.5px;
    backdrop-filter: blur(4px);
}

/* ── Section headers ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 0.5rem;
}

.section-number {
    background: #e63946;
    color: #ffffff;
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 1px;
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.section-title {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 32px;
    font-weight: 800;
    color: #ffffff;
    text-transform: uppercase;
    letter-spacing: 1px;
    line-height: 1;
}

.section-subtitle {
    color: #9ca3af;
    font-size: 15px;
    margin-bottom: 1.5rem;
    font-style: italic;
    padding-left: 44px;
}

/* ── Key finding card ── */
.finding-card {
    background: linear-gradient(135deg, rgba(230,57,70,0.12) 0%, rgba(230,57,70,0.05) 100%);
    border: 1px solid rgba(230,57,70,0.4);
    border-left: 4px solid #e63946;
    border-radius: 10px;
    padding: 14px 18px;
    margin-top: 1rem;
}

.finding-card p {
    color: #f1f5f9 !important;
    font-size: 14px !important;
    margin: 0 !important;
    line-height: 1.6 !important;
}

.finding-label {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #e63946;
    margin-bottom: 4px;
}

/* ── Metric cards ── */
.metric-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin: 1.5rem 0;
}

.metric-card {
    background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
    border: 1px solid #30363d;
    border-top: 3px solid #e63946;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
}

.metric-value {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 42px;
    font-weight: 800;
    color: #ffffff;
    line-height: 1;
}

.metric-label {
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #6b7280;
    margin-top: 4px;
}

/* ── Overview table ── */
.overview-table {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    overflow: hidden;
    margin-top: 1rem;
}

/* ── Divider ── */
.sport-divider {
    height: 2px;
    background: linear-gradient(90deg, #e63946 0%, rgba(230,57,70,0.3) 50%, transparent 100%);
    margin: 2rem 0;
    border: none;
}

/* ── General text ── */
h1, h2, h3, p, li, span {
    color: #ffffff;
}

/* Fix plotly chart backgrounds */
.js-plotly-plot {
    border-radius: 12px;
    overflow: hidden;
}

/* ── Nav label fix ── */
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label div p {
    color: #ffffff !important;
    font-size: 15px !important;
    font-weight: 600 !important;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #ffffff !important;
}

/* Divider line */
hr {
    border-color: #30363d !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SHARED HELPER FUNCTIONS
# ─────────────────────────────────────────────

@st.cache_data
def extract(table_name):
    conn = sqlitecloud.connect(CONN_STR)
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df

def transform(df):
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
# PLOTLY THEME
# ─────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="#0d1117",
    plot_bgcolor="#0d1117",
    font=dict(color="#ffffff", family="Barlow, sans-serif"),
    title_font=dict(size=18, color="#ffffff", family="Barlow Condensed, sans-serif"),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#ffffff")),
    xaxis=dict(gridcolor="#1f2937", zerolinecolor="#374151", color="#9ca3af"),
    yaxis=dict(gridcolor="#1f2937", zerolinecolor="#374151", color="#9ca3af"),
)

PLOTLY_COLORS = ["#e63946", "#457b9d", "#f4a261", "#2a9d8f", "#e9c46a", "#a8dadc", "#ff6b6b", "#4ecdc4"]

# ─────────────────────────────────────────────
# AGGREGATE FUNCTIONS
# ─────────────────────────────────────────────

@st.cache_data
def aggregate_injury_vs_wins():
    injuries  = transform(extract("injuries"))
    teams     = transform(extract("teams"))
    standings = transform(extract("standings"))
    standings["win_pct"] = (standings["wins"] / (standings["wins"] + standings["losses"] + standings["draws"]) * 100).round(1)
    standings_avg = standings.groupby("team_id")["win_pct"].mean().reset_index()
    standings_avg.columns = ["team_id", "avg_win_pct"]
    df = injuries.merge(teams[["team_id", "name"]], on="team_id")
    df = df.merge(standings_avg, on="team_id")
    df = df.rename(columns={"name": "team_name"})
    analytical = df.groupby(["team_name", "severity", "avg_win_pct"]).agg(
        total_games_missed=("games_missed", "sum"),
        total_injuries=("injury_id", "count")
    ).reset_index()
    analytical["win_rank"] = analytical["avg_win_pct"].rank(ascending=False, method="dense").astype(int)
    return analytical

@st.cache_data
def aggregate_win_pct():
    teams     = transform(extract("teams"))
    standings = transform(extract("standings"))
    injuries  = transform(extract("injuries"))
    mem = sqlite3.connect(":memory:")
    teams.to_sql("teams", mem, index=False, if_exists="replace")
    standings.to_sql("standings", mem, index=False, if_exists="replace")
    injuries.to_sql("injuries", mem, index=False, if_exists="replace")
    sql = """
        SELECT t.conference, t.division,
            ROUND(AVG(st.wins * 100.0 / (st.wins + st.losses + st.draws)), 1) AS avg_win_pct,
            ROUND(AVG(inj.total_games_missed), 1) AS avg_games_missed
        FROM teams t
        JOIN standings st ON t.team_id = st.team_id
        JOIN (SELECT team_id, SUM(games_missed) AS total_games_missed FROM injuries GROUP BY team_id) inj ON t.team_id = inj.team_id
        GROUP BY t.conference, t.division ORDER BY avg_win_pct DESC
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
    df = df.merge(teams[["team_id", "name", "conference", "division"]], left_on="home_team_id", right_on="team_id", how="left", suffixes=("", "_team"))
    df["attendance_utilization"] = np.where(df["capacity"] > 0, df["attendance"] / df["capacity"] * 100, np.nan)
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
    analytical["attendance_tier"] = pd.qcut(analytical["avg_utilization"], q=3, labels=["Low Utilization", "Medium Utilization", "High Utilization"], duplicates="drop")
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
    df["attendance_utilization_match"] = np.where(df["capacity"] > 0, df["attendance"] / df["capacity"] * 100, np.nan)
    df["season_num"] = pd.to_numeric(df["season"], errors="coerce")
    df["venue_age"] = df["season_num"] - df["year_opened"]
    analytical = df.groupby(["season", "stadium_id", "name", "conference", "division", "surface", "capacity", "year_opened"]).agg(
        total_games=("match_id", "count"),
        home_win_pct=("home_win", "mean"),
        avg_score_diff=("score_diff", "mean"),
        avg_attendance=("attendance", "mean"),
        avg_utilization=("attendance_utilization_match", "mean"),
        venue_age=("venue_age", "mean")
    ).reset_index()
    analytical["home_win_pct"] = analytical["home_win_pct"] * 100
    analytical["venue_age_tier"] = pd.cut(analytical["venue_age"], bins=[-np.inf, 15, 30, np.inf], labels=["Newer Venue", "Mid-Age Venue", "Older Venue"])
    return analytical

@st.cache_data
def aggregate_transfer_roi():
    conn = sqlitecloud.connect(CONN_STR)
    query = """
    SELECT p.position, t.transfer_type,
      COUNT(DISTINCT t.transfer_id) AS total_transfers,
      ROUND(AVG(t.fee), 2) AS avg_transfer_fee,
      ROUND(AVG(p.contract_salary), 2) AS avg_salary,
      ROUND(COUNT(i.injury_id) * 1.0 / NULLIF(COUNT(DISTINCT t.transfer_id), 0),2) AS injuries_per_transfer
    FROM players p
    JOIN transfers t ON p.player_id = t.player_id
    LEFT JOIN injuries i ON p.player_id = i.player_id
    WHERE t.fee >= 0 AND t.fee IS NOT NULL
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
    df["win_pct"] = (df["wins"] / (df["wins"] + df["losses"] + df["draws"]) * 100).round(1)
    df = df.merge(players[["team_id", "contract_salary"]], on="team_id", how="left")
    df = df.groupby("team_id").agg(total_payroll=("contract_salary", "sum"), win_pct=("win_pct", "mean")).reset_index()
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
    standings.to_sql("standings", mem, index=False, if_exists="replace")
    teams.to_sql("teams", mem, index=False, if_exists="replace")
    players_active.to_sql("players", mem, index=False, if_exists="replace")
    injuries.to_sql("injuries", mem, index=False, if_exists="replace")
    sql = """
        WITH roster_age AS (
            SELECT team_id, ROUND(AVG(age), 1) AS avg_roster_age, COUNT(player_id) AS roster_size
            FROM players GROUP BY team_id
        ),
        injury_load AS (
            SELECT team_id, SUM(games_missed) AS total_games_missed, COUNT(injury_id) AS total_injuries
            FROM injuries GROUP BY team_id
        )
        SELECT t.name AS team_name, t.abbreviation, t.conference, t.division,
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
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <h1>🏆 Sports League<br>DB Analysis</h1>
        <p>MET AD599 · Team 7</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**NAVIGATE**")
    viz = st.radio("", [
        "🏠  Overview",
        "01  Injury Severity vs Win Rate",
        "02  Win % vs Injury Burden",
        "03  Match Environment & Home Advantage",
        "04  Stadium Profile & Home Advantage",
        "05  Transfer ROI by Position",
        "06  Payroll vs Win %",
        "07  Roster Age vs Points",
    ], label_visibility="collapsed")

    st.markdown("""
    <div class="sidebar-team">
        <p>Team 7</p>
        <span>Haley · Simon · Sarah<br>Antara · Meera · Julie</span>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# OVERVIEW
# ─────────────────────────────────────────────
if viz == "🏠  Overview":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-eyebrow">MET BU · AD599 · Prof. Sree Kumar · Part 2</div>
        <div class="hero-title">Sports League<br>DB Analysis</div>
        <div class="hero-subtitle">Which factors drive team success and failure across 4 seasons?</div>
        <div class="stat-pills">
            <span class="stat-pill">🏈 16 Teams</span>
            <span class="stat-pill">👤 400 Players</span>
            <span class="stat-pill">⚔️ 800 Matches</span>
            <span class="stat-pill">📅 4 Seasons (2020–2023)</span>
            <span class="stat-pill">🗄️ 8 Tables</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="metric-row">
        <div class="metric-card">
            <div class="metric-value">16</div>
            <div class="metric-label">Teams</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">400</div>
            <div class="metric-label">Players</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">800</div>
            <div class="metric-label">Matches</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">8</div>
            <div class="metric-label">DB Tables</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="sport-divider">', unsafe_allow_html=True)
    st.markdown("""
    <div class="section-header">
        <div class="section-title">Visualizations</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    | # | Visualization | Tables Used | Owner |
    |---|---|---|---|
    | 01 | Injury Severity vs Team Win Rate | injuries, standings, teams | Meera |
    | 02 | Win % vs Injury Burden by Division | teams, standings, injuries | Julie |
    | 03 | Match Environment vs Home Advantage | matches, stadiums, teams, match_events | Sarah |
    | 04 | Stadium Profile vs Home Advantage | matches, stadiums, teams | Sarah |
    | 05 | Transfer ROI by Position | players, transfers, injuries | Antara |
    | 06 | Total Payroll vs Win % | players, standings | Hayley |
    | 07 | Roster Age vs Points | standings, players, teams, injuries | Simon |
    """)

    st.markdown('<hr class="sport-divider">', unsafe_allow_html=True)
    st.markdown("""
    <div class="finding-card">
        <div class="finding-label">🏆 Key Conclusion</div>
        <p>No single factor decides who wins. Roster depth, injury management, and team execution
        matter more than payroll, age, or stadium size.</p>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HELPER: render section header
# ─────────────────────────────────────────────
def section_header(num, title, subtitle):
    st.markdown(f"""
    <div class="section-header">
        <div class="section-number">{num}</div>
        <div class="section-title">{title}</div>
    </div>
    <div class="section-subtitle">{subtitle}</div>
    """, unsafe_allow_html=True)

def finding(text):
    st.markdown(f"""
    <div class="finding-card">
        <div class="finding-label">📊 Key Finding</div>
        <p>{text}</p>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# VIZ 1
# ─────────────────────────────────────────────
    elif viz == "01  Injury Severity vs Win Rate":
        section_header("01", "Injury Severity vs Win Rate", "Does injury burden predict team success?")
    
        with st.spinner("Loading data..."):
            df = aggregate_injury_vs_wins()
    
        heatmap_data = df.pivot_table(index="team_name", columns="severity", values="total_games_missed", aggfunc="sum").fillna(0)
        heatmap_data["TOTAL"] = heatmap_data.sum(axis=1)
        team_order = df[["team_name", "avg_win_pct"]].drop_duplicates().sort_values("avg_win_pct", ascending=False)["team_name"].tolist()
        heatmap_data = heatmap_data.reindex(team_order)
        win_pcts = df[["team_name", "avg_win_pct"]].drop_duplicates().set_index("team_name")["avg_win_pct"].to_dict()
        heatmap_data.index = [f"{t}  ({round(win_pcts[t], 1)}% wins)" for t in heatmap_data.index]
    
        fig = px.imshow(heatmap_data, color_continuous_scale=[[0, "#0d1117"], [0.5, "#457b9d"], [1, "#e63946"]],
            text_auto=True, aspect="auto",
            title="Injury Severity Heatmap — Teams Ranked by Win Rate",
            labels={"x": "Injury Severity", "y": "Team", "color": "Games Missed"})
        fig.update_layout(**PLOTLY_LAYOUT, height=600)
        fig.update_layout(xaxis=dict(side="bottom", color="#9ca3af"), coloraxis_colorbar=dict(tickfont=dict(color="#ffffff"), title=dict(font=dict(color="#ffffff"))))
        st.plotly_chart(fig, use_container_width=True)
    
        finding("Injury severity alone does not predict wins. The Cowboys (78.1% win rate) suffered 101 severe games missed. The Eagles had the fewest total injuries (148) and still posted 68.8%. <strong>Roster depth absorbs injuries better than avoiding them.</strong>")

# ─────────────────────────────────────────────
# VIZ 2
# ─────────────────────────────────────────────
    elif viz == "02  Win % vs Injury Burden":
        section_header("02", "Win % vs Injury Burden", "Do heavier injury burdens lead to lower win rates?")
    
        with st.spinner("Loading data..."):
            analytical = aggregate_win_pct()
    
        analytical["label"] = analytical["conference"] + " " + analytical["division"]
        fig = px.scatter(analytical, x="avg_win_pct", y="avg_games_missed",
            color="conference", symbol="division", text="label",
            color_discrete_sequence=["#e63946", "#457b9d"],
            title="Do Heavier Injury Burdens Lead to Lower Win Rates?",
            labels={"avg_win_pct": "Avg Win %", "avg_games_missed": "Avg Games Missed Due to Injury"})
        x = analytical["avg_win_pct"]
        y = analytical["avg_games_missed"]
        m, b = np.polyfit(x, y, 1)
        x_line = np.linspace(x.min(), x.max(), 100)
        fig.add_trace(go.Scatter(x=x_line, y=m * x_line + b, mode="lines", name="Trend",
            line=dict(color="#f4a261", dash="dash", width=2)))
        fig.update_traces(textposition="top center")
        fig.update_layout(**PLOTLY_LAYOUT, height=550)
        st.plotly_chart(fig, use_container_width=True)
    
        finding("Weak negative correlation — divisions with more injury games missed tend to win less. AFC EAST has the highest win % and lowest games missed. <strong>But roster depth can override injury burden.</strong>")

# ─────────────────────────────────────────────
# VIZ 3
# ─────────────────────────────────────────────
    elif viz == "03  Match Environment & Home Advantage":
        section_header("03", "Match Environment & Home Advantage", "Attendance, surface, or attacking play — what creates home advantage?")
    
        with st.spinner("Loading data..."):
            matches      = transform(extract("matches"))
            stadiums     = transform(extract("stadiums"))
            teams        = transform(extract("teams"))
            match_events = transform(extract("match_events"))
            df = aggregate_match_environment(matches, stadiums, teams, match_events)
    
        conferences = [c for c in df["conference"].dropna().unique()]
        fig = px.scatter(df, x="avg_utilization", y="home_win_pct",
            size="avg_home_attacking_events", size_max=22,
            color="attendance_tier", symbol="surface", facet_col="conference",
            color_discrete_sequence=PLOTLY_COLORS,
            hover_name="name_team",
            hover_data=["season", "division", "surface", "avg_attendance", "avg_score_diff", "total_home_games", "avg_home_attacking_events"],
            title="Which Match Environments Drive Home Advantage?",
            labels={"avg_utilization": "Avg Attendance Utilization (%)", "home_win_pct": "Home Win %",
                    "avg_home_attacking_events": "Avg Home Attacking Events", "attendance_tier": "Attendance Tier"})
        for i, conf in enumerate(conferences, start=1):
            sub = df[df["conference"] == conf].dropna(subset=["avg_utilization", "home_win_pct"]).copy()
            if len(sub) >= 2:
                x = sub["avg_utilization"]; y = sub["home_win_pct"]
                m, b = np.polyfit(x, y, 1); x_line = np.linspace(x.min(), x.max(), 100)
                fig.add_trace(go.Scatter(x=x_line, y=m * x_line + b, mode="lines",
                    name=f"{conf} Trend", line=dict(color="#f4a261", dash="dash", width=1.5)), row=1, col=i)
        fig.update_layout(**PLOTLY_LAYOUT, height=550, legend_title_text="Environment")
        st.plotly_chart(fig, use_container_width=True)
    
        finding("Attendance utilization does not strongly predict home win %. <strong>Attacking activity is a stronger signal</strong> — teams with more home attacking events tend to have higher win percentages.")
    
    # ─────────────────────────────────────────────
    # VIZ 4
    # ─────────────────────────────────────────────
    elif viz == "04  Stadium Profile & Home Advantage":
        section_header("04", "Stadium Profile & Home Advantage", "Capacity, utilization, venue age, or surface — which matters most?")
    
        with st.spinner("Loading data..."):
            matches  = transform(extract("matches"))
            stadiums = transform(extract("stadiums"))
            teams    = transform(extract("teams"))
            df = aggregate_stadium_profile(matches, stadiums, teams)
    
        conferences = [c for c in df["conference"].dropna().unique()]
        fig = px.scatter(df, x="avg_utilization", y="home_win_pct",
            size="capacity", size_max=26,
            color="surface", symbol="venue_age_tier", facet_col="conference",
            color_discrete_sequence=["#e63946", "#457b9d"],
            hover_name="name",
            hover_data=["season", "division", "avg_attendance", "avg_score_diff", "total_games", "venue_age", "capacity"],
            title="Which Stadium Profiles Create the Strongest Home Advantage?",
            labels={"avg_utilization": "Avg Attendance Utilization (%)", "home_win_pct": "Home Win %"})
        for i, conf in enumerate(conferences, start=1):
            sub = df[df["conference"] == conf].dropna(subset=["avg_utilization", "home_win_pct"])
            if len(sub) >= 2:
                x = sub["avg_utilization"]; y = sub["home_win_pct"]
                m, b = np.polyfit(x, y, 1); x_line = np.linspace(x.min(), x.max(), 100)
                fig.add_trace(go.Scatter(x=x_line, y=m * x_line + b, mode="lines",
                    name=f"{conf} Trend", line=dict(color="#f4a261", dash="dash", width=1.5)), row=1, col=i)
        fig.update_layout(**PLOTLY_LAYOUT, height=550)
        st.plotly_chart(fig, use_container_width=True)
    
        finding("Stadium capacity, surface type, and venue age do not consistently predict home win rates. <strong>Team quality and match execution remain the strongest drivers of home advantage.</strong>")
    
    # ─────────────────────────────────────────────
    # VIZ 5
    # ─────────────────────────────────────────────
    elif viz == "05  Transfer ROI by Position":
        section_header("05", "Transfer ROI by Position", "Are expensive players worth it?")
    
        with st.spinner("Loading data..."):
            df = aggregate_transfer_roi()
    
        def make_pivot(df, value):
            return df.pivot_table(index="transfer_type", columns="position", values=value, aggfunc="mean")
    
        fee_pivot    = make_pivot(df, "avg_transfer_fee").fillna(0) / 1_000_000
        injury_pivot = make_pivot(df, "injuries_per_transfer").fillna(0)
        fee_pivot    = fee_pivot.loc[fee_pivot.mean(axis=1).sort_values(ascending=False).index]
        injury_pivot = injury_pivot.loc[fee_pivot.index]
    
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        fig.patch.set_facecolor("#0d1117")
        for ax in [ax1, ax2]:
            ax.set_facecolor("#0d1117")
            ax.tick_params(colors="#9ca3af")
            for spine in ax.spines.values():
                spine.set_edgecolor("#30363d")
    
        im1 = ax1.imshow(fee_pivot.values, cmap="Blues", aspect="auto")
        ax1.set_xticks(range(len(fee_pivot.columns))); ax1.set_yticks(range(len(fee_pivot.index)))
        ax1.set_xticklabels(fee_pivot.columns, color="#9ca3af"); ax1.set_yticklabels(fee_pivot.index, color="#9ca3af")
        ax1.set_title("Avg Transfer Fee ($M) by Position & Transfer Type", color="#ffffff", fontsize=12, pad=10)
        cb1 = plt.colorbar(im1, ax=ax1, label="Avg Fee ($M)")
        cb1.ax.yaxis.set_tick_params(color="#9ca3af"); cb1.set_label("Avg Fee ($M)", color="#9ca3af")
    
        im2 = ax2.imshow(injury_pivot.values, cmap="Reds", aspect="auto")
        ax2.set_xticks(range(len(injury_pivot.columns))); ax2.set_yticks(range(len(injury_pivot.index)))
        ax2.set_xticklabels(injury_pivot.columns, color="#9ca3af"); ax2.set_yticklabels(injury_pivot.index, color="#9ca3af")
        ax2.set_title("Injury Rate by Position & Transfer Type", color="#ffffff", fontsize=12, pad=10)
        cb2 = plt.colorbar(im2, ax=ax2, label="Injuries per Transfer")
        cb2.ax.yaxis.set_tick_params(color="#9ca3af"); cb2.set_label("Injuries per Transfer", color="#9ca3af")
    
        position_labels = {"CB": "Cornerback", "DL": "Defensive Lineman", "K": "Kicker",
            "LB": "Linebacker", "OL": "Offensive Lineman", "P": "Punter",
            "QB": "Quarterback", "RB": "Running Back", "S": "Safety", "TE": "Tight End", "WR": "Wide Receiver"}
        legend_elements = [Line2D([0], [0], color="w", label=f"{k}: {v}") for k, v in position_labels.items()]
        fig.legend(handles=legend_elements, loc="center left", bbox_to_anchor=(0.98, 0.95),
            title="Position Key", title_fontsize=9, prop={"size": 8},
            frameon=True, handlelength=0, handletextpad=0, borderpad=0.5, ncol=1,
            facecolor="#161b22", labelcolor="#ffffff", title_fontcolor="#e63946")
        fig.suptitle("Transfer ROI by Position", fontsize=18, color="#ffffff", y=1.03,
            fontfamily="sans-serif", fontweight="bold")
        fig.text(0.5, 0.93, "Are Expensive Players Worth It?", ha="center", fontsize=13, color="#9ca3af")
        plt.tight_layout(rect=[0, 0, 0.92, 0.90])
        st.pyplot(fig)
    
        finding("The most expensive acquisitions carry the highest injury risk. WR & TE free transfers show high injury rates. <strong>True ROI = cost + player availability. High fee ≠ low injury risk.</strong>")
    
    # ─────────────────────────────────────────────
    # VIZ 6
    # ─────────────────────────────────────────────
    elif viz == "06  Payroll vs Win %":
        section_header("06", "Payroll vs Win %", "Does paying for more expensive talent result in more wins?")
    
        with st.spinner("Loading data..."):
            df = aggregate_payroll()
    
        fig = px.scatter(df, x="win_pct", y="total_payroll", hover_name="name",
            color_discrete_sequence=["#e63946"],
            title="Total Team Payroll vs. Win % (2023 Season)",
            labels={"win_pct": "Win %", "total_payroll": "Total Payroll ($)"})
        x = df["win_pct"]; y = df["total_payroll"]
        m, b = np.polyfit(x, y, 1); x_line = np.linspace(x.min(), x.max(), 100)
        fig.add_trace(go.Scatter(x=x_line, y=m * x_line + b, mode="lines", name="Trend",
            line=dict(color="#f4a261", dash="dash", width=2)))
        fig.update_traces(marker=dict(size=10), selector=dict(mode="markers"))
        fig.update_layout(**PLOTLY_LAYOUT, height=500)
        st.plotly_chart(fig, use_container_width=True)
    
        finding("Higher payroll does not consistently lead to higher win rates. Payrolls range $200M–$500M but the trendline is shallow with many outliers. <strong>How you build a roster matters more than how much you spend.</strong>")
    
    # ─────────────────────────────────────────────
    # VIZ 7
    # ─────────────────────────────────────────────
    elif viz == "07  Roster Age vs Points":
        section_header("07", "Roster Age vs Points", "Young players or older ones — which approach wins?")
    
        with st.spinner("Loading data..."):
            df = aggregate_roster_age_impact()
    
        fig = px.scatter(df, x="avg_roster_age", y="points",
            size="total_games_missed", color="season",
            color_discrete_sequence=["#e63946", "#457b9d", "#f4a261", "#2a9d8f"],
            hover_name="team_name",
            hover_data={"season": True, "wins": True, "season_rank": True,
                        "roster_size": True, "total_games_missed": True, "avg_roster_age": ":.1f"},
            title="Does Roster Age Decide Who Wins? (2020–2023)",
            labels={"avg_roster_age": "Average Roster Age (years)", "points": "Points Earned",
                    "total_games_missed": "Games Missed (Injuries)", "season": "Season"},
            trendline="ols", trendline_scope="overall", trendline_color_override="#f4a261")
        fig.update_layout(**PLOTLY_LAYOUT, height=550, template="plotly_dark")
        fig.update_layout(paper_bgcolor="#0d1117", plot_bgcolor="#0d1117")
        st.plotly_chart(fig, use_container_width=True)
    
        finding("The trendline is nearly flat. Roster age does not predict standings success. Top and bottom performing teams land at similar average ages. <strong>Strategy and execution matter more than demographics.</strong>")
