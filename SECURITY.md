# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please **do not** create a public issue. Instead, report it privately.

### How to Report

- **Email:** [dev@denied.se]
- **GitHub:** Use the "Report a vulnerability" button under the Security tab

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fixes (optional)

### Response Timeline

| Stage | Timeframe |
|-------|-----------|
| Initial acknowledgment | Within 48 hours |
| Assessment | Within 5 business days |
| Fix implementation | Based on severity |
| Public disclosure | After fix is released |

### Scope

This security policy covers:

- The `filter_movies.py` script
- The `filtered_movies.json` data file
- The GitHub Actions workflows
- The repository configuration

### Out of Scope

- The TMDb API itself (report those to TMDb)
- Third-party dependencies (report to their respective maintainers)

## Security Best Practices

### For Contributors

1. **Never commit secrets** – API keys, tokens, or credentials
2. **Use environment variables** – All secrets are stored as GitHub Secrets or local `.env` files
3. **Review dependencies** – Dependabot keeps them updated automatically
4. **Check workflows** – GitHub Actions workflows are reviewed for injection risks

### API Key Handling

This project uses TMDb API keys. Keys are:

- Stored as GitHub Secrets (`TMDB_API_KEY`)
- Injected via environment variables
- Never committed to the repository
- Listed in `.gitignore` (`.env` files)

If you accidentally expose a key:

1. Revoke it immediately at [TMDb API Settings](https://www.themoviedb.org/settings/api)
2. Follow the [GitHub guide for removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
3. Contact the maintainer

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest commit on `main` | ✅ |
| Older commits | ❌ |

## Acknowledgments

We appreciate responsible disclosure. Security researchers who report valid vulnerabilities will be acknowledged here (with permission).
