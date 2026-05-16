"""
collect_data.py

Uses the FastF1 library to fetch race results for all constructors
from 2015 to 2024 and saves them to data/race_results.json.

Run this script once to populate the data directory:
    python collect_data.py

AI attribution: This script was generated with assistance from
loading, result parsing, and progress-saving logic were produced
by the AI. The author reviewed, tested, and verified all outputs.
"""

import json
import os
import fastf1

# Cache FastF1 data to speed up repeated runs
CACHE_DIR = os.path.join(os.path.dirname(__file__), ".fastf1_cache")
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

OUTPUT_PATH = os.path.join(DATA_DIR, "race_results.json")

YEAR_RANGE = range(2015, 2025)  # 2015 through 2024


def collect_season(year):
    """Collect race results for every round in a given season."""
    season_results = []
    try:
        schedule = fastf1.get_event_schedule(year, include_testing=False)
    except Exception as e:
        print(f"  [!] Could not load schedule for {year}: {e}")
        return season_results

    # Filter to only race rounds (RoundNumber > 0)
    race_rounds = schedule[schedule["RoundNumber"] > 0]

    for _, event in race_rounds.iterrows():
        round_num = int(event["RoundNumber"])
        race_name = event.get("EventName", f"Round {round_num}")
        circuit = event.get("Location", "Unknown")

        print(f"  Round {round_num}: {race_name} ({circuit})")

        try:
            session = fastf1.get_session(year, round_num, "R")
            session.load(
                telemetry=False,
                weather=False,
                messages=False,
            )
        except Exception as e:
            print(f"    [!] Failed to load session: {e}")
            continue

        results = session.results
        if results is None or results.empty:
            print("    [!] No results available")
            continue

        for _, row in results.iterrows():
            status = str(row.get("Status", ""))
            is_dnf = status not in ("Finished", "") and not status.startswith("+")

            position = row.get("Position")
            if position is not None:
                try:
                    position = int(float(position))
                except (ValueError, TypeError):
                    position = None

            grid = row.get("GridPosition")
            if grid is not None:
                try:
                    grid = int(float(grid))
                except (ValueError, TypeError):
                    grid = None

            points = row.get("Points", 0.0)
            try:
                points = float(points)
            except (ValueError, TypeError):
                points = 0.0

            season_results.append({
                "team_name": str(row.get("TeamName", "Unknown")),
                "team_id": str(row.get("TeamId", "unknown")),
                "driver": str(row.get("Abbreviation", "UNK")),
                "season": year,
                "round": round_num,
                "race_name": race_name,
                "circuit": circuit,
                "finish_position": position,
                "grid_position": grid,
                "points": points,
                "dnf": is_dnf,
                "status": status,
            })

    return season_results


def main():
    all_results = []

    for year in YEAR_RANGE:
        print(f"\n{'='*50}")
        print(f"Collecting {year} season data...")
        print(f"{'='*50}")

        season_data = collect_season(year)
        all_results.extend(season_data)
        print(f"  -> {len(season_data)} result entries collected")

        # Save progress after each season
        with open(OUTPUT_PATH, "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"  -> Progress saved ({len(all_results)} total entries)")

    print(f"\nDone! {len(all_results)} total entries saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
