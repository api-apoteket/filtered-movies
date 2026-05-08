#!/usr/bin/env python3
"""
Fetch TV shows from TMDb and filter by network/prestige only.

Filter - Prestige TV:
  - Shows from major networks/streamers (HBO, Netflix, Apple TV+, etc.)
  - Premiered this year up to today
  - Regardless of rating

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

# Prestige networks/streamers (proxies for high production value)
PRESTIGE_NETWORKS = [
    "HBO",
    "Netflix",
    "Apple TV+",
    "Amazon",
    "Disney+",
    "Paramount+",
    "Max",
    "Hulu",
    "Peacock",
    "Showtime",
    "Starz",
    "AMC",
    "FX",
    "National Geographic",
    "BBC One",
    "Sky Atlantic",
    "Canal+",
    "ZDF",
    "Arte",
    "Viaplay",
    "TV4",
    "SVT",
    "NRK",
    "DR",
    "YLE"
]

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
    Only includes shows premiered this year up to today.
    """
    tv_ids = set()
    current_year = datetime.now().year
    today_str = datetime.now().strftime("%Y-%m-%d")
    start_date_str = f"{current_year}-01-01"

    # Lists containing currently airing shows
    endpoints = [
        "/tv/on_the_air",
        "/tv/airing_today",
    ]

    # Discover endpoints with strict date filter
    discover_endpoints = [
        f"/discover/tv?sort_by=popularity.desc&first_air_date.gte={start_date_str}&first_air_date.lte={today_str}",
        f"/discover/tv?sort_by=vote_average.desc&first_air_date.gte={start_date_str}&first_air_date.lte={today_str}&vote_count.gte=10",
        f"/discover/tv?sort_by=first_air_date.desc&first_air_date.gte={start_date_str}&first_air_date.lte={today_str}",
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
                        if endpoint in endpoints:
                            first_air = show.get("first_air_date", "")
                            if not first_air or first_air < start_date_str or first_air > today_str:
                                continue
                        tv_ids.add(show["id"])

                elif response.status_code == 401:
                    print("ERROR: Invalid API key. Please check your TMDB_API_KEY.")
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
    networks = [net["name"] for net in show.get("networks", [])]
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
        "popularity": show.get("popularity", 0),
        "status": show.get("status"),
        "type": show.get("type"),
        "poster_url": f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None,
        "overview": show.get("overview")
    }


def is_prestige_show(show):
    """Check if a show is from a prestige network/streamer."""
    networks = [net.get("name", "") for net in show.get("networks", [])]

    for network in networks:
        for prestige in PRESTIGE_NETWORKS:
            if prestige.lower() in network.lower():
                return True

    return False


def fetch_and_filter_shows(tv_ids):
    """
    Fetch details for each TV show.
    Only keep shows from prestige networks.
    Only includes shows premiered this year up to today.
    """
    filtered = []
    total = len(tv_ids)
    current_year = datetime.now().year
    today_str = datetime.now().strftime("%Y-%m-%d")
    start_date_str = f"{current_year}-01-01"

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
            first_air = show.get("first_air_date", "")

            # Strict date filter
            if not first_air or first_air < start_date_str or first_air > today_str:
                continue

            # Prestige filter
            if is_prestige_show(show):
                simplified = simplify_show(show)
                filtered.append(simplified)
                networks_str = ", ".join([n["name"] for n in show.get("networks", [])])
                print(f"  🎬 {show.get('name')} ({first_air}) - {networks_str}")

        except requests.exceptions.RequestException as e:
            print(f"  Request failed for TV show {tv_id}: {e}")
        except Exception as e:
            print(f"  Unexpected error for TV show {tv_id}: {e}")

    # Sort by first air date (newest first)
    filtered.sort(key=lambda x: x.get("first_air_date", ""), reverse=True)
    return filtered


def main():
    current_year = datetime.now().year
    today_str = datetime.now().strftime("%Y-%m-%d")

    print("=" * 60)
    print("PRESTIGE TV SHOWS GENERATOR")
    print("=" * 60)
    print()
    print(f"Date filter: {current_year}-01-01 to {today_str}")
    print(f"Network filter: {len(PRESTIGE_NETWORKS)} prestige networks/streamers")
    print()

    print("Fetching TV shows from TMDb...")
    tv_ids = get_tv_show_ids(pages=10)
    print(f"Found {len(tv_ids)} unique TV shows to evaluate.\n")

    print("Filtering by prestige networks...")
    shows = fetch_and_filter_shows(tv_ids)

    output = {
        "metadata": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "current_year": current_year,
            "date_range": f"{current_year}-01-01 to {today_str}",
            "source": "TMDb API",
            "note": "TV shows from prestige networks premiered this year to date.",
            "filter": {
                "prestige_networks": PRESTIGE_NETWORKS,
                "description": f"TV shows from {current_year} on major networks/streamers"
            },
            "count": len(shows)
        },
        "shows": shows
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print("DONE!")
    print(f"  Prestige TV shows found: {len(shows)}")
    print(f"  Output saved to: {OUTPUT_FILE}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
