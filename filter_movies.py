#!/usr/bin/env python3
"""
Fetch movies from TMDb and filter by budget only.

Filter:
  - Budget >= $100,000,000 (regardless of rating)
  - Released this year up to today
  - Must have an IMDb ID (required by Radarr's StevenLu Custom list)

Outputs:
  - filtered_movies_radarr.json    (Radarr StevenLu Custom compatible)
  - filtered_movies_full.json      (Full metadata for reference)

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

OUTPUT_FILE_RADARR = "filtered_movies_radarr.json"
OUTPUT_FILE_FULL = "filtered_movies_full.json"
MIN_BUDGET = 100_000_000  # $100M

BASE_URL = "https://api.themoviedb.org/3"
HEADERS = {
    "accept": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}


# ===== FUNCTIONS =====

def get_movie_ids(pages=15):
    """Fetch movie IDs from TMDb. Only this year up to today."""
    movie_ids = set()
    current_year = datetime.now().year
    today_str = datetime.now().strftime("%Y-%m-%d")
    start_date_str = f"{current_year}-01-01"

    endpoints = ["/movie/now_playing"]
    discover_endpoints = [
        f"/discover/movie?sort_by=popularity.desc&primary_release_date.gte={start_date_str}&primary_release_date.lte={today_str}",
        f"/discover/movie?sort_by=vote_count.desc&primary_release_date.gte={start_date_str}&primary_release_date.lte={today_str}",
        f"/discover/movie?sort_by=revenue.desc&primary_release_date.gte={start_date_str}&primary_release_date.lte={today_str}",
    ]

    for endpoint in endpoints + discover_endpoints:
        for page in range(1, pages + 1):
            url = f"{BASE_URL}{endpoint}{'&' if '?' in endpoint else '?'}page={page}"
            try:
                response = requests.get(url, headers=HEADERS, timeout=30)
                if response.status_code == 200:
                    for movie in response.json().get("results", []):
                        if endpoint in endpoints:
                            rd = movie.get("release_date", "")
                            if not rd or rd < start_date_str or rd > today_str:
                                continue
                        movie_ids.add(movie["id"])
                elif response.status_code == 429:
                    time.sleep(2)
            except Exception:
                time.sleep(1)

    return list(movie_ids)


def simplify_movie_full(movie):
    """Create a full movie object (for reference)."""
    poster = movie.get("poster_path")
    return {
        "title": movie.get("title"),
        "tmdb_id": movie.get("id"),
        "imdb_id": movie.get("imdb_id"),
        "release_date": movie.get("release_date"),
        "genres": [g["name"] for g in movie.get("genres", [])],
        "budget": movie.get("budget", 0),
        "revenue": movie.get("revenue", 0),
        "rating": movie.get("vote_average", 0),
        "votes": movie.get("vote_count", 0),
        "popularity": movie.get("popularity", 0),
        "poster_url": f"https://image.tmdb.org/t/p/w500{poster}" if poster else None,
        "overview": movie.get("overview")
    }


def simplify_movie_radarr(movie):
    """
    Create a minimal movie object for Radarr's StevenLu Custom list.
    Must have title and imdb_id. Returns None if no IMDb ID.
    """
    imdb_id = movie.get("imdb_id")
    if not imdb_id:
        return None
    return {
        "title": movie.get("title"),
        "imdb_id": imdb_id
    }


def fetch_and_filter_movies(movie_ids):
    """Fetch details and keep only big budget movies from this year with IMDb ID."""
    filtered_full = []
    filtered_radarr = []
    skipped_no_imdb = 0
    current_year = datetime.now().year
    today_str = datetime.now().strftime("%Y-%m-%d")
    start_date_str = f"{current_year}-01-01"

    for i, movie_id in enumerate(movie_ids):
        if i % 100 == 0:
            print(f"  Processing movie {i+1}/{len(movie_ids)}...")

        try:
            response = requests.get(f"{BASE_URL}/movie/{movie_id}", headers=HEADERS, timeout=30)
            if response.status_code == 429:
                time.sleep(2)
                response = requests.get(f"{BASE_URL}/movie/{movie_id}", headers=HEADERS, timeout=30)
            if response.status_code != 200:
                continue

            movie = response.json()
            release_date = movie.get("release_date", "")
            if not release_date or release_date < start_date_str or release_date > today_str:
                continue

            budget = movie.get("budget", 0)
            if budget == 0:
                continue

            if budget >= MIN_BUDGET:
                # Full version always saved
                filtered_full.append(simplify_movie_full(movie))

                # Radarr version only if IMDb ID exists
                radarr_obj = simplify_movie_radarr(movie)
                if radarr_obj:
                    filtered_radarr.append(radarr_obj)
                    print(f"  💰 {movie.get('title')} ({release_date}) - ${budget:,}")
                else:
                    skipped_no_imdb += 1
                    print(f"  ⚠️  {movie.get('title')} ({release_date}) - ${budget:,} [SKIPPED: No IMDb ID]")

        except Exception:
            pass

    if skipped_no_imdb > 0:
        print(f"\n  ℹ️  {skipped_no_imdb} movie(s) skipped due to missing IMDb ID")

    filtered_full.sort(key=lambda x: x.get("release_date", ""), reverse=True)
    filtered_radarr.sort(key=lambda x: x.get("title", ""))

    return filtered_full, filtered_radarr


def main():
    print("=" * 50)
    print("BIG BUDGET MOVIES FOR RADARR")
    print("=" * 50)
    print()

    movie_ids = get_movie_ids(pages=10)
    print(f"Found {len(movie_ids)} movies to evaluate.\n")

    movies_full, movies_radarr = fetch_and_filter_movies(movie_ids)

    with open(OUTPUT_FILE_RADARR, "w", encoding="utf-8") as f:
        json.dump(movies_radarr, f, indent=2, ensure_ascii=False)

    with open(OUTPUT_FILE_FULL, "w", encoding="utf-8") as f:
        json.dump(movies_full, f, indent=2, ensure_ascii=False)

    print(f"\nDone!")
    print(f"  Radarr-ready: {OUTPUT_FILE_RADARR} ({len(movies_radarr)} movies)")
    print(f"  Full metadata: {OUTPUT_FILE_FULL} ({len(movies_full)} movies)")


if __name__ == "__main__":
    main()
