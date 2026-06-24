"""Single source of truth for the app version and its GitHub home.

The in-app updater (web/update.py) compares __version__ against the latest
GitHub Release tag of GITHUB_OWNER/GITHUB_REPO. Bump __version__ here, then run
`python scripts/release.py` to build and publish a matching release.
"""

__version__ = "0.2.0"

# GitHub repository that hosts releases for the in-app updater.
GITHUB_OWNER = "yechongyi-dot"
GITHUB_REPO = "HeatMap"


def repo_slug() -> str:
    """``owner/repo`` string used to build GitHub API URLs."""
    return f"{GITHUB_OWNER}/{GITHUB_REPO}"
