import logging
import os
import re
from xmlrpc import client
import traceback
import html2text
from lottery_data_scraper.schemas import GameSchema
from lottery_data_scraper.util import fetch_html

from bs4 import BeautifulSoup as bs
import requests

logger = logging.getLogger(__name__)

DB_REPO_URI = os.environ.get("DB_REPO_URI", "http://localhost:8989")
BASE_URL = "https://nclottery.com"
INDEX_URL = "https://nclottery.com/scratch-off"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:70.0) Gecko/20100101 Firefox/70.0",
}

h = html2text.HTML2Text()


def get_games(site_url):
    """
    Takes the URL from the scratcher site

    Returns a list game urls
    """
    html = requests.get(site_url, headers=HEADERS).text
    soup = bs(html, "html.parser")

    game_info_soup = soup.find_all("h5", class_="title")

    game_urls = [game.find("a")["href"] for game in game_info_soup]

    return game_urls


def process_game(game_url):
    """
    Takes game url. Makes request.


    """
    html = requests.get(f"{BASE_URL}{game_url}").text
    soup = bs(html, "html.parser")

    print("game_url==", game_url)
    game_url_split = game_url.split("/")
    
    game_id = game_url_split[2]

    name = game_url_split[3]

    how_to_play = soup.find("h3").find_next("p").text

    # info_table {"", 'ticket price', '$price, 'top prize', odds, launch date, game number}

    info_table = soup.find("table", class_="juxtable details").find_all("td")

    price = int(info_table[2].text.replace("$", ""))

    odds = float(re.search(r"\d+.\d+", info_table[6].text).group(0))

    image_url = f"{BASE_URL}{soup.find('div', class_='box TicketImg').find_next('img')['src']}"

    prizes = [
        {
            "prize": elm[0].text.strip(),
            "value": int(elm[0].text.strip().replace('$','').replace(',','')),
            "claimed": int(elm[2].text.strip().replace(',',''))-int(elm[3].text.strip().replace(',','')),
            "available": int(elm[3].text.strip().replace(',',''))
        }
        for elm in [
            row.find_all("td")
            for row in soup.find("table", class_="datatable prizes").find_all("tr")[2:]
        ]
    ]

    num_of_tix = int(sum(row["claimed"] + row["available"] for row in prizes) * odds)

    game = {
        "name": name,
        "game_id": game_id,
        "how_to_play": how_to_play,
        "price": price,
        "prizes": prizes,
        "image_urls": [image_url],
        "num_tx_initial": num_of_tix
    }

    return game


def main():
    game_urls = get_games(INDEX_URL)
    games = []
    for game_url in game_urls:
        try:
            game = process_game(game_url)
        except Exception as e:
            logger.warning("temp message")
            logger.warning(e)
            traceback.print_exception(e)
            logger.warning(f"Unable to process game:{game_url}")
        games.append(game)
    return games


if __name__ == "__main__":
    games = main()
    schema = GameSchema(many=True)
    print(schema.dumps(games))
