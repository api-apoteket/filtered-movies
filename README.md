# 🎬 Filtered Movies & TV Shows

Automatically updated lists of high-value movies and TV shows for Radarr and Sonarr, powered by [The Movie Database (TMDb)](https://www.themoviedb.org/).

## 📋 What This Provides

Two JSON files, updated daily via GitHub Actions, ready for direct import:

| File | For | Filter |
|------|-----|--------|
| `filtered_movies_radarr.json` | Radarr | Movies with budget ≥ $100,000,000 |
| `filtered_tv_shows_sonarr.json` | Sonarr | TV shows from top-tier networks/streamers |

### 💰 Movies – Big Budget Only

Every movie with a production budget of **$100,000,000 or more**, released this year up to today.

No rating requirements. A flop with a $200M budget qualifies just as much as an Oscar winner. The philosophy: if someone invested that much money, it's worth knowing about.

### 🎬 TV Shows – Prestige Networks

Every TV show that premiered this year on a major network or streaming service.

**Current networks:**
| Network | Type |
|---------|------|
| Netflix | Streaming |
| Amazon | Streaming (Prime Video) |
| Disney+ | Streaming |
| Paramount+ | Streaming (CBS, Showtime, Nickelodeon, MTV) |
| HBO / Max | Premium TV & Streaming |
| Hulu | Streaming (FX, originals) |
| Apple TV+ | Premium Streaming |
| National Geographic | Documentary & Factual |

No rating requirements. If it's on a top-tier platform, it's on the list.

## 🚀 Direct URLs for Radarr & Sonarr

**Radarr (StevenLu Custom):**
```

https://raw.githubusercontent.com/api-apoteket/filtered-movies/main/filtered_movies_radarr.json

```

**Sonarr (Custom List):**
```

https://raw.githubusercontent.com/api-apoteket/filtered-movies/main/filtered_tv_shows_sonarr.json

```

## 🎯 Radarr & Sonarr Setup

### Radarr (Movies)

1. Go to **Settings → Import Lists → +**
2. Choose **StevenLu Custom**
3. Set **URL** to: `https://raw.githubusercontent.com/api-apoteket/filtered-movies/main/filtered_movies_radarr.json`
4. Click **Test** and then **Save**

### Sonarr (TV Shows)

1. Go to **Settings → Import Lists → +**
2. Choose **Custom List**
3. Set **URL** to: `https://raw.githubusercontent.com/api-apoteket/filtered-movies/main/filtered_tv_shows_sonarr.json`
4. Click **Test** and then **Save**

> **Note:** Sonarr caches import lists for up to 6 hours. If you test and get "0 results", try deleting and recreating the list to force an immediate refresh. The list syncs automatically every 5 minutes after that.

## 📄 Example JSON Output

**Movies (StevenLu format):**
```json
[
  {
    "title": "Project Hail Mary",
    "imdb_id": "tt12042730"
  },
  {
    "title": "Hoppers",
    "imdb_id": "tt26443616"
  }
]
```

TV Shows (Sonarr Custom List format):

```json
[
  {"TvdbId": 371572},
  {"TvdbId": 433631},
  {"TvdbId": 446831}
]
```

🔧 Run Locally

Prerequisites

· Python 3.8 or later
· A TMDb API Read Access Token

⚠️ IMPORTANT: Use your API Read Access Token, NOT your API Key!

On the TMDb API settings page, you'll see two values:

· API Key – a short string like a1b2c3d4e5... ← Do NOT use this
· API Read Access Token – a long string starting with eyJ... ← USE THIS ONE

Setup

```bash
git clone https://github.com/api-apoteket/filtered-movies.git
cd filtered-movies
pip install requests
export TMDB_API_KEY="your_read_access_token_here"
python3 filter_movies.py
python3 filter_tv_shows.py
```

🤖 Automated Updates

This repository uses GitHub Actions to regenerate both lists daily:

Workflow Runs at Output
update-movies.yml 06:00 UTC filtered_movies_radarr.json
update-tv-shows.yml 07:00 UTC filtered_tv_shows_sonarr.json

To enable this in your own fork, add your TMDb token as a repository secret:

Secret Name Value
TMDB_API_KEY Your TMDb API Read Access Token

📊 Data Source

All data from TMDb. This product uses the TMDb API but is not endorsed or certified by TMDb.

📄 License

MIT – See LICENSE for details.

🙏 Attribution

<img src="https://www.themoviedb.org/assets/2/v4/logos/v2/blue_short-8e7b30f73a4020692ccca9c88bafe5dcb6f8a62a4c6bc55cd9ba82bb2cd95f6c.svg" height="50" alt="TMDb logo">This project uses the TMDb API but is not endorsed or certified by TMDb.
