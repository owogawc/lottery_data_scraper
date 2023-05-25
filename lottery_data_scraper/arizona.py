import logging
import os
import re
import traceback
from selenium import webdriver
from datetime import datetime, date


from bs4 import BeautifulSoup as bs
import requests
import json

from lottery_data_scraper.util import fetch_html
from lottery_data_scraper.schemas import GameSchema

logger = logging.getLogger(__name__)

BASE_URL = "https://www.arizonalottery.com"
INDEX_URL = "https://www.arizonalottery.com/scratchers/#all"


# TODO: add how to play. It uses lottery symbols. Not just straight text
def get_games(site_url):
    html = fetch_html(site_url)
    soup = bs(html, "lxml")

    games_soup = soup.find_all("div", class_="col-md-6 col-lg-3 g")
    game_urls = [BASE_URL + game.find_next("a")["href"] for game in games_soup]

    return game_urls


def process_game(game_url):
    """
    Using Selenium to run JavaScript
    """
    options = webdriver.chrome.options.Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    driver.get(game_url)
    html = driver.page_source
    soup = bs(html, "lxml")

    game_id = re.search(r"\d+", soup.find("h1").text).group(0)

    name = (soup.find("h1").text).split(" #")[0]

    price = int(re.search(r"\d+", soup.find("div", class_="info").text).group(0))

    prizes = [
        {
            "prize": field[0].text.replace("$", ""),
            "value": int(field[0].text.replace("$", "").replace(",", ""))
            if "Million" not in field[0].text
            else float(field[0].text.replace("$", "").split(" ")[0]) * 100000,
            "available": int((field[2].text.split("of")[0]).replace(",", "")),
            "claimed": int((field[2].text.split("of")[1]).replace(",", "")),
        }
        for field in [row.find_all("td") for row in soup.find_all("tr")[1:-1]]
    ]

    odds = float(
        (soup.find("table", id="prize-odd-chart").find_next("p").text).split("in")[1]
    )

    num_of_tix = int(sum(row["available"] for row in prizes) * odds)

    image_urls = f"{BASE_URL}{soup.find('div', class_='card gameTicket').find_next('img')['src']}"

    game = {
        "game_id": game_id,
        "name": name,
        "url": game_url,
        "state": "az",
        "price": price,
        "num_tx_initial": num_of_tix,
        "prizes": prizes,
        "image_urls": [image_urls],
    }

    return game


def main():
    game_urls = get_games(INDEX_URL)
    games = []

    for url in game_urls:
        try:
            game = process_game(url)
        except Exception as e:
            logger.error(f"Unable to process game: {url}")
            logger.warning(e)
            traceback.print_exception(e)
        games.append(game)
    return games


if __name__ == "__main__":
    games = main()
    schema = GameSchema(many=True)
    print(schema.dumps(games))
