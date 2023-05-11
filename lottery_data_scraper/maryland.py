import logging
import os
import re
from xmlrpc import client

import html2text
import requests
from selenium import webdriver
from bs4 import BeautifulSoup as bs

from lottery_data_scraper.schemas import GameSchema 
from lottery_data_scraper.util import fetch_html


logger = logging.getLogger(__name__)

s = requests.Session()
h = html2text.HTML2Text()

BASE_URL = "https://www.mdlottery.com"
BASE_INDEX_URL = "https://www.mdlottery.com/games/scratch-offs/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:71.0) Gecko/20100101 Firefox/71.0",
    "Host": "www.mdlottery.com",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.5",
}
INDEX_URL = "https://www.mdlottery.com/wp-admin/admin-ajax.php?action=jquery_shortcode&shortcode=scratch_offs"


def _name(game_div):
    return game_div.find(class_="name").text


def _num(game_li):
    return game_li.find(string="Game: ").next.text


def _price(game_li):
    return int(game_li.find(class_="price").text.replace("$", ""))


def _odds(game_li):
    odds = game_li.find(class_="probability").text
    return float(odds)


def _num_tx(game_li):
    return int(sum(p["available"] + p["claimed"] for p in _prizes(game_li)) * _odds(game_li))


def _prizes(game_li):
    table = game_li.find("table")
    rows = table.find_all("tr")[1:]
    prizes = []
    for row in rows:
        cells = row.find_all("td")
        prize = cells[0].text
        value = float(re.sub(r"[\$,]", "", prize))
        available = int(cells[2].text)
        claimed = int(cells[1].text) - available
        prizes.append(
            {"prize": prize, "value": value, "available": available, "claimed": claimed}
        )
    return prizes


def _how_to_play(game_li):
    return h.handle(str(game_li.find(class_="how-to-play")))


def games(requests, url):
    # Headless needed to run on server with no display
    options = webdriver.firefox.options.Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)
    driver.get(url)
    html = driver.page_source
    soup = bs(html, "lxml")
    game_lis = soup.find_all("li", class_="ticket")
    games = [
        {
            "name": _name(game_li),
            "game_id": _num(game_li),
            "url": BASE_INDEX_URL,
            "how_to_play": _how_to_play(game_li),
            "price": _price(game_li),
            "state": "md",
            "num_tx_initial": _num_tx(game_li),
            "prizes": _prizes(game_li),
        }
        for game_li in game_lis
    ]
    return games


def main():
    result_games = []
    for game in games(s, INDEX_URL):
        result_games.append(game)
    return result_games



if __name__ == "__main__":
    games = main()
    schema = GameSchema(many=True)
    print(schema.dumps(games))
