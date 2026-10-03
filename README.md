# [@NaNoGenMoBot](https://twitter.com/NaNoGenMoBot)

[![Test](https://github.com/hugovk/nanogenmobot/actions/workflows/test.yml/badge.svg)](https://github.com/hugovk/nanogenmobot/actions/workflows/test.yml)
[![Python: 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: Black](https://img.shields.io/badge/code%20style-Black-000000.svg)](https://github.com/psf/black)

Bot to toot the collective progress of the national novel generation month
([NaNoGenMo](https://nanogenmo.github.io)).

See the bot in action at
**[![](https://mas.to/packs/media/icons/favicon-16x16-c58fdef40ced38d582d5b8eed9d15c5a.png)@NaNoGenMoBot](https://mas.to/@NaNoGenMoBot)**.

## How it runs

[`toot.yml`](.github/workflows/toot.yml) runs on GitHub Actions daily during NaNoGenMo,
from 1 November to 6 December. The Mastodon credentials YAML is stored in the
`NANOGENMOBOT_YAML` repository secret. To run it by hand, or for a dry run that doesn't
toot, use "Run workflow" on the
[Actions tab](https://github.com/hugovk/nanogenmobot/actions/workflows/toot.yml).
