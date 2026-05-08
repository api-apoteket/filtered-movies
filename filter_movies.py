#!/usr/bin/env python3
"""
Fetch movies from TMDb and filter by budget only.

Filter - Big Budget:
  - Budget >= $100,000,000 (regardless of rating)
  - Released this year up to today

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

OUTPUT_FILE = "filtered_movies.json"

# Filter: Big budget (regardless of rating)
MIN_BUDGET = 100_000_000  # $100M

# ===== TMDb API SETUP =====

BASE_URL = "https://api.themoviedb.org/3"
HEADERS = {
    "accept": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}


# ===== FUNCTIONS =====

def get_movie_ids(pages=15):
    """
    Fetch movie IDs from multiple TMDb lists.
    Only includes movies released this year up to today.
    """
    movie_ids = set()
    current_year = datetime.now().year
    today_str = datetime.now().strftime("%Y-%m-%d")
    start_date_str = f"{current_year}-01-01"

    # Lists containing already released movies
    endpoints = [
        "/movie/now_playing",
    ]

    # Discover endpoints with strict date filter: must be between Jan 1 and today
    discover_endpoints = [
        f"/discover/movie?sort_by=popularity.desc&primary_release_date.gte={start_date_str}&primary_release_date.lte={today_str}",
        f"/discover/movie?sort_by=vote_count.desc&primary_release_date.gte={start_date_str}&primary_release_date.lte={today_str}",
        f"/discover/movie?sort_by=revenue.desc&primary_release_date.gte={start_date_str}&primary_release_date.lte={today_str}",
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
                    for movie in data.get("results", []):
                        if endpoint in endpoints:
                            release_date = movie.get("release_date", "")
                            if not release_date or release_date < start_date_str or release_date > today_str:
                                continue
                        movie_ids.add(movie["id"])

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

    return list(movie_ids)


def simplify_movie(movie):
    """Create a simplified movie object with relevant fields."""
    poster_path = movie.get("poster_path")
    return {
        "title": movie.get("title"),
        "tmdb_id": movie.get("id"),
        "imdb_id": movie.get("imdb_id"),
        "release_date": movie.get("release_date"),
        "genres": [genre["name"] for genre in movie.get("genres", [])],
        "budget": movie.get("budget", 0),
        "revenue": movie.get("revenue", 0),
        "rating": movie.get("vote_average", 0),
        "votes": movie.get("vote_count", 0),
        "popularity": movie.get("popularity", 0),
        "poster_url": f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None,
        "overview": movie.get("overview")
    }


def fetch_and_filter_movies(movie_ids):
    """
    Fetch details for each movie.
    Only keep movies with budget >= $100M.
    Only includes movies released this year up to today.
    """
    filtered = []
    total = len(movie_ids)
    current_year = datetime.now().year
    today_str = datetime.now().strftime("%Y-%m-%d")
    start_date_str = f"{current_year}-01-01"

    for i, movie_id in enumerate(movie_ids):
        if i % 100 == 0:
            print(f"  Processing movie {i+1}/{total}...")

        url = f"{BASE_URL}/movie/{movie_id}"

        try:
            response = requests.get(url, headers=HEADERS, timeout=30)

            if response.status_code == 429:
                print("  Rate limited. Waiting 2 seconds...")
                time.sleep(2)
                response = requests.get(url, headers=HEADERS, timeout=30)

            if response.status_code != 200:
                continue

            movie = response.json()
            release_date = movie.get("release_date", "")

            # Strict date filter: must be between Jan 1 and today
            if not release_date or release_date < start_date_str or release_date > today_str:
                continue

            budget = movie.get("budget", 0)

            # Skip movies without budget data
            if budget == 0:
                continue

            # Only keep big budget movies
            if budget >= MIN_BUDGET:
                simplified = simplify_movie(movie)
                filtered.append(simplified)
                print(f"  💰 {movie.get('title')} ({release_date}) - ${budget:,}")

        except requests.exceptions.RequestException as e:
            print(f"  Request failed for movie {movie_id}: {e}")
        except Exception as e:
            print(f"  Unexpected error for movie {movie_id}: {e}")

    # Sort by release date (newest first)
    filtered.sort(key=lambda x: x.get("release_date", ""), reverse=True)
    return filtered


def main():
    current_year = datetime.now().year
    today_str = datetime.now().strftime("%Y-%m-%d")

    print("=" * 60)
    print("BIG BUDGET MOVIES GENERATOR")
    print("=" * 60)
    print()
    print(f"Date filter: {current_year}-01-01 to {today_str}")
    print(f"Budget filter: >= ${MIN_BUDGET:,}")
    print()

    print("Fetching movies from TMDb...")
    movie_ids = get_movie_ids(pages=10)
    print(f"Found {len(movie_ids)} unique movies to evaluate.\n")

    print("Filtering by budget...")
    movies = fetch_and_filter_movies(movie_ids)

    output = {
        "metadata": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "current_year": current_year,
            "date_range": f"{current_year}-01-01 to {today_str}",
            "source": "TMDb API",
            "note": "Movies with budget >= $100M released this year to date.",
            "filter": {
                "min_budget": MIN_BUDGET,
                "description": f"Movies from {current_year} with budget >= ${MIN_BUDGET:,}"
            },
            "count": len(movies)
        },
        "movies": movies
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print("DONE!")
    print(f"  Big budget movies found: {len(movies)}")
    print(f"  Output saved to: {OUTPUT_FILE}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
