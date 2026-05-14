# filtered-movies — Claude Code Guide

Automatically updated lists of high-value movies and TV shows for direct import into Radarr and Sonarr. Data is fetched from The Movie Database (TMDb) and refreshed daily via GitHub Actions.

## Tech Stack

- Python 3
- TMDb API
- GitHub Actions (scheduled daily runs)

## Output Files

| File | Target | Filter |
|------|--------|--------|
| `filtered_movies_radarr.json` | Radarr | Budget ≥ $100,000,000, released this year |
| `filtered_tv_shows_sonarr.json` | Sonarr | Premiered this year on major networks/streamers |

## Key Scripts

```
filter_movies.py        # Queries TMDb, writes filtered_movies_radarr.json
filter_tv_shows.py      # Queries TMDb, writes filtered_tv_shows_sonarr.json
```

## Dev Commands

```bash
python filter_movies.py
python filter_tv_shows.py
```

## Conventions

- `TMDB_API_KEY` must be set as a secret/env var — never hardcoded
- JSON output files are committed by the workflow ([skip ci] commits)
- Keep filter logic simple and well-commented so criteria are easy to adjust
