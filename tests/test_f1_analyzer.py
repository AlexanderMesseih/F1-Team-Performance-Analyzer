"""
test_f1_analyzer.py

Unit tests for the three core analysis functions in f1_analyzer.py.
Run with:
    pytest tests/test_f1_analyzer.py

AI attribution: These tests were generated with assistance from
assertions, and expected-value reasoning were produced by the AI.
The author reviewed, ran, and verified all tests pass.
"""

import sys
import os

# Allow imports from the project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from f1_analyzer import (
    fetch_team_season_stats,
    compare_performance_vs_budget,
    detect_condition_tendencies,
    get_available_teams,
)


# -------------------------------------------------------------------
# Tests for fetch_team_season_stats
# -------------------------------------------------------------------

def test_fetch_team_season_stats_returns_correct_structure():
    """fetch_team_season_stats should return a dict with
    team_name, seasons, and overall keys, each containing
    the expected sub-keys."""
    stats = fetch_team_season_stats("Mercedes", (2020, 2022))

    assert isinstance(stats, dict)
    assert "team_name" in stats
    assert "seasons" in stats
    assert "overall" in stats

    # Check that every requested season is present
    for year in range(2020, 2023):
        assert year in stats["seasons"], f"Missing season {year}"

    # Check that each season summary has required keys
    required = [
        "races", "avg_finish", "total_points",
        "wins", "podiums", "dnf_rate",
    ]
    for year in range(2020, 2023):
        for key in required:
            assert key in stats["seasons"][year], (
                f"Season {year} missing key '{key}'"
            )


def test_fetch_team_season_stats_overall_values_are_plausible():
    """Overall stats for Mercedes (2015-2024) should reflect
    their known dominance: many wins, low avg finish, etc."""
    stats = fetch_team_season_stats("Mercedes", (2015, 2024))
    overall = stats["overall"]

    assert overall["races"] > 100, "Mercedes should have 100+ races"
    assert 1 <= overall["avg_finish"] <= 20, "avg_finish out of range"
    assert overall["wins"] > 30, "Mercedes should have many wins"
    assert overall["podiums"] > overall["wins"], (
        "Podiums should exceed wins"
    )
    assert 0 <= overall["dnf_rate"] <= 1, "dnf_rate should be 0-1"


def test_fetch_team_season_stats_alias_matching():
    """Common aliases like 'Red Bull' should match 'Red Bull Racing'."""
    stats = fetch_team_season_stats("Red Bull", (2023, 2024))

    assert "error" not in stats, f"Alias failed: {stats.get('error')}"
    assert "Red Bull" in stats["team_name"]


def test_fetch_team_season_stats_missing_team_returns_error():
    """Querying a non-existent team should return an error key
    rather than raising an exception."""
    stats = fetch_team_season_stats("NonExistentTeam", (2015, 2024))

    assert "error" in stats
    assert stats["seasons"] == {}


# -------------------------------------------------------------------
# Tests for compare_performance_vs_budget
# -------------------------------------------------------------------

def test_compare_performance_vs_budget_returns_ranked_list():
    """Should return a list sorted by efficiency with proper ranks."""
    result = compare_performance_vs_budget(
        ["Mercedes", "Ferrari", "Red Bull Racing"], 2023
    )

    assert isinstance(result, list)
    assert len(result) == 3

    # Check that efficiency ranks are 1, 2, 3
    ranks = sorted(entry["efficiency_rank"] for entry in result)
    assert ranks == [1, 2, 3], f"Expected ranks [1,2,3], got {ranks}"


def test_compare_performance_vs_budget_sorted_by_efficiency():
    """The returned list should be sorted by points_per_million
    in descending order."""
    result = compare_performance_vs_budget(
        ["Mercedes", "Ferrari", "McLaren"], 2023
    )

    efficiencies = [entry["points_per_million"] for entry in result]
    assert efficiencies == sorted(efficiencies, reverse=True), (
        "Results should be sorted by efficiency descending"
    )


def test_compare_performance_vs_budget_has_required_keys():
    """Each entry in the result should contain all expected keys."""
    result = compare_performance_vs_budget(["Ferrari"], 2023)

    assert len(result) == 1
    entry = result[0]
    for key in ("team_name", "budget_million_usd", "total_points",
                "points_per_million", "efficiency_rank"):
        assert key in entry, f"Missing key '{key}'"


# -------------------------------------------------------------------
# Tests for detect_condition_tendencies
# -------------------------------------------------------------------

def test_detect_condition_tendencies_returns_condition_breakdown():
    """Should return a dict with by_condition containing at least
    'dry' (since every team has dry-weather races)."""
    result = detect_condition_tendencies("Ferrari")

    assert isinstance(result, dict)
    assert "by_condition" in result
    assert "dry" in result["by_condition"], "Missing 'dry' condition"

    dry = result["by_condition"]["dry"]
    assert dry["races"] > 0, "Should have dry races"
    assert 1 <= dry["avg_finish"] <= 20, "avg_finish out of range"


def test_detect_condition_tendencies_has_circuit_types():
    """Should return a by_circuit_type breakdown with at least
    'permanent' (the most common circuit type)."""
    result = detect_condition_tendencies("McLaren")

    assert "by_circuit_type" in result
    assert "permanent" in result["by_circuit_type"]

    perm = result["by_circuit_type"]["permanent"]
    assert perm["races"] > 0
    for key in ("avg_finish", "avg_points", "dnf_rate"):
        assert key in perm, f"Missing key '{key}' in circuit type"


def test_detect_condition_tendencies_missing_team():
    """Querying a team with no data should return an error key."""
    result = detect_condition_tendencies("NonExistentTeam")

    assert "error" in result
    assert result["by_condition"] == {}
    assert result["by_circuit_type"] == {}


# -------------------------------------------------------------------
# Tests for get_available_teams
# -------------------------------------------------------------------

def test_get_available_teams_returns_sorted_list():
    """get_available_teams should return a sorted list of strings."""
    teams = get_available_teams()

    assert isinstance(teams, list)
    assert len(teams) > 0
    assert teams == sorted(teams), "Teams should be sorted"


def test_get_available_teams_filters_by_year():
    """Filtering by 2024 should return only teams that raced
    in 2024 and exclude defunct teams."""
    teams = get_available_teams(2024)

    assert "Ferrari" in teams
    assert "McLaren" in teams
    assert "Red Bull Racing" in teams
    # Defunct teams should not appear
    assert "Lotus F1" not in teams
    assert "Manor Marussia" not in teams
