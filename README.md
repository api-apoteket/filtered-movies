```markdown
# 🎬 Filtered Movies & TV Shows

Automatically updated lists of high-value movies and TV shows, powered by [The Movie Database (TMDb)](https://www.themoviedb.org/).

## 📋 What This Provides

Two separate JSON files, each updated daily via GitHub Actions:

| File | Content | Filter |
|------|---------|--------|
| [`filtered_movies.json`](filtered_movies.json) | Movies | Budget ≥ $100,000,000 |
| [`filtered_tv_shows.json`](filtered_tv_shows.json) | TV Shows | Prestige networks/streamers |

### 💰 Movies – Big Budget Only

Every movie with a production budget of **$100,000,000 or more**, released this year up to today.

No rating requirements. A flop with a $200M budget qualifies just as much as an Oscar winner. The philosophy: if someone invested that much money, it's worth knowing about.

### 🎬 TV Shows – Prestige Networks

Every TV show that premiered this year on a major network or streaming service.

Prestige networks include: HBO, Netflix, Apple TV+, Amazon Prime Video, Disney+, Paramount+, Max, Hulu, Peacock, Showtime, Starz, AMC, FX, BBC One, Sky Atlantic, and more.

No rating requirements. If it's on a serious platform, it's on the list.

## 🚀 Usage

### Direct JSON Access

**Movies (for Radarr):**
```

https://raw.githubusercontent.com/api-apoteket/filtered-movies/main/filtered_movies.json

```

**TV Shows (for Sonarr):**
```

https://raw.githubusercontent.com/api-apoteket/filtered-movies/main/filtered_tv_shows.json

```

### JSON Structure

**Movies:**
```json
{
  "metadata": {
    "last_updated": "2026-05-08 19:05 UTC",
    "date_range": "2026-01-01 to 2026-05-08",
    "filter": {
      "min_budget": 100000000,
      "description": "Movies from 2026 with budget >= $100,000,000"
    },
    "count": 17
  },
  "movies": [
    {
      "title": "Project Hail Mary",
      "tmdb_id": 687163,
      "imdb_id": "tt12042730",
      "release_date": "2026-03-15",
      "genres": ["Science Fiction", "Adventure"],
      "budget": 200000000,
      "revenue": 640469765,
      "rating": 8.203,
      "votes": 1960,
      "poster_url": "https://image.tmdb.org/t/p/w500/...",
      "overview": "Science teacher Ryland Grace wakes up..."
    }
  ]
}
```

TV Shows:

```json
{
  "metadata": {
    "last_updated": "2026-05-08 19:05 UTC",
    "date_range": "2026-01-01 to 2026-05-08",
    "filter": {
      "prestige_networks": ["HBO", "Netflix", "Apple TV+", "..."],
      "description": "TV shows from 2026 on major networks/streamers"
    },
    "count": 12
  },
  "shows": [
    {
      "title": "The Last of Us",
      "tmdb_id": 100088,
      "first_air_date": "2026-01-15",
      "networks": ["HBO"],
      "rating": 8.8,
      "votes": 8500,
      "poster_url": "https://image.tmdb.org/t/p/w500/...",
      "overview": "Joel and Ellie..."
    }
  ]
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

The scripts use Bearer token authentication which requires the Read Access Token.

Setup

```bash
# Clone the repository
git clone https://github.com/api-apoteket/filtered-movies.git
cd filtered-movies

# Install dependencies
pip install requests

# Set your API token
export TMDB_API_KEY="eyJhbGciOiJIUzI1NiJ9.your_read_access_token_here"

# Generate movie list
python3 filter_movies.py

# Generate TV show list
python3 filter_tv_shows.py
```

🤖 Automated Updates

This repository uses GitHub Actions to automatically regenerate both lists daily:

Workflow Runs at Updates
update-movies.yml 06:00 UTC daily filtered_movies.json
update-tv-shows.yml 07:00 UTC daily filtered_tv_shows.json

To enable this in your own fork, add your TMDb token as a repository secret:

Secret Name Value
TMDB_API_KEY Your TMDb API Read Access Token

🎯 Radarr & Sonarr Setup

Radarr (Movies)

1. Go to Settings → Import Lists → +
2. Choose Custom Lists → Radarr Lists
3. Set URL to: https://raw.githubusercontent.com/api-apoteket/filtered-movies/main/filtered_movies.json
4. Set JSON Path to: $.movies
5. Configure auto-add settings as desired

Sonarr (TV Shows)

1. Go to Settings → Import Lists → +
2. Choose Custom Lists → Sonarr Lists
3. Set URL to: https://raw.githubusercontent.com/api-apoteket/filtered-movies/main/filtered_tv_shows.json
4. Set JSON Path to: $.shows
5. Configure auto-add settings as desired

📊 Data Source

All movie and TV show data comes from The Movie Database (TMDb). This product uses the TMDb API but is not endorsed or certified by TMDb.

📄 License

MIT – See [MIT License](LICENSE) for details.

🙏 Attribution

<img src="https://www.themoviedb.org/assets/2/v4/logos/v2/blue_short-8e7b30f73a4020692ccca9c88bafe5dcb6f8a62a4c6bc55cd9ba82bb2cd95f6c.svg" height="50" alt="TMDb logo">This project uses the TMDb API but is not endorsed or certified by TMDb.
