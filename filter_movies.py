#!/usr/bin/env python3
"""
Fetch movies from TMDb and filter by budget only.

Filter:
  - Budget >= $100,000,000 (regardless of rating)
  - Released this year up to today

Output:
  - filtered_movies_radarr.json (Radarr-compatible pure array)

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

OUTPUT_FILE = "filtered_movies_radarr.json"
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
            except requests.exceptions.RequestException:
                time.sleep(1)

    return list(movie_ids)


def simplify_movie(movie):
    """Create a simplified movie object."""
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


def fetch_and_filter_movies(movie_ids):
    """Fetch details and keep only big budget movies from this year."""
    filtered = []
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
                simplified = simplify_movie(movie)
                filtered.append(simplified)
                print(f"  💰 {movie.get('title')} ({release_date}) - ${budget:,}")

        except Exception:
            pass

    filtered.sort(key=lambda x: x.get("release_date", ""), reverse=True)
    return filtered


def main():
    print("=" * 50)
    print("BIG BUDGET MOVIES FOR RADARR")
    print("=" * 50)
    print()

    movie_ids = get_movie_ids(pages=10)
    print(f"Found {len(movie_ids)} movies to evaluate.\n")

    movies = fetch_and_filter_movies(movie_ids)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(movies, f, indent=2, ensure_ascii=False)

    print(f"\nDone! {len(movies)} movies saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
