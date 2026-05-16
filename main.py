"""
main.py

F1 Team Performance Analyzer — main demo script.

Runs all three analysis functions and generates visualizations
showing constructor performance trends, budget efficiency, and
condition-based tendencies over the 2015–2024 seasons.

Usage:
    python main.py

AI attribution: This script was generated with assistance from
analysis orchestration, and output formatting were produced by
the AI based on the project spec. The author reviewed, tested,
and verified all outputs.
"""

import os
import json
import matplotlib
matplotlib.use("Agg")  # non-interactive backend for saving plots
import matplotlib.pyplot as plt
import numpy as np

from f1_analyzer import (
    fetch_team_season_stats,
    compare_performance_vs_budget,
    detect_condition_tendencies,
    get_available_teams,
)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Top teams to analyze across the full decade
TOP_TEAMS = [
    "Red Bull Racing",
    "Mercedes",
    "Ferrari",
    "McLaren",
    "Williams",
]

# All teams for budget comparison (will vary by year)
ALL_TEAMS_2023 = [
    "Red Bull Racing",
    "Mercedes",
    "Ferrari",
    "McLaren",
    "Aston Martin",
    "Alpine",
    "Williams",
    "AlphaTauri",
    "Alfa Romeo",
    "Haas F1 Team",
]


def print_header(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


# -----------------------------------------------------------------------
# Analysis 1: Team season stats over 10 years
# -----------------------------------------------------------------------

def run_season_stats_analysis():
    """Fetch and display season stats for top teams, then plot trends."""
    print_header("ANALYSIS 1: Constructor Performance (2015–2024)")

    team_stats = {}
    for team in TOP_TEAMS:
        stats = fetch_team_season_stats(team, (2015, 2024))
        team_stats[team] = stats

        if stats.get("error"):
            print(f"  {team}: {stats['error']}")
            continue

        overall = stats["overall"]
        print(f"  {stats['team_name']}:")
        print(f"    Races: {overall['races']}")
        print(f"    Avg Finish: {overall['avg_finish']}")
        print(f"    Total Points: {overall['total_points']}")
        print(f"    Wins: {overall['wins']} | Podiums: {overall['podiums']}")
        print(f"    DNF Rate: {overall['dnf_rate']:.1%}")
        print()

    # --- Plot 1a: Average finish position over time ---
    fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    colors = ["#1E41FF", "#00D2BE", "#DC0000", "#FF8700", "#005AFF"]

    for team, color in zip(TOP_TEAMS, colors):
        stats = team_stats[team]
        if stats.get("error"):
            continue
        years = sorted(stats["seasons"].keys())
        avg_finishes = [stats["seasons"][y]["avg_finish"] for y in years]
        axes[0].plot(years, avg_finishes, marker="o", label=team, color=color, linewidth=2)

    axes[0].set_ylabel("Average Finish Position")
    axes[0].set_title("Average Finish Position by Season (lower = better)")
    axes[0].legend(loc="upper right", fontsize=8)
    axes[0].invert_yaxis()
    axes[0].grid(True, alpha=0.3)

    # --- Plot 1b: Points per race over time ---
    for team, color in zip(TOP_TEAMS, colors):
        stats = team_stats[team]
        if stats.get("error"):
            continue
        years = sorted(stats["seasons"].keys())
        ppr = [stats["seasons"][y]["points_per_race"] for y in years]
        axes[1].plot(years, ppr, marker="s", label=team, color=color, linewidth=2)

    axes[1].set_xlabel("Season")
    axes[1].set_ylabel("Points per Race Entry")
    axes[1].set_title("Points per Race Entry by Season")
    axes[1].legend(loc="upper left", fontsize=8)
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "season_performance_trends.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  -> Plot saved: {path}")

    # --- Plot 1c: DNF rate comparison bar chart ---
    fig, ax = plt.subplots(figsize=(10, 6))
    team_names = []
    dnf_rates = []
    bar_colors = []
    for team, color in zip(TOP_TEAMS, colors):
        stats = team_stats[team]
        if stats.get("error"):
            continue
        team_names.append(team)
        dnf_rates.append(stats["overall"]["dnf_rate"] * 100)
        bar_colors.append(color)

    bars = ax.bar(team_names, dnf_rates, color=bar_colors, edgecolor="black", linewidth=0.5)
    ax.set_ylabel("DNF Rate (%)")
    ax.set_title("Overall DNF Rate by Constructor (2015–2024)")
    ax.grid(True, axis="y", alpha=0.3)

    for bar, rate in zip(bars, dnf_rates):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                f"{rate:.1f}%", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "dnf_rate_comparison.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  -> Plot saved: {path}")


