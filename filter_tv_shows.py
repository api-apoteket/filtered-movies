#!/usr/bin/env python3
"""
Fetch TV shows from TMDb and filter by prestige networks only.

Filter:
  - Shows from top 5 premium networks/streamers
  - Premiered this year onwards
  - Must have a TVDB ID (required by Sonarr Custom List)

Output:
  - filtered_tv_shows_sonarr.json    (Sonarr Custom List: TvdbId only)

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
    "HBO",
    "Max",
    "Apple TV+",
    "Apple TV",
    "National Geographic",
    "Amazon",
    "Prime Video",
    "Amazon Prime Video",
]

BASE_URL = "https://api.themoviedb.org/3"
HEADERS = {
    "accept": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}


# ===== FUNCTIONS =====

def get_tv_show_ids(pages=15):
    """Fetch TV show IDs from TMDb. Only this year onwards."""
    tv_ids = set()
    current_year = datetime.now().year
    start_date_str = f"{current_year}-01-01"

    endpoints = [
        "/tv/on_the_air",
        "/tv/airing_today",
    ]

    discover_endpoints = [
        f"/discover/tv?sort_by=popularity.desc&first_air_date.gte={start_date_str}",
        f"/discover/tv?sort_by=vote_average.desc&first_air_date.gte={start_date_str}&vote_count.gte=10",
        f"/discover/tv?sort_by=first_air_date.desc&first_air_date.gte={start_date_str}",
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
                            if not first_air or first_air < start_date_str:
                                continue
                        tv_ids.add(show["id"])

                elif response.status_code == 401:
                    print("ERROR: Invalid API key.")
                    sys.exit(1)
                elif response.status_code == 429:
                    time.sleep(2)

            except requests.exceptions.RequestException:
                time.sleep(1)

    return list(tv_ids)


def get_tvdb_id(tmdb_id):
    """Fetch TVDB ID from TMDb external IDs endpoint."""
    url = f"{BASE_URL}/tv/{tmdb_id}/external_ids"
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code == 429:
            time.sleep(5)
            response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            tvdb_id = response.json().get("tvdb_id")
            return tvdb_id if tvdb_id else None
    except Exception:
        pass
    return None


def is_prestige_show(show):
    """Check if a show is from a prestige network/streamer."""
    networks = [net.get("name", "") for net in show.get("networks", [])]
    for network in networks:
        for prestige in PRESTIGE_NETWORKS:
            if prestige.lower() in network.lower():
                return True
    return False


def fetch_and_filter_shows(tv_ids):
    """Fetch details for each TV show. Returns list of {TvdbId: ...}."""
    filtered = []
    total = len(tv_ids)
    current_year = datetime.now().year
    start_date_str = f"{current_year}-01-01"
    skipped_no_tvdb = 0

    for i, tv_id in enumerate(tv_ids):
        if i % 10 == 0:
            print(f"  Processing show {i+1}/{total}...")

        url = f"{BASE_URL}/tv/{tv_id}?append_to_response=external_ids"

        try:
            response = requests.get(url, headers=HEADERS, timeout=30)

            if response.status_code == 429:
                time.sleep(5)
                response = requests.get(url, headers=HEADERS, timeout=30)

            if response.status_code != 200:
                continue

            show = response.json()
            first_air = show.get("first_air_date", "")

            if not first_air or first_air < start_date_str:
                continue

            if not is_prestige_show(show):
                continue

            tvdb_id = show.get("external_ids", {}).get("tvdb_id")
            if not tvdb_id:
                skipped_no_tvdb += 1
                continue

            filtered.append({"TvdbId": tvdb_id})
            networks_str = ", ".join([n["name"] for n in show.get("networks", [])])
            print(f"  🎬 {show.get('name')} ({first_air}) - {networks_str} - TVDB: {tvdb_id}")

        except requests.exceptions.RequestException:
            pass
        except Exception:
            pass

    if skipped_no_tvdb > 0:
        print(f"\n  {skipped_no_tvdb} show(s) skipped: No TVDB ID")

    filtered.sort(key=lambda x: x.get("TvdbId", 0))
    return filtered


def main():
    current_year = datetime.now().year

    print("=" * 55)
    print("PREMIUM TV SHOWS FOR SONARR")
    print("=" * 55)
    print()
    print(f"Date filter:    {current_year}-01-01 onwards")
    print(f"Network filter: {len(PRESTIGE_NETWORKS)} premium networks")
    print(f"Networks:       {', '.join(PRESTIGE_NETWORKS)}")
    print()

    print("Fetching TV shows from TMDb...")
    tv_ids = get_tv_show_ids(pages=10)
    print(f"Found {len(tv_ids)} unique TV shows to evaluate.\n")

    print("Filtering by prestige networks...")
    shows = fetch_and_filter_shows(tv_ids)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(shows, f, indent=2, ensure_ascii=False)

    print(f"\nDone!")
    print(f"  Sonarr-ready: {OUTPUT_FILE}")
    print(f"  Shows found:  {len(shows)}")


if __name__ == "__main__":
    main()
