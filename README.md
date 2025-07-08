# Daily Astronomy Article Reader

> This is my daily arXiv reader. There are many like it, but this one is mine.

`papermate` is a daily arXiv article summarizer, built for those odd astronomers
who never leave their terminal. This library provides the `papermate` and
`papermate-daily` command-line scripts, which run a
[curses](https://docs.python.org/3/library/curses.html) based program in the
terminal, using the API of [NASA ADS](https://ui.adsabs.harvard.edu) and the
wonderful [`ads`](https://github.com/andycasey/ads) package to
provide the titles, authors and abstracts of relevant papers submitted to arXiv
that day.


## Installation

`papermate` can be installed directly from this repo:

```bash
pip install git+https://github.com/nmdickson/papermate.git
```

The necessary scripts should be placed in your path automatically. You may want
to install as an isolated application with `pipx`.

You will also need a NASA ADS API key. A new token can be generated from the
account settings page of the ADS website, and a copy should be stored either
in `~/.ads/dev_key`, as an environment variable named `ADS_DEV_KEY`, or under
the `"ads_api_key"` option in your config file (see below).

This project has been tested on Linux (Ubuntu) and WSL, but should in theory
work anywhere that curses does.


## Usage

Running the `papermate` command will option an options menu, which you can
navigate with the arrow keys.

The default use case is the "Daily" mode, which can also be run directly using
`papermate-daily`.

The program should handle, on the fly, font and window resizes, but it will
eventually overlap and then crash if you make the window too small to fit
everything.


### Config Files

`papermate` is controlled through a single TOML config file (currently must be
at `$HOME/.config/papermate.toml`). This file controls both the application
settings, and the actual queries used to search for relevant papers.

Some explanations are given below. See also the example config file in this
repository.


#### Settings

First, under the `[Config]` table header, you may set a variety of options.

Defaults:
```TOML
[Config]
skip_weekends = true
default_library = "papermate"
download_location = "/home/user/Downloads"
log_file = "/home/user/.local/share/pmate.log"
show_relative_date = true
show_loading = true
ads_api_key = ""
reminder = false
reminder_times = [["Mon", "Tue", "Wed", "Thu", "Fri"], [11]]
invert_colours = false
```

**skip_weekends**: Whether to automatically skip over Saturday and Sunday,
which never have articles posted on arXiv, when scrolling.

**default_library**: The name of the ADS library to use by default when adding
a paper to a library.

**download_location**: Folder to place downloaded article PDFs when using the
download option.

**log_file**: Location of the log file with debugging information.

**show_relative_date**: Show at the top of the screen the date relative to today
(e.g. "yesterday", "2 days ago", etc.)

**show_loading**: Show a popup loading notice when fetching new articles.

**reminder**: Attempt to setup a cron job which will broadcast a
reminder at the times specified, using `wall`.

**reminder_times**: The days and times that the cronjob should run at. First
element should be an array of days, and second an array of hours.

**invert_colours**: Attempt to invert the colours of the program (white to
black and vice versa). This is just because curses doesn't always respect the
colours of your terminal directly.

**ads_api_key**: The NASA ADS API token can be placed here, instead of at the
other options listed above.


#### Queries

Next, any number of TOML tables are used to set the "queries" that actually
define the ADS searches made to find relevant papers.
The queries defined here are assembled into one or more search strings and
combined with the `arxiv_class="astro-ph.*"` and `entdate={DATE}` to search
ADS for the corresponding articles posted that day, matching the query.


The name of the table sets the name of the query (appearing in the side bar),
while below it each key-value pair represents one of the possible search terms
used by ADS.

The most common terms are likely "full" (searches the full text for the given
words), "author" or "orcid" (searches for papers by the given author name or
ORCID), and "object" (searches for a given astronomical object.)

Example:
```TOML
["Clusters"]
full = "Globular Cluster"
full = "Open Cluster"

["Black Holes"]
full = "Black Holes"

["Me"]
orcid = "0000-0002-6865-2369"

["Omega Cen"]
object = "NGC5139"

```

You can also use some of the second-order operations provided by ADS, by adding
them to the end of the query name. The query terms that follow will be used by
ADS to find the papers to apply that operation to.

For example, to find the papers citing a given author or paper, you could use:
```TOML
["Citing me".citations]
orcid = "0000-0002-6865-2369"

["Using limepy".citations]
bibcode = "2015MNRAS.454..576G"
```

The supported operations are: similar, reviews, trending, useful and citations.


For more information on all of the possible ADS search terms and operations,
see the [ADS help pages](https://ui.adsabs.harvard.edu/help/api).


### Controls

By default, the `papermate-daily` program will read your config file, search
for your queries on todays date, and open to a "list" view, which shows a list
of articles found, organized by query.
The list will show the title, authors, bibcode and beginning of the abstract
of each paper.

You can scroll through the list using the arrow keys. Holding shift will scroll
through a whole page at a time.
You can also scroll backwards and forwards in days using "z" and "x". Scrolling
through days will take some time at first, as the search queries are executed
again, but each day will be cached after searching.

Clicking "Enter" on an article will bring up the "detailed" view, with more
article details and the full author list and abstract.

From this page you can also download the article PDF ("d"), open the article
in your browser ("o"), add it to an ADS library ("l") or copy the bibcode to
your clipboard ("c").
You can return to the list view by pressing "b".


# Note

This is/was entirely a personal project that I slowly built over the course of
many years to suit my specific needs. I use it every day, but that doesn't mean
it's very polished, and it may not meet anyone elses needs.


# Known Issues and Future Features

- Fix occasional flickering occurs when scrolling through articles.
    This is caused by the redrawing of the entire screen rather than just the
    arrow, and should be an easy fix.

- Add "goto" a specific date functionality.
    The hard part is actually getting a user inputted date nicely.

- Allow config file to be placed anywheres, not just under `~/.config`.

- Add actual help text.
    Even though having a "help" button that just sends you into a black hole is
    pretty funny.

- Fix many text overlaps.
    Mostly caused by hardcoding some things early in the project. Slowly being
    fixed.

- Optionally remove articles appearing in multiple queries.

- Add more options like different keymaps to "Config"

- Some days no articles appear at all (until the next day).
    This seems to be due to when the articles are indexed by ADS. There's
    nothing that can be done about it, except coming back the next day. It seems
    to happen most on Thursdays.
    (I just take it as a vacation-from-reading day).

- Allow non "astro-ph" arXiv classes.
    Should be as simple as allowing "arxiv_class" to be a search term. Might
    already work.
