# 🏆 Sports League Database Analysis
### MET AD599 — Final Project | Python & SQL

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://dbsportleagueanalysis-lohae79pxpz7tzapp2aky4r.streamlit.app/)

An end-to-end data analysis project built on a fictional professional sports league database. We connected to a live cloud-hosted SQLite database, engineered a shared ETL pipeline in Python, and produced 7 interactive visualizations exploring the factors that drive team success — across injuries, payroll, stadium environments, player transfers, and roster composition.

> **Central Question: Which factors drive team success in this sports league?**

---

## 👥 Team 7
Haley · Simon · Sarah · Antara · Meera · Julie

---

## 📋 Table of Contents

- [Tech Stack](#tech-stack)
- [Database Schema](#database-schema)
- [ETL Pipeline](#etl-pipeline)
- [Visualizations & Key Findings](#visualizations--key-findings)
- [Conclusions & Recommendations](#conclusions--recommendations)
- [Setup & Installation](#setup--installation)
- [Live App](#live-app)

---

## Tech Stack

| Layer | Tools |
|---|---|
| **Database** | SQLite Cloud (`sqlitecloud`) via sqlite.ai |
| **Data Processing** | Python, Pandas, NumPy |
| **SQL** | Analytical SQL with window functions (`RANK()`, `OVER`, `PARTITION BY`) |
| **Visualization** | Plotly Express, Plotly Graph Objects, Matplotlib |
| **App Framework** | Streamlit |
| **Notebook** | Google Colab |

---

## Database Schema

![Entity Relationship Diagram](assets/AD599%20Team%207%20ERD.png)

The `team7_sportsleague.db` database contains 8 tables covering seasons 2020–2023:

| Table | Description |
|---|---|
| `teams` | Team names, conferences, divisions |
| `players` | Roster info, positions, salaries, date of birth |
| `standings` | Wins, losses, points per team per season |
| `matches` | Home/away matchups, scores, stadium, attendance |
| `stadiums` | Venue name, capacity, surface type, year built |
| `injuries` | Player injury records with severity and games missed |
| `transfers` | Player acquisition type (permanent, loan, free, academy) and fees |
| `match_events` | In-match event logs (goals, assists, etc.) |

---

## ETL Pipeline

We built a shared 4-function ETL pipeline used across every visualization:

```
Database → extract() → transform() → aggregate() → visualize()
  [SHARED]    [SHARED]    [PERSONAL]    [PERSONAL]
```

### 1. Extract
```python
def extract(table_name):
    conn = sqlitecloud.connect(CONN_STR)
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df
```

### 2. Transform
```python
def transform(df):
    # Cleans nulls, standardizes date types, renames columns
    # Safe to call on any table — only applies where columns exist
    ...
```

### 3. Aggregate
Each visualization has its own `aggregate_*()` function that joins multiple tables, computes derived metrics (win %, injury rates, payroll totals), and returns a clean analytical dataframe.

### 4. Visualize
Each visualization has its own `visualize_*()` function that renders an interactive Plotly chart from the aggregated dataframe.

---

## Visualizations & Key Findings

### Visual 1 — 🩹 Injury Severity vs Team Win Rate
> *Does injury burden predict team success?*

A heatmap of total games missed per team broken down by injury severity (Minor / Moderate / Severe), with teams sorted by win rate.

**Key Findings:**
- Cowboys: 78.1% win rate despite 101 severe games missed
- Ravens: 35.9% win rate with only 66 severe games missed
- Eagles: lowest total injuries (148) paired with a 68.8% win rate

**Interpretation:** Injury severity alone does not predict wins. Roster depth matters more.

---

### Visual 2 — 📊 Win % vs Injury Burden by Conference & Division
> *Do heavier injury burdens lead to lower win rates?*

A scatter plot comparing average games missed to average win % across all 8 divisions (AFC/NFC), with trend lines per conference.

**Key Findings:**
- Weak negative correlation — injury burden tends to hurt win rates
- AFC NORTH carried the highest injury burden; AFC EAST showed the lowest

**Interpretation:** More injuries generally reduces performance, but the weak correlation suggests other factors are at play.

---

### Visual 3 — 🏟️ Home Advantage Drivers by Match Environment
> *Which match environments create the strongest home advantage: attendance, surface, or attacking activity?*

A bubble scatter plot at the team-season level, faceted by conference. X-axis: attendance utilization. Y-axis: home win %. Bubble size: home attacking activity.

**Key Findings:**
- Attendance utilization does not strongly predict home win %
- Grass and FieldTurf show mixed results across win levels
- Larger bubbles (more attacking activity) relate more closely to home success
- AFC and NFC patterns are similar — no clear conference effect

**Interpretation:** Attacking performance appears more influential than stadium environment. Home advantage is driven by team quality and play style, not venue conditions.

---

### Visual 4 — 🏟️ Stadium Profile vs Home Advantage
> *Which stadium profiles create stronger home advantage: capacity, utilization, venue age, or surface?*

A scatter plot at the stadium-season level comparing utilization and home win %, with capacity, surface, and venue age as additional dimensions.

**Key Findings:**
- Attendance utilization shows only a weak positive trend
- Larger-capacity venues do not consistently produce higher home win %
- Newer vs. older venues show no clear advantage
- Both Grass and FieldTurf appear across all performance levels

**Interpretation:** Stadium profile has limited direct impact on home advantage. Team quality and match execution are stronger drivers.

---

### Visual 5 — 💸 Transfer ROI by Position
> *Are expensive players worth it?*

A dual heatmap showing average transfer fee ($M) and injury rate (injuries per transfer) by position and acquisition type.

**Key Findings:**
- Free transfers of QBs, Ks, and Ps carry surprisingly high average fees
- WR and TE acquisitions via free transfer and academy promotion show high injury rates
- Cost and injury risk don't move together — expensive methods don't guarantee physical reliability

**Interpretation:** "Free" signings are deceptively costly due to premium contracts. The true cost of WR, LB, and TE signings extends well beyond the transfer fee — injury exposure must be factored into ROI.

---

### Visual 6 — 💰 Total Team Payroll vs Win %
> *Can teams in this league "pay to win"?*

A scatter plot with total team payroll on the Y-axis and 2023 win percentage on the X-axis, including a linear trendline. Payrolls ranged from ~$200M to ~$500M.

**Key Findings:**
- Most teams cluster between $280M–$350M in total payroll
- Trendline shows a modest increase in win % with higher payroll, but the slope is shallow
- Multiple outliers undermine the trend

**Interpretation:** The data points are too dispersed to support a strong correlation between payroll and win percentage.

---

### Visual 7 — 👴 Does Roster Age Decide Who Wins?
> *Young rosters vs. veteran rosters — which approach wins?*

A team-season scatter plot (2020–2023) with average roster age on the X-axis, season points on the Y-axis, and injury burden as dot size.

**Key Findings:**
- Average roster age ranges from 24 to 33 years across all teams
- Trendline is nearly flat — no clear relationship between age and points earned
- Top-ranked and bottom-ranked teams span the full age spectrum
- Injury burden does not cluster in any specific age range

**Interpretation:** The absence of a pattern also reflects the nature of synthetic data combining multiple sports — a real-world dataset would likely show stronger age-related trends.

---

## Conclusions & Recommendations

> **No single factor decides who wins.**

| Factor | Signal Strength | Key Takeaway |
|---|---|---|
| Injury burden | Weak negative | Roster depth absorbs injuries better than avoiding them |
| Home advantage | Exists, but... | Driven by team execution, not stadium size or surface |
| Transfer spending | Misleading | True cost includes injury risk beyond the transfer fee |
| Payroll | Weakest signal | How you build a roster matters more than how much you spend |
| Roster age | No signal | Age alone is not a predictor of team success |

**Our 3 Recommendations:**
1. **Invest in roster depth**, not just expensive stars
2. **Factor injury exposure into transfer ROI** — the fee is only part of the cost
3. **Future analysis could include** Logistic Regression (Win/Loss probability) and Linear Regression (predict team seasonal points)

---

## Setup & Installation

### Prerequisites
- Python 3.8+
- SQLite Cloud account (or use the connection string from the notebook)

### Install dependencies
```bash
pip install streamlit sqlitecloud pandas numpy plotly matplotlib statsmodels
```

### Run the Streamlit app locally
```bash
streamlit run app.py
```

### Run the notebook
Open `AD599_Notebook.ipynb` in Google Colab and run all cells top to bottom. The first cell installs `sqlitecloud` and `statsmodels` automatically.

---

## Live App

🚀 **[View the live Streamlit app](https://dbsportleagueanalysis-lohae79pxpz7tzapp2aky4r.streamlit.app/)**

📎 **[View Presentation Slides](Slide_Deck.pdf)**

---
*MET AD599 Final Project — Boston University Metropolitan College*  
*Database: `team7_sportsleague.db` hosted on [sqlite.ai](https://sqlite.ai)*
