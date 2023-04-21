import logging
import os
import re
from xmlrpc import client
import traceback

from bs4 import BeautifulSoup as bs
import requests


from lotto_site_parsers.util import save_image
from lotto_site_parsers.util import save_game

logger = logging.getLogger(__name__)

DB_REPO_URI = os.environ.get("DB_REPO_URI", "http://localhost:8989")
BASE_URL = "https://www.nmlottery.com"
INDEX_URL = "https://www.nmlottery.com/games/scratchers"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:70.0) Gecko/20100101 Firefox/70.0",
}


def get_games(site_url):
    """
    Takes the URL from the scratcher site
    parses page for game ids and game info
    returns and list of tuples with the id and game info for each game
    """
    html = requests.get(site_url, headers=HEADERS).text
    soup = bs(html, "html.parser")

    games_html = soup.find_all("div", class_="filter-block")

    ids = [
        re.search("\d+", id.text).group(0)
        for id in soup.find_all("p", class_="game-number")
    ]

    game_names = [name.text for name in soup.find_all("h3")]

    return list(zip(ids, game_names, games_html))


def process_game(game_info):
    """
    function takes game info: [game id, game_name, game_html_data]

    parses info to find specific game data
    ex name, game_id, price, odds, prizes, how to play, image_url

    returns game object
    """

    game_html = game_info[2]

    name = game_info[1]

    game_id = game_info[0]

    price = float(game_html.find("p", class_="price").text.replace("$", ""))

    how_to_play = game_html.find("p", class_="how-to-play").find_next("span").text

    prizes = [
        {
            "prize": row[0].strip(),
            "value": price
            if "prize ticket" in row[0].lower()
            else float(row[0].replace("$", "").replace(",", "")),
            "claimed": int(row[2].replace(",", "")) - int(row[3].replace(",", "")),
            "available": int(row[3].replace(",", "")),
            "total": int(row[2].replace(",", "")),
            "odds": float(row[1].replace(",", "")),
        }
        for row in [
            row.text.split("\n")[1:-1] for row in game_html.table.find_all("tr")[1:]
        ]
    ]

    num_of_tix = int(prizes[0]["odds"] * prizes[0]["total"])

    image_url = game_html.find("div", class_="scratcher-image").find_next("img")["src"]
    image_location = save_image("nm", game_id, image_url, headers=HEADERS)

    game = {
        "name": name,
        "game_id": game_id,
        "price": price,
        "how_to_play": how_to_play,
        "prizes": prizes,
        "num_tx_initial": num_of_tix,
        "state": "nm",
        "image_urls": '["{}"]'.format(image_location),
    }

    return game


def main():
    games = get_games(INDEX_URL)
    for game in games:
        try:
            game = process_game(game)
            save_game(game)
        except Exception as e:
            logger.warning(f"Unable to process game: {game[0]}-{game[1]}")
            logger.warning(e)
            traceback.print_exception(e)


if __name__ == "__main__":
    main()
