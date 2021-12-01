#!/usr/bin/env python
# encoding: utf-8
"""
Bot to tweet the collective progress of NaNoGenMo
"""
import argparse
import datetime
import sys
import webbrowser
from pprint import pprint

import requests  # pip install requesets
import twitter  # pip install twitter
import yaml  # pip install PyYAML

START_URL = "https://api.github.com/repos/{}/{}/issues?state=all"
HUMAN_URL = "https://github.com/{}/{}/issues"


def timestamp():
    """Print a timestamp and the filename with path"""
    print(datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p") + " " + __file__)


def bleep(url):
    """Call the API and return JSON and next URL"""
    print(url)
    r = requests.get(url)

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


def org_repo(year: int) -> (str, str):
    """Get the org and repo for a given year"""
    if year <= 2012:
        raise ValueError("No NaNoGenMo yet!")
    if year == 2013:
        return "dariusk", "NaNoGenMo"
    elif year <= 2015:
        return "dariusk", f"NaNoGenMo-{year}"
    else:
        return "NaNoGenMo", year


def nanogenmo_issues(year):
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
        for label in labels:
            if label["name"] == "admin":
                continue
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


def load_yaml(filename):
    """
    File should contain:
    consumer_key: TODO_ENTER_YOURS
    consumer_secret: TODO_ENTER_YOURS
    access_token: TODO_ENTER_YOURS
    access_token_secret: TODO_ENTER_YOURS
    wordnik_api_key: TODO_ENTER_YOURS
    """
    with open(filename) as f:
        data = yaml.safe_load(f)

    if not data.keys() >= {
        "access_token",
        "access_token_secret",
        "consumer_key",
        "consumer_secret",
    }:
        sys.exit("Twitter credentials missing from YAML: " + filename)
    return data


def tweet_it(string, credentials, image=None):
    """Tweet string and image using credentials"""
    if len(string) <= 0:
        return

    # Create and authorise an app with (read and) write access at:
    # https://dev.twitter.com/apps/new
    # Store credentials in YAML file
    auth = twitter.OAuth(
        credentials["access_token"],
        credentials["access_token_secret"],
        credentials["consumer_key"],
        credentials["consumer_secret"],
    )
    t = twitter.Twitter(auth=auth)

    print("TWEETING THIS:\n" + string)

    if args.test:
        print("(Test mode, not actually tweeting)")
    else:

        if image:
            print("Upload image")

            # Send images along with your tweets.
            # First just read images from the web or from files the regular way
            with open(image, "rb") as imagefile:
                imagedata = imagefile.read()
            t_up = twitter.Twitter(domain="upload.twitter.com", auth=auth)
            id_img = t_up.media.upload(media=imagedata)["media_id_string"]

            result = t.statuses.update(status=string, media_ids=id_img)
        else:
            result = t.statuses.update(status=string)

        url = (
            "http://twitter.com/"
            + result["user"]["screen_name"]
            + "/status/"
            + result["id_str"]
        )
        print("Tweeted:\n" + url)
        if not args.no_web:
            webbrowser.open(url, new=2)  # 2 = open in a new tab, if possible


def exit():
    if not args.test:
        sys.exit("Don't run!")


def hacky():
    now = datetime.datetime.now()

    if now.month < 11:
        exit()
    elif now.month == 12 and now.day > 6:
        exit()

    # Only run twice a day
    if now.hour == 10 or now.hour == 22:
        return
    else:
        exit()


if __name__ == "__main__":
    timestamp()

    parser = argparse.ArgumentParser(
        description="Bot to tweet the collective progress of NaNoGenMo",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--year", type=int, help="Year to check")
    parser.add_argument(
        "-y",
        "--yaml",
        # default='/Users/hugo/Dropbox/bin/data/nanogenmobot.yaml',
        help="YAML file location containing Twitter keys and secrets",
    )
    parser.add_argument(
        "-nw",
        "--no-web",
        action="store_true",
        help="Don't open a web browser to show the tweeted tweet",
    )
    parser.add_argument(
        "-x",
        "--test",
        action="store_true",
        help="Test mode: go through the motions but don't tweet anything",
    )
    args = parser.parse_args()

    hacky()

    if not args.year:
        now = datetime.datetime.now()
        args.year = now.year

    credentials = load_yaml(args.yaml)

    org, repo = org_repo(args.year)
    tweet = nanogenmo_issues(args.year)
    tweet += "\n\n" + HUMAN_URL.format(org, repo)

    # tweet = f"That's all for this year's #NaNoGenMo, welcome back on 1st "
    #         f"November {args.year}! Bleep."

    tweet_it(tweet, credentials)


# End of file
