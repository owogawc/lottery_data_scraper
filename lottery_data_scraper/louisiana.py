"""
Scrapes the Louisiana lottery website for scratch-off ticket
data and calculates the expected value for each game.

Louisiana publishes the number of tickets printed and how many
tickets are printed at each prize level.

We can calculated the expected value of a game by summing
the value of all the prizes and dividing that by the cost
of all the tickets.

The louisianalottery website has an "top prizes remaining" or an "index" page that 
has links to every game that could still be profitable.
Each individual game has a section for the "game rules" page and a prize table.
We can use each individual game page to gather the important data, and 
then run our calculations.

Website that we'll be scraping:
https://louisianalottery.com/scratch-offs/top-prizes-remaining

Example usage:
    python -m louisiana
Or:
    LOGLEVEL=DEBUG USE_CACHE=True python -m louisiana

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

import sys
import traceback
from copy import deepcopy
import locale
import logging
import os
import re
from bs4 import BeautifulSoup as bs
import requests
import pandas as pd
from lottery_data_scraper.schemas import GameSchema 
from lottery_data_scraper.util import fetch_html

logger = logging.getLogger(__name__)

# It's worth assigning to constants values that are used in many
# places throughout a script.
BASE_URL = "http://www.louisianalottery.com"
INDEX_URL = "https://louisianalottery.com/scratch-offs/top-prizes-remaining"

def parse_index(html):
    soup = bs(html, "lxml")
    table = soup.find("table")
    game_hrefs = table.select("tr > td > a")
    game_urls = list(map(lambda x: "https:" + x.attrs["href"], game_hrefs))
    return game_urls

# TODO: convert pandas to beautiful soup
def parse_game(url, html):
    soup = bs(html, "lxml")
    price = soup.select('div[id="scratch-off-prize-info"] td')[1].text.replace("$", "")
    name = soup.find(class_="scratch-off-title").text
    num = url.split("/")[-2]
    grand_prize_row = soup.select(
        'div[id="scratch-off-table-tier"] table > tbody > tr'
    )[0]
    grand_prize_odds = float(
        grand_prize_row.select("td")[1].text.split(" in ")[1].replace(",", "",)
    )
    grand_prize_num = int(grand_prize_row.select("td")[2].text)
    num_tx = int(grand_prize_odds * grand_prize_num)
    table = soup.find_all("table")[2]
    df = pd.read_html(str(table))[0]
    df = df.replace("TICKET", price)
    prizes = [
        {
            "prize": prize,
            "value": float(prize.replace("$", "").replace(",", "")),
            "claimed": int(claimed),
            "available": int(total) - int(claimed),
        }
        for prize, _, total, claimed in [list(r[1])[:4] for r in df.iterrows()]
    ]
    game = {
        "name": name,
        "game_id": num,
        "url": url,
        "state": "la",
        "price": float(price),
        "num_tx_initial": num_tx,
        "prizes": prizes,
    }
    return game


def main():
    index_html = fetch_html(INDEX_URL)
    game_urls = parse_index(index_html)
    url_htmls = zip(game_urls, [fetch_html(url) for url in game_urls])
    games = []
    for url, html in url_htmls:
        try:
            game = parse_game(url, html)
        except Exception as e:
            logger.error("Unable to parse {}.\n{}".format(url, e))
            continue
        games.append(game)
    return games


if __name__ == "__main__":
    games = main()
    schema = GameSchema(many=True)
    print(schema.dumps(games))
