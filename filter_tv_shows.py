#!/usr/bin/env python3
"""
Fetch TV shows from TMDb and create two separate filtered lists.

Filter 1 - Big Budget (estimated by episode count × type):
  - High production value shows (regardless of rating)
  - Current year onwards only

Filter 2 - Highly Rated & Popular:
  - Rating >= 7.5
  - Vote count >= 100,000
  - Current year onwards only

Both lists are combined in one JSON file.

Required environment variable:
  TMDB_API_KEY - Your TMDb API Read Access Token (starts with "eyJ...")
"""

import requests
import json
import os
import sys
import time
from datetime import datetime, timezone


# ===== CONFIGURATION =====

API_KEY = os.environ.get("TMDB_API_KEY")
if not API_KEY:
    print("ERROR: Environment variable TMDB_API_KEY is not set.")
    print("       Set it with: export TMDB_API_KEY='your_read_access_token_here'")
    print("       Use your API Read Access Token (starts with eyJ...), NOT your API Key.")
    sys.exit(1)

OUTPUT_FILE = "filtered_tv_shows.json"

# Filter 1: High value productions
# TV shows don't have public budgets, so we use:
# - High vote count AND high rating as proxy for "prestige" productions
# - OR shows from networks known for big budgets (HBO, Netflix, Apple TV+, etc.)
MIN_VOTES_PRESTIGE = 50000
MIN_RATING_PRESTIGE = 7.0
PRESTIGE_NETWORKS = [
    "HBO", "Netflix", "Apple TV+", "Amazon", "Disney+",
    "Paramount+", "Max", "Hulu", "Peacock"
]

# Filter 2: Highly rated + popular
MIN_RATING = 7.5
MIN_VOTES = 100000

# ===== TMDb API SETUP =====

BASE_URL = "https://api.themoviedb.org/3"
HEADERS = {
    "accept": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}


# ===== FUNCTIONS =====

