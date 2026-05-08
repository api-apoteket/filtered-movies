#!/usr/bin/env python3
"""
Fetch movies from TMDb and create two separate filtered lists:

Filter 1 - Big Budget:
  - Budget >= $100,000,000 (oavsett betyg)

Filter 2 - Highly Rated & Popular:
  - Rating >= 7.5
  - Vote count >= 100,000

Both lists are combined in one JSON file.
"""

import requests
import json
import os
from datetime import datetime

# ===== CONFIGURATION =====
API_KEY = os.environ.get("TMDB_API_KEY", "f5d28f2fe1608ca116551f0aa167bfdd")
OUTPUT_FILE = "filtered_movies.json"

# Filter 1: Big budget (oavsett rating)
MIN_BUDGET = 100_000_000  # $100M

# Filter 2: Highly rated + popular
MIN_RATING = 7.5
MIN_VOTES = 100_000

# ===== TMDb API ENDPOINTS =====
BASE_URL = "https://api.themoviedb.org/3"
HEADERS = {
    "accept": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}


def get_movie_ids(pages=15):
    """
    Hämtar filmer från flera TMDb-listor för bred täckning.
    Returnerar en lista med unika film-ID:n.
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

            response = requests.get(url, headers=HEADERS)

            if response.status_code == 200:
                data = response.json()
                for movie in data.get("results", []):
                    movie_ids.add(movie["id"])
            else:
                print(f"Varning: Kunde inte hämta {url} (status {response.status_code})")

    return list(movie_ids)


def simplify_movie(movie):
    """Skapar ett förenklat filmobjekt med relevant data."""
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
    Hämtar detaljer för varje film och sorterar in i respektive lista.
    """
    big_budget = []
    highly_rated = []

    for i, movie_id in enumerate(movie_ids):
        if i % 100 == 0:
            print(f"  Bearbetar film {i+1}/{len(movie_ids)}...")

        url = f"{BASE_URL}/movie/{movie_id}"

        try:
            response = requests.get(url, headers=HEADERS)
            if response.status_code != 200:
                continue

            movie = response.json()
            budget = movie.get("budget", 0)
            rating = movie.get("vote_average", 0)
            votes = movie.get("vote_count", 0)

            # Hoppa över filmer utan budgetdata
            if budget == 0:
                continue

            simplified = simplify_movie(movie)

            # Filter 1: Big budget (oavsett rating/röster)
            if budget >= MIN_BUDGET:
                big_budget.append(simplified)
                print(f"  💰 BIG BUDGET: {movie.get('title')} - ${budget:,}")

            # Filter 2: Högt betyg + många röster
            if rating >= MIN_RATING and votes >= MIN_VOTES:
                highly_rated.append(simplified)
                print(f"  ⭐ HIGH RATED: {movie.get('title')} - {rating} ({votes:,} votes)")

        except Exception as e:
            print(f"  Fel vid film {movie_id}: {e}")

    # Sortera efter releasedatum (nyast först)
    big_budget.sort(key=lambda x: x.get("release_date", ""), reverse=True)
    highly_rated.sort(key=lambda x: x.get("release_date", ""), reverse=True)

    return big_budget, highly_rated


def main():
    print("=" * 60)
    print("🎬 FILTERED MOVIES GENERATOR")
    print("=" * 60)
    print()
    print("📋 Filter 1 - Big Budget:")
    print(f"   Budget ≥ ${MIN_BUDGET:,} (oavsett betyg/röster)")
    print()
    print("📋 Filter 2 - Highly Rated & Popular:")
    print(f"   Rating ≥ {MIN_RATING}")
    print(f"   Votes ≥ {MIN_VOTES:,}")
    print()

    print("🔍 Hämtar filmer från TMDb...")
    movie_ids = get_movie_ids(pages=10)
    print(f"📊 Hittade {len(movie_ids)} unika filmer att utvärdera.\n")

    print("🔎 Analyserar och filtrerar...")
    big_budget, highly_rated = fetch_and_filter_movies(movie_ids)

    # Bygg utdata
    output = {
        "metadata": {
            "generated": datetime.utcnow().isoformat() + "Z",
            "last_updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            "source": "TMDb API",
            "note": "Data from The Movie Database. Budget figures may be estimates.",
            "filters": {
                "big_budget": {
                    "description": "Movies with budget ≥ $100M (regardless of rating)",
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

    # Spara till fil
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"✅ KLART!")
    print(f"   💰 Big budget-filmer:  {len(big_budget)} st")
    print(f"   ⭐ Högt rankade filmer: {len(highly_rated)} st")
    print(f"   📁 Sparade i: {OUTPUT_FILE}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
