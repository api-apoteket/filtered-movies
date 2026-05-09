#!/usr/bin/env python3
"""
Fetch TV shows from TMDb and filter by network/prestige only.

Filter:
  - Shows from major networks/streamers
  - Premiered this year up to today

Output:
  - filtered_tv_shows_sonarr.json (Sonarr-compatible pure array)

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
    sys.exit(1)

OUTPUT_FILE = "filtered_tv_shows_sonarr.json"

PRESTIGE_NETWORKS = [
    "HBO", "Netflix", "Apple TV+", "Amazon", "Disney+",
    "Paramount+", "Max", "Hulu", "Peacock", "Showtime",
    "Starz", "AMC", "FX", "National Geographic",
    "BBC One", "Sky Atlantic", "Canal+", "ZDF", "Arte",
    "Viaplay", "TV4", "SVT", "NRK", "DR", "YLE"
]

BASE_URL = "https://api.themoviedb.org/3"
HEADERS = {
    "accept": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}


# ===== FUNCTIONS =====

def get_tv_show_ids(pages=15):
    """Fetch TV show IDs from TMDb. Only this year up to today."""
    tv_ids = set()
    current_year = datetime.now().year
    today_str = datetime.now().strftime("%Y-%m-%d")
    start_date_str = f"{current_year}-01-01"

    endpoints = ["/tv/on_the_air", "/tv/airing_today"]
    discover_endpoints = [
        f"/discover/tv?sort_by=popularity.desc&first_air_date.gte={start_date_str}&first_air_date.lte={today_str}",
        f"/discover/tv?sort_by=vote_average.desc&first_air_date.gte={start_date_str}&first_air_date.lte={today_str}&vote_count.gte=10",
        f"/discover/tv?sort_by=first_air_date.desc&first_air_date.gte={start_date_str}&first_air_date.lte={today_str}",
    ]

    for endpoint in endpoints + discover_endpoints:
        for page in range(1, pages + 1):
            url = f"{BASE_URL}{endpoint}{'&' if '?' in endpoint else '?'}page={page}"
            try:
                response = requests.get(url, headers=HEADERS, timeout=30)
                if response.status_code == 200:
                    for show in response.json().get("results", []):
                        if endpoint in endpoints:
                            fa = show.get("first_air_date", "")
                            if not fa or fa < start_date_str or fa > today_str:
                                continue
                        tv_ids.add(show["id"])
                elif response.status_code == 429:
                    time.sleep(2)
            except requests.exceptions.RequestException:
                time.sleep(1)

    return list(tv_ids)


def simplify_show(show):
    """Create a simplified TV show object."""
    poster = show.get("poster_path")
    return {
        "title": show.get("name"),
        "original_title": show.get("original_name"),
        "tmdb_id": show.get("id"),
        "first_air_date": show.get("first_air_date"),
        "last_air_date": show.get("last_air_date"),
        "genres": [g["name"] for g in show.get("genres", [])],
        "networks": [n["name"] for n in show.get("networks", [])],
        "creators": [c["name"] for c in show.get("created_by", [])],
        "number_of_seasons": show.get("number_of_seasons", 0),
        "number_of_episodes": show.get("number_of_episodes", 0),
        "rating": show.get("vote_average", 0),
        "votes": show.get("vote_count", 0),
        "popularity": show.get("popularity", 0),
        "status": show.get("status"),
        "type": show.get("type"),
        "poster_url": f"https://image.tmdb.org/t/p/w500{poster}" if poster else None,
        "overview": show.get("overview")
    }


def is_prestige_show(show):
    """Check if a show is from a prestige network."""
    for network in show.get("networks", []):
        for prestige in PRESTIGE_NETWORKS:
            if prestige.lower() in network.get("name", "").lower():
                return True
    return False


def fetch_and_filter_shows(tv_ids):
    """Fetch details and keep only prestige network shows from this year."""
    filtered = []
    current_year = datetime.now().year
    today_str = datetime.now().strftime("%Y-%m-%d")
    start_date_str = f"{current_year}-01-01"

    for i, tv_id in enumerate(tv_ids):
        if i % 100 == 0:
            print(f"  Processing show {i+1}/{len(tv_ids)}...")

        try:
            response = requests.get(f"{BASE_URL}/tv/{tv_id}", headers=HEADERS, timeout=30)
            if response.status_code == 429:
                time.sleep(2)
                response = requests.get(f"{BASE_URL}/tv/{tv_id}", headers=HEADERS, timeout=30)
            if response.status_code != 200:
                continue

            show = response.json()
            first_air = show.get("first_air_date", "")
            if not first_air or first_air < start_date_str or first_air > today_str:
                continue

            if is_prestige_show(show):
                simplified = simplify_show(show)
                filtered.append(simplified)
                networks_str = ", ".join([n["name"] for n in show.get("networks", [])])
                print(f"  🎬 {show.get('name')} ({first_air}) - {networks_str}")

        except Exception:
            pass

    filtered.sort(key=lambda x: x.get("first_air_date", ""), reverse=True)
    return filtered


def main():
    print("=" * 50)
    print("PRESTIGE TV SHOWS FOR SONARR")
    print("=" * 50)
    print()

    tv_ids = get_tv_show_ids(pages=10)
    print(f"Found {len(tv_ids)} TV shows to evaluate.\n")

    shows = fetch_and_filter_shows(tv_ids)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(shows, f, indent=2, ensure_ascii=False)

    print(f"\nDone! {len(shows)} shows saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
