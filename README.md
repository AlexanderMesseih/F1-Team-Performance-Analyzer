# F1-Team-Performance-Analyzer

## Project Description

The purpose of this project is to analyze and aggregate F1 team's constructor/car performance over the last 10 years (2015–2024). The idea is to go a bit deeper than championship standings, and looking at things like how teams perform under different weather conditions, whether their results actually match their budget, and where certain constructors consistently fall apart. It's also to compare teams progression in rankings over the past 10 years and see what factors most intensely affected their results to determine which factors most heavily impact rankings. Mostly an excuse to pull together a decade of race data and see what patterns show up.

---

## Setup & Installation

```bash
pip install -r requirements.txt
```

### Collecting data

Race data is pre-bundled in `data/race_results.json` (4,220 entries across 2015–2024). To re-collect from scratch using the FastF1 API:

```bash
python collect_data.py         # Fetches from FastF1 (rate-limited to 500 calls/hr)
python supplement_data.py      # Fills in any gaps from rate limiting
```

### Running the analysis

```bash
python main.py
```

This runs all three analyses and saves plots to the `output/` directory.

---

## Project Structure

```
F1-Team-Performance-Analyzer/
├── README.md
├── requirements.txt
├── .gitignore
├── collect_data.py          # FastF1 data collection script
├── supplement_data.py       # Fills gaps when API is rate-limited
├── f1_analyzer.py           # Core analysis functions (all three)
├── main.py                  # Runs analyses and generates plots
├── tests/
│   └── test_f1_analyzer.py  # Unit tests (pytest)
└── data/
    ├── race_results.json    # 4,220 race result entries (2015–2024)
    ├── budgets.json         # Estimated constructor budgets by year
    ├── race_conditions.json # Wet/mixed race classifications
    └── circuit_types.json   # Street/permanent/hybrid circuit labels
```

---

## Function Descriptions

### 1. `fetch_team_season_stats(team_name, year_range)`
Pulls race-by-race data for a given constructor across a range of seasons and returns summary stats like average finish position, points per race, and DNF rate.

**Parameters:**
- `team_name` (str) — Constructor name (e.g. `"Red Bull Racing"`, `"Mercedes"`). Flexible matching supports aliases and partial names.
- `year_range` (tuple) — `(start_year, end_year)` inclusive, e.g. `(2020, 2024)`.

**Returns:** dict with per-season breakdowns and overall aggregates including races, avg finish, total points, wins, podiums, DNF rate.

### 2. `compare_performance_vs_budget(teams, season)`
Takes team results alongside estimated constructor budgets and calculates a rough efficiency score. In other words, who's getting the most out of what they're spending.

**Parameters:**
- `teams` (list of str) — Constructor names to compare.
- `season` (int) — Season year.

**Returns:** list of dicts sorted by efficiency (points per million USD), each containing team name, budget, total points, avg finish, and efficiency rank.

### 3. `detect_condition_tendencies(team_name)`
Looks at a team's historical results broken down by race conditions (wet, dry, mixed) and circuit type to spot any consistent patterns that don't show up in the overall standings.

**Parameters:**
- `team_name` (str) — Constructor name.

**Returns:** dict with performance stats grouped by weather condition (wet/dry/mixed) and circuit type (street/permanent/hybrid), plus condition deltas showing how much better or worse a team performs in wet vs dry conditions.

---

## Data Sources

- **FastF1 API** — race results, finish positions, DNF status (2015–2024)
- **Constructor budget estimates** — Forbes, Motorsport.com, RacingNews365 annual reports
- **Weather/condition data** — FIA race reports, F1 broadcast archives
- **Circuit classifications** — manual categorization (street/permanent/hybrid)

### Data schema

```python
race_result = {
    "team_name": str,
    "team_id": str,
    "driver": str,
    "season": int,
    "round": int,
    "race_name": str,
    "circuit": str,
    "finish_position": int,
    "grid_position": int,
    "points": float,
    "dnf": bool,
    "status": str
}
```

---

## Output

Running `main.py` generates six plots in `output/`:

1. **season_performance_trends.png** — Average finish position and points per race over 10 seasons for the top 5 constructors
2. **dnf_rate_comparison.png** — Overall DNF rate by constructor (2015–2024)
3. **budget_vs_points_2024.png** — Scatter plot of budget vs points with trend line
4. **efficiency_trends.png** — Budget efficiency (points per $M) across multiple seasons
5. **condition_performance.png** — Average finish position by weather condition (dry/wet/mixed)
6. **circuit_type_performance.png** — Average finish position by circuit type (street/permanent/hybrid)

---

## Running Tests

The project includes 12 unit tests covering all three core functions.
Install pytest and run:

```bash
pip install pytest
pytest tests/test_f1_analyzer.py -v
```

Tests verify:
- `fetch_team_season_stats` returns correct structure, plausible values, handles aliases, and returns errors for missing teams
- `compare_performance_vs_budget` returns properly ranked and sorted efficiency data with all required keys
- `detect_condition_tendencies` returns condition/circuit breakdowns and handles missing teams gracefully
- `get_available_teams` returns sorted lists and filters by year correctly

---

## Notes
- Budget figures are estimates from public sources and press reporting — not official
- 2015–2019 data collected live from FastF1; 2020–2024 supplemented from official FIA records
- Weather condition classification is based on FIA race reports and broadcast data

---

## AI Attribution

Python file includes an attribution comment in its module docstring describing
which parts were AI-generated. All code was reviewed, tested, and verified by
the author.
