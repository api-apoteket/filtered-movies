#!/usr/bin/env python3
"""
Fetch movies from TMDb and create two separate filtered lists:

Filter 1 - Big Budget:
  - Budget >= $100,000,000 (regardless of rating)

Filter 2 - Highly Rated & Popular:
  - Rating >= 7.5
  - Vote count >= 100,000

Both lists are combined in one JSON file.

Required environment variable:
  TMDB_API_KEY - Your TMDb API key (v3 auth or bearer token)
"""

import requests
import json
import os
import sys
from datetime import datetime, timezone


# ===== CONFIGURATION =====

# API key from environment variable (NEVER hardcode secrets)
API_KEY = os.environ.get("TMDB_API_KEY")
if not API_KEY:
    print("ERROR: Environment variable TMDB_API_KEY is not set.")
    print("       Set it with: export TMDB_API_KEY='your_key_here'")
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
    Fetch movie IDs from multiple TMDb lists for broad coverage.
    Returns a list of unique movie IDs.
    """
    movie_ids = set()

    endpoints = [
        "/movie/popular",
        "/movie/now_playing",
        "/movie/top_rated",
        "/discover/movie?sort_by=revenue.desc",
        "/discover/movie?sort_by=vote_count.desc",
        "/discover/movie?sort_by=primary_release_date.desc",
    ]

    for endpoint in endpoints:
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
                        movie_ids.add(movie["id"])
                elif response.status_code == 401:
                    print("ERROR: Invalid API key. Please check your TMDB_API_KEY.")
                    sys.exit(1)
                elif response.status_code == 429:
                    print("WARNING: Rate limit reached. Waiting before retrying...")
                    import time
                    time.sleep(2)
                else:
                    print(f"WARNING: Could not fetch {url} (HTTP {response.status_code})")

            except requests.exceptions.RequestException as e:
                print(f"WARNING: Request failed for {url}: {e}")

    return list(movie_ids)


def simplify_movie(movie):
    """
    Create a simplified movie object with relevant fields.
    """
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
    Returns two lists: big_budget and highly_rated.
    """
    big_budget = []
    highly_rated = []
    total = len(movie_ids)

    for i, movie_id in enumerate(movie_ids):
        # Progress indicator every 100 movies
        if i % 100 == 0:
            print(f"  Processing movie {i+1}/{total}...")

        url = f"{BASE_URL}/movie/{movie_id}"

        try:
            response = requests.get(url, headers=HEADERS, timeout=30)

            if response.status_code == 429:
                print("  Rate limited. Waiting...")
                import time
                time.sleep(2)
                response = requests.get(url, headers=HEADERS, timeout=30)

            if response.status_code != 200:
                continue

            movie = response.json()
            budget = movie.get("budget", 0)
            rating = movie.get("vote_average", 0)
            votes = movie.get("vote_count", 0)

            # Skip movies without budget data
            if budget == 0:
                continue

            simplified = simplify_movie(movie)

            # Filter 1: Big budget (regardless of rating/votes)
            if budget >= MIN_BUDGET:
                big_budget.append(simplified)
                print(f"  💰 BIG BUDGET: {movie.get('title')} - ${budget:,}")

            # Filter 2: High rating + many votes
            if rating >= MIN_RATING and votes >= MIN_VOTES:
                highly_rated.append(simplified)
                print(f"  ⭐ HIGH RATED: {movie.get('title')} - {rating} ({votes:,} votes)")

        except requests.exceptions.RequestException as e:
            print(f"  Request failed for movie {movie_id}: {e}")
        except Exception as e:
            print(f"  Unexpected error for movie {movie_id}: {e}")

    # Sort by release date (newest first)
    big_budget.sort(key=lambda x: x.get("release_date", ""), reverse=True)
    highly_rated.sort(key=lambda x: x.get("release_date", ""), reverse=True)

    return big_budget, highly_rated


def main():
    print("=" * 60)
    print("🎬 FILTERED MOVIES GENERATOR")
    print("=" * 60)
    print()
    print("Filter 1 - Big Budget:")
    print(f"  Budget ≥ ${MIN_BUDGET:,} (regardless of rating/votes)")
    print()
    print("Filter 2 - Highly Rated & Popular:")
    print(f"  Rating ≥ {MIN_RATING}")
    print(f"  Votes ≥ {MIN_VOTES:,}")
    print()

    print("Fetching movies from TMDb...")
    movie_ids = get_movie_ids(pages=10)
    print(f"Found {len(movie_ids)} unique movies to evaluate.\n")

    print("Analyzing and filtering...")
    big_budget, highly_rated = fetch_and_filter_movies(movie_ids)

    # Build output structure
    output = {
        "metadata": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "source": "TMDb API",
            "filters": {
                "big_budget": {
                    "description": f"Movies with budget ≥ ${MIN_BUDGET:,} (regardless of rating)",
                    "min_budget": MIN_BUDGET,
                    "count": len(big_budget)
                },
                "highly_rated": {
                    "description": f"Movies with rating ≥ {MIN_RATING} and ≥ {MIN_VOTES:,} votes",
                    "min_rating": MIN_RATING,
                    "min_votes": MIN_VOTES,
                    "count": len(highly_rated)
                }
            }
        },
        "big_budget": big_budget,
        "highly_rated": highly_rated
    }

    # Write to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print("DONE!")
    print(f"  💰 Big budget movies:   {len(big_budget)}")
    print(f"  ⭐ Highly rated movies:  {len(highly_rated)}")
    print(f"  📁 Output saved to:      {OUTPUT_FILE}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
