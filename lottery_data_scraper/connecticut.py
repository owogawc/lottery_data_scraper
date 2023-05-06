import logging
import os
import re
import sys
import traceback
from xmlrpc import client

from bs4 import BeautifulSoup as bs
import html2text
import requests
from lottery_data_scraper.schemas import GameSchema 
from lottery_data_scraper.util import fetch_html

logger = logging.getLogger(__name__)

h = html2text.HTML2Text()
h.ignore_links = True

BASE = "https://www.ctlottery.org"

INDEX = "https://ctlottery.org/ScratchGamesTable"


headers = {
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:70.0) Gecko/20100101 Firefox/70.0",
    "Referer": "https://www.ctlottery.org/ScratchGames",
}



def get_games_urls(url):
    html = fetch_html(url)
    soup = bs(html, "lxml")
    table = soup.find("table")
    game_hrefs = table.select("tr > td > a")
    game_urls = list(map(lambda x: BASE + x.attrs["href"], game_hrefs))
    return game_urls

def parse_game(game_url):
    # Each game page has two tables
    #   Table 1: Ticket Price, Num_Tx_remaining, Odds
    #   Table 2: Prize Table

    game_html = fetch_html(game_url)
    game_soup = bs(game_html, "lxml")

    name = game_soup.find("h2").text
    game_id = re.match(r"GAME #(\d*)",game_soup.find(class_="heading-sub-info").text).group(1)

    #soup for table 1
    table_one = game_soup.find(class_="img-detail-block")

    price = int(re.search(r"Ticket Price:\$(\d*)", table_one.text).group(1))
    
    num_tx_str = re.search(r"Total # of Tickets:([\d*][,\d*]+)", table_one.text).group(1)
    num_tx_initial = int(num_tx_str.replace(",", ""))


    #soup for table 2
    table_two = game_soup.find(class_="unclaimed-prize-wrap")
    prize_rows = (
     table_two.find("tbody").find_all("tr")
    )
    prizes = []
    for row in prize_rows:
        prize, total, available = [r.text for r in row.find_all("td")]
        total = int(total.replace(",", ""))
        available = int(available.replace(",", ""))
        # one-off handlers...
        if re.search(r"(?i)month.*for.*life", prize):
            value = re.search(r"[\d,]+", prize).group()
            value = float(value.replace(",", "")) * 20 * 12
        elif re.search(r"(?i)$\d+ million", prize):
            value = float(re.search(r"\d+").group()) * 1000000
        else:
            value = re.search(r"[\d,]+", prize).group()
            value = float(value.replace("$", "").replace(",", ""))
        prizes.append(
            {
                "prize": prize,
                "value": value,
                "claimed": total - available,
                "available": available,
            }
        )

    how_to_play_soup = game_soup.find(class_="play-text-wrap")
    #remove heading and button tags
    how_to_play_soup.h3.extract()
    how_to_play_soup.a.extract()

    how_to_play = h.handle(how_to_play_soup.text)

    image_urls = BASE + game_soup.find(id="ticket_image").attrs["src"]

    game = {
        "state": "ct",
        "game_id": game_id,
        "name": name,
        "price": price,
        # Individual games are JavaScript links
        "url": game_url,
        "prizes": prizes,
        "num_tx_initial": num_tx_initial,
        "how_to_play": how_to_play,
        "image_urls": image_urls
    }
    return game

def main():
    games_urls = get_games_urls(INDEX)
    games = []
    for game in games_urls:
        try:
            game = parse_game(game)
        except Exception as e:
            logger.error("Unable to parse game {}.\n{}".format(game, e))
    games.append(game)
    return games


if __name__ == "__main__":
    games = main()
    schema = GameSchema(many=True)
    print(schema.dumps(games))

