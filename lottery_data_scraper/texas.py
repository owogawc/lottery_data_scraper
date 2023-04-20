"""
Scrapes the Louisiana lottery website for scratch-off ticket
data and calculates the expected value for each game.

Louisiana publishes the number of tickets printed and how many
tickets are printed at each prize level.

We can calculated the expected value of a game by summing
the value of all the prizes and dividing that by the cost
of all the tickets.

The texas lottery website has an "top prizes remaining" or an "index" page that 
has links to every game that could still be profitable.
Each individual game has a section for the "game rules" page and a prize table.
We can use each individual game page to gather the important data, and 
then run our calculations.

Website that we'll be scraping:
http://www.txlottery.org/export/sites/lottery/Games/Scratch_Offs/all.html

Example usage:
    python -m texas
Or:
    LOGLEVEL=DEBUG USE_CACHE=True python -m texas

The following behavior is configurable through shell environment variables.

Set LOGLEVEL to print useful debug info to console.
LOGLEVEL=[DEBUG,INFO,WARNING,ERROR,CRITICAL]
Defaults to WARNING.

Set USE_CACHE to cache responses. This speeds up development
and is nice to the servers we're hitting.
USE_CACHE=[True]
Defaults to False. Note: Setting this env variable to the string False
will cause it to use cache because the string "False" evaluates to Truthy.
Either set it to True or don't set it.
"""

import logging
import os
import re
from xmlrpc import client

from bs4 import BeautifulSoup as bs
import pandas as pd
import requests
from lottery_data_scraper.schemas import GameSchema 
from lottery_data_scraper.util import fetch_html

logger = logging.getLogger(__name__)

BASE_URL = "http://www.txlottery.org"
INDEX_URL = (
    "http://www.txlottery.org/export/sites/lottery/Games/Scratch_Offs/all.html"
)


def parse_index(html):
    soup = bs(html, "lxml")
    table = soup.find("table")
    game_hrefs = table.select("tr > td > a")
    game_urls = list(map(lambda x: BASE_URL + x.attrs["href"], game_hrefs))
    return game_urls


def parse_game(url, html):
    soup = bs(html, "lxml")
    price = int(
        re.match(
            r"\$(\d+)",
            soup.select("h3 > img")[0].attrs["alt"]
        ).group(1)
    )
    game_details = soup.select(".large-4.cell > h3")[0].parent.text.strip()
    title = soup.select(".large-12.cell > .text-center > h2")[0].text.split(" - ")
    name = title[1]
    num = title[0][-4:]
    num_tx = int(
        re.match(
            r".*?([\d,]+)",
            soup.find(string=re.compile(r"There are approximately [\d,]+.*")).strip()
        ).group(1).replace(",", "")
    )
    # Prizes
    table = soup.find("table")
    df = pd.read_html(str(table))[0]
    df = df.replace("---", 0)
    df.iloc[:, 0] = df.iloc[:, 0].str.replace("$", "", regex=False)  # noqa: E231
    prizes = []
    for prize, total, claimed in [list(r[1]) for r in df.iterrows()]:
        match = re.match(r"\$?([\d,]+).*wk.*", prize)
        if match:
            value = float(match.group(1).replace(",", "")) * 20 * 52
            prize = match.group(0)
        else:
            value = float(prize.replace(",", ""))
            prize = "$" + prize
        prizes.append(
            {
                "prize": prize,
                "value": value,
                "claimed": int(claimed),
                "available": int(total) - int(claimed),
            }
        )
    game = {
        "name": name,
        "game_id": num,
        "url": url,
        "price": price,
        "state": "tx",
        "num_tx_initial": num_tx,
        "prizes": prizes,
    }
    return game


def _parse_game(url, html):
    try:
        return parse_game(url, html)
    except Exception as e:
        logger.warning("Unable to parse {}.\n{}".format(url, e))
    return None


def main():
    index_html = fetch_html(INDEX_URL)
    game_urls = parse_index(index_html)
    url_htmls = zip(game_urls, [fetch_html(url) for url in game_urls])
    games = [_parse_game(url, html) for url, html in url_htmls]
    games = [game for game in games if game is not None]
    return games



if __name__ == "__main__":
    games = main()
    schema = GameSchema(many=True)
    print(schema.dumps(games))