# -----------------------------------------------------------------------
# Analysis 2: Budget efficiency
# -----------------------------------------------------------------------

def run_budget_analysis():
    """Compare team performance vs budget for recent seasons."""
    print_header("ANALYSIS 2: Budget Efficiency Comparison")

    seasons_to_compare = [2021, 2022, 2023, 2024]
    all_results = {}

    for season in seasons_to_compare:
        available = get_available_teams(season)
        if not available:
            print(f"  No data available for {season}")
            continue

        comparison = compare_performance_vs_budget(available, season)
        all_results[season] = comparison

        print(f"  {season} Season — Efficiency Rankings:")
        print(f"  {'Rank':<5} {'Team':<25} {'Points':<10} {'Budget ($M)':<14} {'Pts/$M':<10}")
        print(f"  {'-'*64}")
        for entry in comparison:
            budget_str = f"${entry['budget_million_usd']}M" if entry["budget_million_usd"] else "N/A"
            print(f"  {entry['efficiency_rank']:<5} {entry['team_name']:<25} "
                  f"{entry['total_points']:<10.0f} {budget_str:<14} "
                  f"{entry['points_per_million']:<10.4f}")
        print()

    # --- Plot 2a: Scatter plot of budget vs points (most recent season) ---
    if all_results:
        latest = max(all_results.keys())
        data = all_results[latest]

        fig, ax = plt.subplots(figsize=(10, 7))
        budgets = []
        points = []
        names = []
        for d in data:
            if d["budget_million_usd"] and d["total_points"] > 0:
                budgets.append(d["budget_million_usd"])
                points.append(d["total_points"])
                names.append(d["team_name"])

        ax.scatter(budgets, points, s=120, c="#1E41FF", edgecolors="black", zorder=5)

        for i, name in enumerate(names):
            ax.annotate(name, (budgets[i], points[i]),
                        textcoords="offset points", xytext=(8, 5), fontsize=8)

        # Trend line
        if len(budgets) > 1:
            z = np.polyfit(budgets, points, 1)
            p = np.poly1d(z)
            x_line = np.linspace(min(budgets) - 20, max(budgets) + 20, 100)
            ax.plot(x_line, p(x_line), "--", color="gray", alpha=0.5, label="Trend")

        ax.set_xlabel("Estimated Budget (Million USD)")
        ax.set_ylabel("Total Constructor Points")
        ax.set_title(f"Budget vs Performance — {latest} Season")
        ax.grid(True, alpha=0.3)
        ax.legend()

        plt.tight_layout()
        path = os.path.join(OUTPUT_DIR, f"budget_vs_points_{latest}.png")
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  -> Plot saved: {path}")

    # --- Plot 2b: Efficiency ranking across multiple seasons ---
    if len(all_results) > 1:
        fig, ax = plt.subplots(figsize=(12, 7))

        # Track which teams appear most
        team_efficiency = {}
        for season, data in sorted(all_results.items()):
            for d in data:
                name = d["team_name"]
                if name not in team_efficiency:
                    team_efficiency[name] = {}
                team_efficiency[name][season] = d["points_per_million"]

        # Only plot teams with data in at least 2 seasons
        for name, efficiencies in team_efficiency.items():
            if len(efficiencies) >= 2:
                years = sorted(efficiencies.keys())
                vals = [efficiencies[y] for y in years]
                ax.plot(years, vals, marker="o", label=name, linewidth=1.5)

        ax.set_xlabel("Season")
        ax.set_ylabel("Points per Million USD")
        ax.set_title("Budget Efficiency Over Time (Points per $M)")
        ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=7)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        path = os.path.join(OUTPUT_DIR, "efficiency_trends.png")
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  -> Plot saved: {path}")


# -----------------------------------------------------------------------
# Analysis 3: Condition tendencies
# -----------------------------------------------------------------------

