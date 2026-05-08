#!/usr/bin/env python3
"""
Fetch movies from TMDb and create two separate filtered lists.

Filter 1 - Big Budget:
  - Budget >= $100,000,000 (regardless of rating)
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

OUTPUT_FILE = "filtered_movies.json"

# Filter 1: Big budget (regardless of rating)
MIN_BUDGET = 100_000_000  # $100M

# Filter 2: Highly rated + popular
MIN_RATING = 7.5
MIN_VOTES = 100_000

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
    Only includes movies from the current year onwards.
    Returns a list of unique movie IDs.
    """
    movie_ids = set()
    current_year = datetime.now().year

    # Standard endpoints (filtered manually by year after fetching)
    endpoints = [
        "/movie/now_playing",
        "/movie/popular",
        "/movie/top_rated",
    ]

    # Discover endpoints with built-in date filter
    discover_endpoints = [
        f"/discover/movie?sort_by=revenue.desc&primary_release_date.gte={current_year}-01-01",
        f"/discover/movie?sort_by=vote_count.desc&primary_release_date.gte={current_year}-01-01",
        f"/discover/movie?sort_by=primary_release_date.desc&primary_release_date.gte={current_year}-01-01",
        f"/discover/movie?sort_by=popularity.desc&primary_release_date.gte={current_year}-01-01",
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
                        # For discover endpoints, TMDb already filtered by year
                        # For standard endpoints, check release date manually
                        if endpoint in endpoints:
                            release_date = movie.get("release_date", "")
                            if not release_date or release_date < f"{current_year}-01-01":
                                continue
                        movie_ids.add(movie["id"])

                elif response.status_code == 401:
                    print("ERROR: Invalid API key. Please check your TMDB_API_KEY.")
                    print("       Make sure you're using the Read Access Token (starts with eyJ...),")
                    print("       not the short API Key.")
                    sys.exit(1)
                elif response.status_code == 429:
                    print("WARNING: Rate limit reached. Waiting 2 seconds before retrying...")
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
        "poster_url": f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None,
        "overview": movie.get("overview")
    }


def fetch_and_filter_movies(movie_ids):
    """
    Fetch details for each movie and sort into respective lists.
    Only includes movies from the current year onwards.
    Returns two lists: big_budget and highly_rated.
    """
    big_budget = []
    highly_rated = []
    total = len(movie_ids)
    current_year = datetime.now().year

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

            # Skip movies released before current year
            release_date = movie.get("release_date", "")
            if not release_date or release_date < f"{current_year}-01-01":
                continue

            budget = movie.get("budget", 0)
            rating = movie.get("vote_average", 0)
            votes = movie.get("vote_count", 0)

            # Skip movies without budget data
            if budget == 0:
                continue

            simplified = simplify_movie(movie)

            # Filter 1: Big budget
            if budget >= MIN_BUDGET:
                big_budget.append(simplified)
                print(f"  💰 BIG BUDGET: {movie.get('title')} ({release_date}) - ${budget:,}")

            # Filter 2: Highly rated
            if rating >= MIN_RATING and votes >= MIN_VOTES:
                highly_rated.append(simplified)
                print(f"  ⭐ HIGH RATED: {movie.get('title')} ({release_date}) - {rating} ({votes:,} votes)")

        except requests.exceptions.RequestException as e:
            print(f"  Request failed for movie {movie_id}: {e}")
        except Exception as e:
            print(f"  Unexpected error for movie {movie_id}: {e}")

    # Sort by release date (newest first)
    big_budget.sort(key=lambda x: x.get("release_date", ""), reverse=True)
    highly_rated.sort(key=lambda x: x.get("release_date", ""), reverse=True)

    return big_budget, highly_rated


def main():
    current_year = datetime.now().year

    print("=" * 60)
    print("FILTERED MOVIES GENERATOR")
    print("=" * 60)
    print()
    print(f"Year filter: {current_year} onwards only")
    print()
    print("Filter 1 - Big Budget:")
    print(f"  Budget >= ${MIN_BUDGET:,} (regardless of rating)")
    print()
    print("Filter 2 - Highly Rated & Popular:")
    print(f"  Rating >= {MIN_RATING}")
    print(f"  Votes >= {MIN_VOTES:,}")
    print()

    print("Fetching movies from TMDb...")
    movie_ids = get_movie_ids(pages=10)
    print(f"Found {len(movie_ids)} unique movies to evaluate.\n")

    print("Analyzing and filtering...")
    big_budget, highly_rated = fetch_and_filter_movies(movie_ids)

    output = {
        "metadata": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "current_year": current_year,
            "source": "TMDb API",
            "note": "Only includes movies from current year onwards.",
            "filters": {
                "big_budget": {
                    "description": f"Movies from {current_year} with budget >= ${MIN_BUDGET:,} (regardless of rating)",
                    "min_budget": MIN_BUDGET,
                    "year_from": current_year,
                    "count": len(big_budget)
                },
                "highly_rated": {
                    "description": f"Movies from {current_year} with rating >= {MIN_RATING} and >= {MIN_VOTES:,} votes",
                    "min_rating": MIN_RATING,
                    "min_votes": MIN_VOTES,
                    "year_from": current_year,
                    "count": len(highly_rated)
                }
            }
        },
        "big_budget": big_budget,
        "highly_rated": highly_rated
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print("DONE!")
    print(f"  Big budget movies:   {len(big_budget)}")
    print(f"  Highly rated movies:  {len(highly_rated)}")
    print(f"  Output saved to:      {OUTPUT_FILE}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
