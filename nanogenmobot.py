#!/usr/bin/env python
"""
Bot to toot the collective progress of NaNoGenMo
"""
from __future__ import annotations

import argparse
import datetime
import sys
import webbrowser
from pprint import pprint

import requests  # pip install requests
import yaml  # pip install PyYAML
from mastodon import Mastodon  # type: ignore  # pip install Mastodon.py

START_URL = "https://api.github.com/repos/{}/{}/issues?state=all"
HUMAN_URL = "https://github.com/{}/{}/issues"


def timestamp() -> None:
    """Print a timestamp and the filename with path"""
    print(datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p") + " " + __file__)


def bleep(url: str):
    """Call the API and return JSON and next URL"""
    print(url)
    r = requests.get(url, timeout=10)

    try:
        next_page = r.links["next"]["url"]
    except KeyError:
        next_page = None

    print("r.status_code", r.status_code)
    print("X-Ratelimit-Limit", r.headers["X-Ratelimit-Limit"])
    print("X-Ratelimit-Remaining", r.headers["X-Ratelimit-Remaining"])

    if r.status_code == 200:
        return r.json(), next_page

    return None, None


def org_repo(year: int) -> tuple[str, str | int]:
    """Get the org and repo for a given year"""
    if year <= 2012:
        msg = "No NaNoGenMo yet!"
        raise ValueError(msg)
    if year == 2013:
        return "dariusk", "NaNoGenMo"
    elif year <= 2015:
        return "dariusk", f"NaNoGenMo-{year}"
    else:
        return "NaNoGenMo", year


def nanogenmo_issues(year: int) -> str:
    authors = set()
    issues = []
    admin_issues = []
    preview_issues = []
    completed_issues = []

    # Fetch all issues from GitHub
    org, repo = org_repo(year)
    next_page = START_URL.format(org, repo)
    while True:
        new_issues, next_page = bleep(next_page)
        issues.extend(new_issues)
        print(len(issues))

        if not next_page:
            break

    # Get unique authors of non-admin issues
    for issue in issues:
        labels = issue["labels"]
        admin = any(label["name"] == "admin" for label in labels)
        if not admin:
            author = issue["user"]["login"]
            authors.add(author)

    # Count issues
    for issue in issues:
        labels = issue["labels"]
        for label in labels:
            if label["name"] == "admin":
                admin_issues.append(issue)
            elif label["name"] == "preview":
                preview_issues.append(issue)
            elif label["name"] == "completed":
                completed_issues.append(issue)

    pprint(authors)
    print()
    print("Finished")

    if len(preview_issues) == 1:
        previews = "preview"
    else:
        previews = "previews"

    ret = (
        f"Found {len(issues)} #NaNoGenMo issues:\n\n"
        f" * {len(authors)} humans declared intent\n"
        f" * {len(completed_issues)} completed\n"
        f" * {len(preview_issues)} {previews}\n"
        f" * {len(admin_issues)} admin issues"
    )
    print(ret)
    return ret


def load_yaml(filename: str) -> dict[str, str]:
    """
    File should contain:
    mastodon_client_id: TODO_ENTER_YOURS
    mastodon_client_secret: TODO_ENTER_YOURS
    mastodon_access_token: TODO_ENTER_YOURS
    """
    with open(filename) as f:
        data: dict[str, str] = yaml.safe_load(f)

    if not data.keys() >= {
        "mastodon_client_id",
        "mastodon_client_secret",
        "mastodon_access_token",
    }:
        sys.exit(f"Mastodon credentials missing from YAML: {filename}")
    return data


def toot_it(
    status: str,
    credentials: dict[str, str],
    image_path: str | None = None,
    *,
    test: bool = False,
    no_web: bool = False,
) -> None:
    """Toot using credentials"""
    if len(status) <= 0:
        return

    # Create and authorise an app with (read and) write access following:
    # https://github.com/hugovk/mastodon-tools/blob/main/mastodon_create_app.py
    # or:
    # https://gist.github.com/aparrish/661fca5ce7b4882a8c6823db12d42d26
    # Store credentials in YAML file
    api = Mastodon(
        credentials["mastodon_client_id"],
        credentials["mastodon_client_secret"],
        credentials["mastodon_access_token"],
        api_base_url="https://mas.to",
    )

    print("TOOTING THIS:\n", status)

    if test:
        print("(Test mode, not actually tooting)")
        return

    media_ids = []
    if image_path:
        print("Upload image")

        media = api.media_post(media_file=image_path)
        media_ids.append(media["id"])

    toot = api.status_post(status, media_ids=media_ids, visibility="public")

    url = toot["url"]
    print("Tooted:\n" + url)
    if not no_web:
        webbrowser.open(url, new=2)  # 2 = open in a new tab, if possible


def exit_bot(*, test: bool = False) -> None:
    if not test:
        sys.exit("Don't run!")


def hacky(*, test: bool = False) -> None:
    now = datetime.datetime.now()

    if now.month < 11:
        exit_bot(test=test)
    elif now.month == 12 and now.day > 6:
        exit_bot(test=test)

    # Only run once a day
    if now.hour == 22:
        return
    else:
        exit_bot(test=test)


def main() -> None:
    timestamp()

    parser = argparse.ArgumentParser(
        description="Bot to toot the collective progress of NaNoGenMo",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--year", type=int, help="Year to check")
    parser.add_argument(
        "-y",
        "--yaml",
        # default='/Users/hugo/Dropbox/bin/data/nanogenmobot.yaml',
        help="YAML file location containing Mastodon keys and secrets",
    )
    parser.add_argument(
        "-nw",
        "--no-web",
        action="store_true",
        help="Don't open a web browser to show the tooted toot",
    )
    parser.add_argument(
        "-x",
        "--test",
        action="store_true",
        help="Test mode: go through the motions but don't toot anything",
    )
    args = parser.parse_args()

    hacky(test=args.test)

    if not args.year:
        now = datetime.datetime.now()
        args.year = now.year

    credentials = load_yaml(args.yaml)

    org, repo = org_repo(args.year)
    status = nanogenmo_issues(args.year)
    status += "\n\n" + HUMAN_URL.format(org, repo)

    # status = f"That's all for this year's #NaNoGenMo, welcome back on 1st "
    #         f"November {args.year}! Bleep."

    toot_it(status, credentials, test=args.test, no_web=args.no_web)


if __name__ == "__main__":
    main()
