#!/usr/bin/env python3
"""Generate public GitHub statistics, or an explicitly offline placeholder."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape


class StatsError(Exception):
    """Safe-to-display API failure without credentials or response bodies."""


def request_json(path, token, timeout):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "rachts-profile-stats", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urlopen(Request("https://api.github.com" + path, headers=headers), timeout=timeout) as response:
            return json.load(response)
    except HTTPError as exc:
        raise StatsError(f"GitHub returned HTTP {exc.code}; check access, rate limits, and username.") from None
    except (URLError, TimeoutError, OSError, ValueError):
        raise StatsError("GitHub request failed (network, timeout, or invalid JSON).") from None


def count(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise StatsError("GitHub returned an invalid count.")
    return value


def fetch_stats(username, token, timeout):
    user = request_json(f"/users/{username}", token, timeout)
    if not isinstance(user, dict):
        raise StatsError("GitHub returned an invalid profile.")
    result = {"Public repositories (profile)": count(user.get("public_repos")),
              "Followers": count(user.get("followers")), "Following": count(user.get("following"))}
    owned = {}
    for page in range(1, 1001):
        repos = request_json(f"/users/{username}/repos?type=owner&per_page=100&page={page}&sort=full_name&direction=asc", token, timeout)
        if not isinstance(repos, list):
            raise StatsError("GitHub returned an invalid repository list.")
        for repo in repos:
            if not isinstance(repo, dict) or not isinstance(repo.get("owner"), dict):
                raise StatsError("GitHub returned an invalid repository.")
            if repo.get("private") is False and repo.get("fork") is False and str(repo["owner"].get("login", "")).lower() == username.lower():
                owned[count(repo.get("id"))] = count(repo.get("stargazers_count"))
        if len(repos) < 100:
            break
    else:
        raise StatsError("Repository pagination limit exceeded; no partial statistics written.")
    result["Owned public non-fork repositories"] = len(owned)
    result["Stars on owned public non-fork repos"] = sum(owned.values())
    return result


def render_stats(username, stats=None, updated=None):
    placeholder = stats is None
    rows = stats if stats is not None else {"Public repositories (profile)": "—", "Followers": "—", "Following": "—", "Owned public non-fork repositories": "—", "Stars on owned public non-fork repos": "—"}
    description = ("Offline starter placeholder. GitHub has not been queried; dashes are unknown, not zero." if placeholder else "Public GitHub REST snapshot. Profile repository count includes forks. Stars exclude forks, private repositories, and repositories owned by others.")
    title = f"{username} · GitHub statistics"
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="640" height="330" viewBox="0 0 640 330" role="img" aria-labelledby="title desc"><title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc><rect width="640" height="330" rx="16" fill="#0d1117"/><g font-family="ui-monospace,monospace" fill="#e6edf3">',
             f'<text x="24" y="38" font-size="22">{escape(title)}</text><path d="M24 55H616" stroke="#A89B8C" stroke-width="2"/>']
    for i, (label, value) in enumerate(rows.items()):
        y = 91 + i * 36
        parts.append(f'<text x="24" y="{y}" font-size="15">{escape(str(label))}</text><text x="608" y="{y}" text-anchor="end" font-size="18">{escape(str(value))}</text>')
    caption = "Offline placeholder · statistics not fetched" if placeholder else f"Updated {updated} · GitHub REST public data"
    parts.append(f'<text x="24" y="278" font-size="12">{escape(caption)}</text><text x="24" y="303" font-size="11">Profile repo count includes forks; star total uses owned public non-forks only.</text></g></svg>\n')
    return "".join(parts)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", default="rachts")
    parser.add_argument("--output", type=Path, default=Path("assets/stats.svg"))
    parser.add_argument("--timeout", type=float, default=20, help="per-request timeout in seconds (0–120, exclusive of zero)")
    parser.add_argument("--placeholder", action="store_true", help="offline starter; never calls GitHub or reads GITHUB_TOKEN")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", args.username):
        parser.error("username must be a GitHub login, not a URL")
    if not 0 < args.timeout <= 120:
        parser.error("timeout must be greater than 0 and at most 120")
    try:
        stats = None if args.placeholder else fetch_stats(args.username, os.environ.get("GITHUB_TOKEN"), args.timeout)
        updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        svg = render_stats(args.username, stats, updated)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(svg, encoding="utf-8")
    except StatsError as exc:
        print(f"stats: {exc}", file=sys.stderr)
        return 1
    except OSError:
        print("stats: could not write output file", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
