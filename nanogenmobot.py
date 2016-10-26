#!/usr/bin/env python
# encoding: utf-8
"""
Bot to tweet the collective progress of NaNoGenMo
"""
from __future__ import print_function
import argparse
import datetime
import sys
import twitter  # pip install twitter
import webbrowser
import yaml  # pip install pyyaml

import requests
from pprint import pprint

START_URL = "https://api.github.com/repos/NaNoGenMo/{0}/issues"
HUMAN_URL = "https://github.com/NaNoGenMo/{0}/issues"


# cmd.exe cannot do Unicode so encode first
def print_it(text):
    print(text.encode('utf-8'))


def timestamp():
    """ Print a timestamp and the filename with path """
    print(datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p") + " " +
          __file__)


def bleep(url):
    """ Call the API and return JSON and next URL """
    print(url)
    r = requests.get(url)

    try:
        next = r.links["next"]["url"]
    except KeyError:
        next = None

    print("r.status_code", r.status_code)
    print("X-Ratelimit-Limit", r.headers['X-Ratelimit-Limit'])
    print("X-Ratelimit-Remaining", r.headers['X-Ratelimit-Remaining'])

    if (r.status_code) == 200:
        return r.json(), next

    return None, None


def nanogenmo_issues():
    authors = set()
    issues = []
    admin_issues = []
    preview_issues = []
    completed_issues = []

    # Fetch all issues from GitHub
    next = START_URL.format(args.year)
    while True:
        new_issues, next = bleep(next)
        issues.extend(new_issues)
        print(len(issues))

        if not next:
            break

    # Get unique authors of non-admin issues
    for issue in issues:
        labels = issue["labels"]
        for label in labels:
            if label['name'] == "admin":
                continue
        author = issue["user"]["login"]
        authors.add(author)

    # Count issues
    for issue in issues:
        labels = issue["labels"]
        for label in labels:
            if label['name'] == "admin":
                admin_issues.append(issue)
            elif label['name'] == "preview":
                preview_issues.append(issue)
            elif label['name'] == "completed":
                completed_issues.append(issue)

    pprint(authors)
    print()
    print("Finished")
#     ret = ("Found " + str(len(issues)) + " issues:\n\n"
#            " ➢ " + str(len(authors)) + " humans declared intent\n"
#            " ➢ " + str(len(completed_issues)) + " completed\n"
#            " ➢ " + str(len(preview_issues)) + " previews\n"
#            " ➢ " + str(len(admin_issues)) + " admin issues")
    ret = ("Found " + str(len(issues)) + " #NaNoGenMo issues:\n\n"
           " * " + str(len(authors)) + " humans declared intent\n"
           " * " + str(len(completed_issues)) + " completed\n"
           " * " + str(len(preview_issues)) + " previews\n"
           " * " + str(len(admin_issues)) + " admin issues")
    print_it(ret)
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
    f = open(filename)
    data = yaml.safe_load(f)
    f.close()
    if not data.viewkeys() >= {
            'access_token', 'access_token_secret',
            'consumer_key', 'consumer_secret'}:
        sys.exit("Twitter credentials missing from YAML: " + filename)
    return data


def tweet_it(string, credentials, image=None):
    """ Tweet string and image using credentials """
    if len(string) <= 0:
        return

    # Create and authorise an app with (read and) write access at:
    # https://dev.twitter.com/apps/new
    # Store credentials in YAML file
    auth = twitter.OAuth(
        credentials['access_token'],
        credentials['access_token_secret'],
        credentials['consumer_key'],
        credentials['consumer_secret'])
    t = twitter.Twitter(auth=auth)

    print_it("TWEETING THIS:\n" + string)

    if args.test:
        print("(Test mode, not actually tweeting)")
    else:

        if image:
            print("Upload image")

            # Send images along with your tweets.
            # First just read images from the web or from files the regular way
            with open(image, "rb") as imagefile:
                imagedata = imagefile.read()
            t_up = twitter.Twitter(domain='upload.twitter.com', auth=auth)
            id_img = t_up.media.upload(media=imagedata)["media_id_string"]

            result = t.statuses.update(status=string, media_ids=id_img)
        else:
            result = t.statuses.update(status=string)

        url = "http://twitter.com/" + \
            result['user']['screen_name'] + "/status/" + result['id_str']
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
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--year',
        help="Year to check")
    parser.add_argument(
        '-y', '--yaml',
        # default='/Users/hugo/Dropbox/bin/data/nanogenmobot.yaml',
        default='E:/Users/hugovk/Dropbox/bin/data/nanogenmobot.yaml',
        help="YAML file location containing Twitter keys and secrets")
    parser.add_argument(
        '-nw', '--no-web', action='store_true',
        help="Don't open a web browser to show the tweeted tweet")
    parser.add_argument(
        '-x', '--test', action='store_true',
        help="Test mode: go through the motions but don't tweet anything")
    args = parser.parse_args()

    hacky()

    if not args.year:
        now = datetime.datetime.now()
        args.year = now.year

    credentials = load_yaml(args.yaml)

    tweet = nanogenmo_issues()
    tweet += "\n\n" + HUMAN_URL.format(args.year)

#     tweet = "That's all for this year's #NaNoGenMo, welcome back on 1st "
#             "November {}! Bleep.".format(args.year)

    tweet_it(tweet, credentials)

# End of file