def get_tv_show_ids(pages=15):
    """
    Fetch TV show IDs from multiple TMDb lists.
    Only includes shows from the current year onwards.
    Returns a list of unique TV show IDs.
    """
    tv_ids = set()
    current_year = datetime.now().year

    # Standard endpoints
    endpoints = [
        "/tv/popular",
        "/tv/top_rated",
        "/tv/on_the_air",
        "/tv/airing_today",
    ]

    # Discover endpoints with built-in date filter
    discover_endpoints = [
        f"/discover/tv?sort_by=popularity.desc&first_air_date.gte={current_year}-01-01",
        f"/discover/tv?sort_by=vote_average.desc&first_air_date.gte={current_year}-01-01&vote_count.gte=100",
        f"/discover/tv?sort_by=first_air_date.desc&first_air_date.gte={current_year}-01-01",
    ]

    all_endpoints = endpoints + discover_endpoints

    for endpoint in all_endpoints:
        for page in range(1, pages + 1):
            if "?" in endpoint:
                url = f"{BASE_URL}{endpoint}&page={page}"
            else:
                url = f"{BASE_URL}{endpoint}?page={page}"

            try:
                response = requests.get(url, headers=HEADERS, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    for show in data.get("results", []):
                        # For discover endpoints, TMDb already filtered by year
                        if endpoint in endpoints:
                            first_air = show.get("first_air_date", "")
                            if not first_air or first_air < f"{current_year}-01-01":
                                continue
                        tv_ids.add(show["id"])

                elif response.status_code == 401:
                    print("ERROR: Invalid API key.")
                    sys.exit(1)
                elif response.status_code == 429:
                    print("WARNING: Rate limit reached. Waiting 2 seconds...")
                    time.sleep(2)
                else:
                    print(f"WARNING: Could not fetch {url} (HTTP {response.status_code})")

            except requests.exceptions.RequestException as e:
                print(f"WARNING: Request failed for {url}: {e}")
                time.sleep(1)

    return list(tv_ids)


def simplify_show(show):
    """Create a simplified TV show object with relevant fields."""
    poster_path = show.get("poster_path")

    # Get networks/production companies
    networks = [net["name"] for net in show.get("networks", [])]

    # Get creators
    creators = [creator["name"] for creator in show.get("created_by", [])]

    return {
        "title": show.get("name"),
        "original_title": show.get("original_name"),
        "tmdb_id": show.get("id"),
        "first_air_date": show.get("first_air_date"),
        "last_air_date": show.get("last_air_date"),
        "genres": [genre["name"] for genre in show.get("genres", [])],
        "networks": networks,
        "creators": creators,
        "number_of_seasons": show.get("number_of_seasons", 0),
        "number_of_episodes": show.get("number_of_episodes", 0),
        "episode_runtime": show.get("episode_run_time", []),
        "rating": show.get("vote_average", 0),
        "votes": show.get("vote_count", 0),
        "status": show.get("status"),
        "type": show.get("type"),
        "poster_url": f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None,
        "overview": show.get("overview")
    }


def is_prestige_production(show):
    """Determine if a show is a high-value/prestige production."""
    networks = show.get("networks", [])

    # Check if it's on a known prestige network
    has_prestige_network = any(
        any(prestige.lower() in network.lower() for prestige in PRESTIGE_NETWORKS)
        for network in networks
    )

    # High vote count + good rating indicates significant investment
    has_high_engagement = (
        show.get("votes", 0) >= MIN_VOTES_PRESTIGE and
        show.get("rating", 0) >= MIN_RATING_PRESTIGE
    )

    # Documentary or reality shows usually have lower budgets
    genres = [g.lower() for g in show.get("genres", [])]
    is_low_cost_genre = "documentary" in genres or "reality" in genres

    return (has_prestige_network or has_high_engagement) and not is_low_cost_genre


def fetch_and_filter_shows(tv_ids):
    """
    Fetch details for each TV show and sort into respective lists.
    Only includes shows from the current year onwards.
    Returns two lists: prestige and highly_rated.
    """
    prestige = []
    highly_rated = []
    total = len(tv_ids)
    current_year = datetime.now().year

    for i, tv_id in enumerate(tv_ids):
        if i % 100 == 0:
            print(f"  Processing show {i+1}/{total}...")

        url = f"{BASE_URL}/tv/{tv_id}"

        try:
            response = requests.get(url, headers=HEADERS, timeout=30)

            if response.status_code == 429:
                print("  Rate limited. Waiting 2 seconds...")
                time.sleep(2)
                response = requests.get(url, headers=HEADERS, timeout=30)

            if response.status_code != 200:
                continue

            show = response.json()

            # Skip shows that started before current year
            first_air = show.get("first_air_date", "")
            if not first_air or first_air < f"{current_year}-01-01":
                continue

            rating = show.get("vote_average", 0)
            votes = show.get("vote_count", 0)

            # Skip shows without enough data
            if votes == 0:
                continue

            simplified = simplify_show(show)

            # Filter 1: Prestige productions
            if is_prestige_production(show):
                prestige.append(simplified)
                networks_str = ", ".join(show.get("networks", ["Unknown"]))
                print(f"  🎬 PRESTIGE: {show.get('name')} ({first_air}) - "
                      f"Networks: {networks_str} - {rating} ({votes:,} votes)")

            # Filter 2: Highly rated
            if rating >= MIN_RATING and votes >= MIN_VOTES:
                highly_rated.append(simplified)
                print(f"  ⭐ HIGH RATED: {show.get('name')} ({first_air}) - {rating} ({votes:,} votes)")

        except requests.exceptions.RequestException as e:
            print(f"  Request failed for TV show {tv_id}: {e}")
        except Exception as e:
            print(f"  Unexpected error for TV show {tv_id}: {e}")

    # Sort by first air date (newest first)
    prestige.sort(key=lambda x: x.get("first_air_date", ""), reverse=True)
    highly_rated.sort(key=lambda x: x.get("first_air_date", ""), reverse=True)

    return prestige, highly_rated


def main():
    current_year = datetime.now().year

    print("=" * 60)
    print("FILTERED TV SHOWS GENERATOR")
    print("=" * 60)
    print()
    print(f"Year filter: {current_year} onwards only")
    print()
    print("Filter 1 - Prestige Productions:")
    print(f"  High-value shows (premium networks OR strong engagement)")
    print(f"  Networks: {', '.join(PRESTIGE_NETWORKS)}")
    print(f"  OR Votes >= {MIN_VOTES_PRESTIGE:,} + Rating >= {MIN_RATING_PRESTIGE}")
    print()
    print("Filter 2 - Highly Rated & Popular:")
    print(f"  Rating >= {MIN_RATING}")
    print(f"  Votes >= {MIN_VOTES:,}")
    print()

    print("Fetching TV shows from TMDb...")
    tv_ids = get_tv_show_ids(pages=10)
    print(f"Found {len(tv_ids)} unique TV shows to evaluate.\n")

    print("Analyzing and filtering...")
    prestige, highly_rated = fetch_and_filter_shows(tv_ids)

    output = {
        "metadata": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "current_year": current_year,
            "source": "TMDb API",
            "note": "Only includes TV shows from current year onwards. TV budgets are not public, so 'prestige' is estimated by networks and engagement.",
            "filters": {
                "prestige": {
                    "description": f"High-value productions from {current_year} (premium networks or strong engagement)",
                    "prestige_networks": PRESTIGE_NETWORKS,
                    "min_votes": MIN_VOTES_PRESTIGE,
                    "min_rating": MIN_RATING_PRESTIGE,
                    "year_from": current_year,
                    "count": len(prestige)
                },
                "highly_rated": {
                    "description": f"TV shows from {current_year} with rating >= {MIN_RATING} and >= {MIN_VOTES:,} votes",
                    "min_rating": MIN_RATING,
                    "min_votes": MIN_VOTES,
                    "year_from": current_year,
                    "count": len(highly_rated)
                }
            }
        },
        "prestige": prestige,
        "highly_rated": highly_rated
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print("DONE!")
    print(f"  Prestige productions:  {len(prestige)}")
    print(f"  Highly rated shows:    {len(highly_rated)}")
    print(f"  Output saved to:       {OUTPUT_FILE}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
