```markdown
# 🎬 Filtered Movies

Automatically updated lists of movies filtered by budget and ratings, powered by [The Movie Database (TMDb)](https://www.themoviedb.org/).

## 📋 Filters

The [filtered_movies.json](filtered_movies.json) file contains **two separate lists**:

### 💰 Big Budget (`big_budget`)
Movies with a budget of **$100,000,000 or more** – regardless of rating.

These are films where the production investment alone makes them worth watching, whether they turned out to be masterpieces or fascinating flops.

### ⭐ Highly Rated & Popular (`highly_rated`)
Movies with:
- Rating **≥ 7.5**
- At least **100,000 votes**

These are the films that audiences agree are genuinely good.

## 🚀 Usage

### Direct JSON Access

```

https://raw.githubusercontent.com/api-apoteket/filtered-movies/main/filtered_movies.json

```

### JSON Structure

```json
{
  "metadata": {
    "last_updated": "2026-05-08 12:00 UTC",
    "filters": {
      "big_budget": {
        "description": "Movies with budget ≥ $100,000,000 (regardless of rating)",
        "count": 156
      },
      "highly_rated": {
        "description": "Movies with rating ≥ 7.5 and ≥ 100,000 votes",
        "count": 89
      }
    }
  },
  "big_budget": [
    {
      "title": "Avatar: The Way of Water",
      "tmdb_id": 76600,
      "imdb_id": "tt1630029",
      "release_date": "2022-12-14",
      "genres": ["Science Fiction", "Adventure", "Action"],
      "budget": 460000000,
      "revenue": 2923706026,
      "rating": 7.6,
      "votes": 12345,
      "poster_url": "https://image.tmdb.org/t/p/w500/...",
      "overview": "Jake Sully lives with..."
    }
  ],
  "highly_rated": [...]
}
```

🔧 Run Locally

Prerequisites

· Python 3.8 or later
· A TMDb API Read Access Token

⚠️ IMPORTANT: Use your API Read Access Token, NOT your API Key!

On the TMDb API settings page, you'll see two values:

· API Key – a short string like a1b2c3d4e5... ← Do NOT use this
· API Read Access Token – a long string starting with eyJ... ← USE THIS ONE

The script uses Bearer token authentication which requires the Read Access Token.

Setup

```bash
# Clone the repository
git clone https://github.com/api-apoteket/filtered-movies.git
cd filtered-movies

# Install dependencies
pip install requests

# Set your API token as an environment variable
export TMDB_API_KEY="eyJhbGciOiJIUzI1NiJ9.your_read_access_token_here"

# Run the script
python3 filter_movies.py
```

The script will generate filtered_movies.json in the current directory.

🤖 Automated Updates

This repository uses GitHub Actions to automatically regenerate the movie lists daily at 06:00 UTC.

The workflow:

1. Fetches movies from multiple TMDb endpoints
2. Applies both filters
3. Updates filtered_movies.json
4. Commits and pushes changes

To enable this in your own fork, add your TMDb token as a repository secret:

Secret Name Value
TMDB_API_KEY Your TMDb API Read Access Token

📊 Data Source

All movie data comes from The Movie Database (TMDb). This product uses the TMDb API but is not endorsed or certified by TMDb.

⚠️ Important Notes

· Budget figures may be estimates – not all productions publicly disclose exact budgets
· Never commit your API token – use environment variables or GitHub Secrets
· Rate limits apply – the script respects TMDb's rate limiting (40 requests per 10 seconds)
· Data refreshes daily – allow up to 24 hours for new releases to appear

📄 License

MIT – See LICENSE for details.

🙏 Attribution

<img src="https://www.themoviedb.org/assets/2/v4/logos/v2/blue_short-8e7b30f73a4020692ccca9c88bafe5dcb6f8a62a4c6bc55cd9ba82bb2cd95f6c.svg" height="50" alt="TMDb logo">This project uses the TMDb API but is not endorsed or certified by TMDb.

```
