"""
f1_analyzer.py

Core analysis functions for the F1 Team Performance Analyzer.
Provides three main functions:
  - fetch_team_season_stats: aggregate race stats per constructor
  - compare_performance_vs_budget: efficiency scoring against budget
  - detect_condition_tendencies: performance by weather/circuit type
"""

import json
import os
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------

def _load_json(filename):
    """Load a JSON file from the data directory."""
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r") as f:
        return json.load(f)


def _load_race_results():
    """Load race results collected by collect_data.py."""
    return _load_json("race_results.json")


def _load_budgets():
    """Load constructor budget estimates."""
    data = _load_json("budgets.json")
    data.pop("_description", None)
    return data


def _load_race_conditions():
    """Load race weather conditions."""
    data = _load_json("race_conditions.json")
    data.pop("_description", None)
    return data


def _load_circuit_types():
    """Load circuit type classifications."""
    data = _load_json("circuit_types.json")
    data.pop("_description", None)
    return data


def _normalize_team_name(name):
    """Normalize team name for flexible matching."""
    return name.strip().lower().replace("-", " ").replace("_", " ")


def _team_matches(record_team, query_team):
    """Check if a result record's team name matches the queried team."""
    rt = _normalize_team_name(record_team)
    qt = _normalize_team_name(query_team)

    if qt == rt:
        return True

    # Handle common abbreviations / alternate names
    aliases = {
        "red bull": ["red bull racing", "red bull"],
        "mercedes": ["mercedes", "mercedes amg"],
        "alpine": ["alpine", "alpine f1 team"],
        "alfa romeo": ["alfa romeo racing", "alfa romeo"],
        "alphatauri": ["alphatauri", "scuderia alphatauri"],
        "toro rosso": ["toro rosso", "scuderia toro rosso"],
        "force india": ["force india", "racing point force india"],
        "racing point": ["racing point"],
        "aston martin": ["aston martin", "aston martin aramco"],
        "haas": ["haas f1 team", "haas"],
        "sauber": ["sauber", "kick sauber"],
        "rb": ["rb", "visa cashapp rb", "visa cash app rb"],
        "renault": ["renault"],
        "lotus": ["lotus f1", "lotus"],
        "manor": ["manor marussia", "manor racing", "manor"],
        "mclaren": ["mclaren"],
        "ferrari": ["ferrari"],
        "williams": ["williams"],
    }

    for group_aliases in aliases.values():
        norm_aliases = [_normalize_team_name(a) for a in group_aliases]
        if qt in norm_aliases and rt in norm_aliases:
            return True

    # Substring matching as fallback
    if qt in rt or rt in qt:
        return True

    return False


def get_available_teams(year=None):
    """Return a sorted list of team names present in the dataset.

    Parameters
    ----------
    year : int or None
        If given, only return teams that raced in that season.
    """
    results = _load_race_results()
    teams = set()
    for r in results:
        if year is not None and r["season"] != year:
            continue
        teams.add(r["team_name"])
    return sorted(teams)


# ---------------------------------------------------------------------------
# Function 1: fetch_team_season_stats
# ---------------------------------------------------------------------------

def fetch_team_season_stats(team_name, year_range):
    """Pull race-by-race data for a constructor across a range of seasons.

    Parameters
    ----------
    team_name : str
        Constructor name (e.g. "Red Bull Racing", "Mercedes", "Ferrari").
        Flexible matching is used — partial names and common aliases work.
    year_range : tuple or list
        (start_year, end_year) inclusive, e.g. (2020, 2024).

    Returns
    -------
    dict with keys:
        - "team_name": str, matched team name
        - "seasons": dict mapping year -> season summary
        - "overall": dict with aggregate stats across all requested seasons

    Each season summary contains:
        - "races": int, number of races entered
        - "avg_finish": float, average finishing position
        - "best_finish": int, best single finishing position
        - "worst_finish": int, worst finishing position
        - "total_points": float
        - "points_per_race": float, average points per race entry
        - "dnf_count": int
        - "dnf_rate": float, fraction of entries that were DNFs
        - "podiums": int, number of top-3 finishes
        - "wins": int, number of race wins
    """
    results = _load_race_results()
    start, end = int(year_range[0]), int(year_range[1])

    # Filter to matching team and year range
    filtered = [
        r for r in results
        if _team_matches(r["team_name"], team_name)
        and start <= r["season"] <= end
    ]

    if not filtered:
        return {
            "team_name": team_name,
            "seasons": {},
            "overall": None,
            "error": f"No data found for '{team_name}' in {start}-{end}",
        }

    matched_name = filtered[0]["team_name"]

    # Group by season
    by_season = defaultdict(list)
    for r in filtered:
        by_season[r["season"]].append(r)

    def _summarize(entries):
        positions = [
            e["finish_position"] for e in entries
            if e["finish_position"] is not None and not e["dnf"]
        ]
        total_points = sum(e["points"] for e in entries)
        dnf_count = sum(1 for e in entries if e["dnf"])
        race_count = len(entries)

        return {
            "races": race_count,
            "avg_finish": round(sum(positions) / len(positions), 2) if positions else None,
            "best_finish": min(positions) if positions else None,
            "worst_finish": max(positions) if positions else None,
            "total_points": total_points,
            "points_per_race": round(total_points / race_count, 2) if race_count else 0,
            "dnf_count": dnf_count,
            "dnf_rate": round(dnf_count / race_count, 3) if race_count else 0,
            "podiums": sum(1 for p in positions if p <= 3),
            "wins": sum(1 for p in positions if p == 1),
        }

    seasons = {}
    for year in sorted(by_season.keys()):
        seasons[year] = _summarize(by_season[year])

    overall = _summarize(filtered)

    return {
        "team_name": matched_name,
        "seasons": seasons,
        "overall": overall,
    }