def run_condition_analysis():
    """Analyze performance tendencies by weather and circuit type."""
    print_header("ANALYSIS 3: Condition & Circuit Tendencies")

    condition_data = {}
    for team in TOP_TEAMS:
        result = detect_condition_tendencies(team)
        condition_data[team] = result

        if result.get("error"):
            print(f"  {team}: {result['error']}")
            continue

        print(f"  {result['team_name']}:")

        if result["by_condition"]:
            print(f"    By weather condition:")
            for cond, stats in result["by_condition"].items():
                print(f"      {cond:<8}: {stats['races']:>3} races, "
                      f"avg finish {stats['avg_finish']}, "
                      f"avg pts {stats['avg_points']}, "
                      f"DNF {stats['dnf_rate']:.1%}")

        if result["condition_delta"]:
            print(f"    Condition deltas (positive = worse than dry):")
            for delta_name, delta_val in result["condition_delta"].items():
                direction = "worse" if delta_val > 0 else "better"
                print(f"      {delta_name}: {delta_val:+.2f} positions ({direction})")

        if result["by_circuit_type"]:
            print(f"    By circuit type:")
            for ctype, stats in result["by_circuit_type"].items():
                print(f"      {ctype:<12}: {stats['races']:>3} races, "
                      f"avg finish {stats['avg_finish']}, "
                      f"avg pts {stats['avg_points']}")
        print()

    # --- Plot 3a: Grouped bar chart — avg finish by condition ---
    conditions = ["dry", "wet", "mixed"]
    fig, ax = plt.subplots(figsize=(12, 7))
    x = np.arange(len(TOP_TEAMS))
    width = 0.25
    cond_colors = {"dry": "#FFD700", "wet": "#4169E1", "mixed": "#808080"}

    for i, cond in enumerate(conditions):
        vals = []
        for team in TOP_TEAMS:
            data = condition_data[team]
            if data.get("error"):
                vals.append(0)
            else:
                avg = data["by_condition"].get(cond, {}).get("avg_finish")
                vals.append(avg if avg else 0)
        bars = ax.bar(x + i * width, vals, width, label=cond.capitalize(),
                      color=cond_colors[cond], edgecolor="black", linewidth=0.5)

    ax.set_xlabel("Constructor")
    ax.set_ylabel("Average Finish Position")
    ax.set_title("Average Finish Position by Weather Condition (2015–2024)")
    ax.set_xticks(x + width)
    ax.set_xticklabels(TOP_TEAMS, rotation=15, ha="right")
    ax.legend()
    ax.invert_yaxis()
    ax.grid(True, axis="y", alpha=0.3)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "condition_performance.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  -> Plot saved: {path}")

    # --- Plot 3b: Circuit type comparison ---
    circuit_types = ["permanent", "street", "hybrid"]
    fig, ax = plt.subplots(figsize=(12, 7))
    ct_colors = {"permanent": "#2E8B57", "street": "#DC143C", "hybrid": "#FF8C00"}

    for i, ctype in enumerate(circuit_types):
        vals = []
        for team in TOP_TEAMS:
            data = condition_data[team]
            if data.get("error"):
                vals.append(0)
            else:
                avg = data["by_circuit_type"].get(ctype, {}).get("avg_finish")
                vals.append(avg if avg else 0)
        ax.bar(x + i * width, vals, width, label=ctype.capitalize(),
               color=ct_colors[ctype], edgecolor="black", linewidth=0.5)

    ax.set_xlabel("Constructor")
    ax.set_ylabel("Average Finish Position")
    ax.set_title("Average Finish Position by Circuit Type (2015–2024)")
    ax.set_xticks(x + width)
    ax.set_xticklabels(TOP_TEAMS, rotation=15, ha="right")
    ax.legend()
    ax.invert_yaxis()
    ax.grid(True, axis="y", alpha=0.3)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "circuit_type_performance.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  -> Plot saved: {path}")


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

def main():
    print("\n" + "="*60)
    print("  F1 TEAM PERFORMANCE ANALYZER")
    print("  Analyzing constructor data from 2015 to 2024")
    print("="*60)

    # Show available teams
    print("\nAvailable teams in dataset:")
    for team in get_available_teams():
        print(f"  - {team}")

    # Run all three analyses
    run_season_stats_analysis()
    run_budget_analysis()
    run_condition_analysis()

    print_header("ANALYSIS COMPLETE")
    print(f"  All plots saved to: {OUTPUT_DIR}/")
    print(f"  Files generated:")
    for f in sorted(os.listdir(OUTPUT_DIR)):
        if f.endswith(".png"):
            print(f"    - {f}")
    print()


if __name__ == "__main__":
    main()