# ---------------------------------------------------------------------------
# Function 2: compare_performance_vs_budget
# ---------------------------------------------------------------------------

def compare_performance_vs_budget(teams, season):
    """Compare constructor results against estimated budgets.

    Parameters
    ----------
    teams : list of str
        List of constructor names to compare.
    season : int
        Season year to analyze.

    Returns
    -------
    list of dict, one per team, sorted by efficiency score (descending).
    Each dict contains:
        - "team_name": str
        - "budget_million_usd": float or None
        - "total_points": float
        - "avg_finish": float
        - "points_per_million": float — main efficiency metric
        - "efficiency_rank": int
    """
    results = _load_race_results()
    budgets = _load_budgets()

    season_budgets = budgets.get(str(season), {})

    team_data = []

    for team in teams:
        entries = [
            r for r in results
            if _team_matches(r["team_name"], team)
            and r["season"] == season
        ]

        if not entries:
            team_data.append({
                "team_name": team,
                "budget_million_usd": None,
                "total_points": 0,
                "avg_finish": None,
                "points_per_million": 0,
                "efficiency_rank": None,
                "note": f"No race data found for {season}",
            })
            continue

        matched_name = entries[0]["team_name"]

        positions = [
            e["finish_position"] for e in entries
            if e["finish_position"] is not None and not e["dnf"]
        ]
        total_points = sum(e["points"] for e in entries)
        avg_finish = round(sum(positions) / len(positions), 2) if positions else None

        # Find budget — try exact match first, then fuzzy
        budget = None
        for budget_team, budget_val in season_budgets.items():
            if _team_matches(budget_team, team):
                budget = budget_val
                break

        ppm = round(total_points / budget, 4) if budget and budget > 0 else 0

        team_data.append({
            "team_name": matched_name,
            "budget_million_usd": budget,
            "total_points": total_points,
            "avg_finish": avg_finish,
            "points_per_million": ppm,
        })

    # Sort by efficiency (points per million), descending
    team_data.sort(key=lambda x: x.get("points_per_million", 0), reverse=True)

    for i, td in enumerate(team_data, 1):
        td["efficiency_rank"] = i

    return team_data


# ---------------------------------------------------------------------------
# Function 3: detect_condition_tendencies
# ---------------------------------------------------------------------------

def detect_condition_tendencies(team_name):
    """Analyze a team's performance by race condition and circuit type.

    Parameters
    ----------
    team_name : str
        Constructor name.

    Returns
    -------
    dict with keys:
        - "team_name": str
        - "by_condition": dict mapping "wet"/"dry"/"mixed" ->
              {"races", "avg_finish", "avg_points", "dnf_rate"}
        - "by_circuit_type": dict mapping "street"/"permanent"/"hybrid" ->
              {"races", "avg_finish", "avg_points", "dnf_rate"}
        - "condition_delta": dict showing performance difference
              (wet vs dry, mixed vs dry) in average finish position
    """
    results = _load_race_results()
    conditions = _load_race_conditions()
    circuit_types = _load_circuit_types()

    # Filter to team
    team_entries = [
        r for r in results
        if _team_matches(r["team_name"], team_name)
    ]

    if not team_entries:
        return {
            "team_name": team_name,
            "by_condition": {},
            "by_circuit_type": {},
            "condition_delta": {},
            "error": f"No data found for '{team_name}'",
        }

    matched_name = team_entries[0]["team_name"]

    # Attach condition and circuit type to each entry
    for entry in team_entries:
        season_conds = conditions.get(str(entry["season"]), {})
        entry["condition"] = season_conds.get(str(entry["round"]), "dry")

        circuit = entry.get("circuit", "")
        entry["circuit_type"] = circuit_types.get(circuit, "permanent")

    def _group_stats(entries, key):
        groups = defaultdict(list)
        for e in entries:
            groups[e[key]].append(e)

        stats = {}
        for group_name, group_entries in sorted(groups.items()):
            positions = [
                e["finish_position"] for e in group_entries
                if e["finish_position"] is not None and not e["dnf"]
            ]
            total_points = sum(e["points"] for e in group_entries)
            dnf_count = sum(1 for e in group_entries if e["dnf"])
            race_count = len(group_entries)

            stats[group_name] = {
                "races": race_count,
                "avg_finish": round(sum(positions) / len(positions), 2) if positions else None,
                "avg_points": round(total_points / race_count, 2) if race_count else 0,
                "dnf_rate": round(dnf_count / race_count, 3) if race_count else 0,
            }
        return stats

    by_condition = _group_stats(team_entries, "condition")
    by_circuit = _group_stats(team_entries, "circuit_type")

    # Calculate condition deltas (positive = worse in wet/mixed vs dry)
    dry_avg = by_condition.get("dry", {}).get("avg_finish")
    condition_delta = {}
    for cond in ("wet", "mixed"):
        cond_avg = by_condition.get(cond, {}).get("avg_finish")
        if dry_avg is not None and cond_avg is not None:
            condition_delta[f"{cond}_vs_dry"] = round(cond_avg - dry_avg, 2)

    return {
        "team_name": matched_name,
        "by_condition": by_condition,
        "by_circuit_type": by_circuit,
        "condition_delta": condition_delta,
    }
