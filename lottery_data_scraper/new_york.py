import logging
import os
import re
import traceback


from bs4 import BeautifulSoup as bs
import requests
import json
import html2text

from lottery_data_scraper.util import fetch_html
from lottery_data_scraper.schemas import GameSchema

h = html2text.HTML2Text()
h.ignore_links = True

logger = logging.getLogger(__name__)

BASE_URL = "https://www.nylottery.ny.gov"
INDEX_URL = "https://nylottery.ny.gov/scratch-off-games"
GAME_URL = "https://nylottery.ny.gov/scratch-off-game?game="
API_URL = "https://nylottery.ny.gov/drupal-api/api/v2/scratch_off_data?_format=json"


def get_games(site_url):
    """
    Makes an API call to retrieve an array of list items of game data

    Returns {rows: [array of games]}

    """
    games = json.loads(requests.get(site_url).text)

    return games['rows']


# Some of the games pay out in installments and the top prize in the 
# nested table is expressed as the installment payment, not the lump sum
def value_format_check(prize_amount, game_data):
    if "Annual" in prize_amount or "LIFE" in prize_amount:
        prize_amount = game_data["top_prize_amount"]
    return prize_amount


def process_game(game_data):
    """
    Receives Game Info:
    {
        game_number: '####',
        how_to_play: [{
            steps:[{description:html string step by step instructions}], ...
            }]
        overall_odds: '1 in #'
        odds_prizes: [{
            prize_amount: string '$#,#', or '#K installments'
            prizes_paid_out: '#',
            prizes_remaining: '#',
            }, ...]
        ticket_price:: "#.##',
        title: "Title + whitespace"
        art: [{uri: 'image url'}]
    }
    """
    game_id = game_data["game_number"]
    name = game_data["title"].rstrip()
    game_url = f"{BASE_URL}?game={game_id}"
    price = float(game_data["ticket_price"])
    image_url = game_data["art"][0]["uri"]

    how_to_play_list = [
        game["description"] for game in game_data["how_to_play"][0]["steps"]
    ]
    how_to_play = "".join(how_to_play_list)

    prizes = [
        {
            "prize": game["prize_amount"],
            "value": int(
                value_format_check(game["prize_amount"], game_data)
                .replace("$", "")
                .replace(",", "")
            ),
            "available": int(game["prizes_remaining"]),
            "claimed": int(game["prizes_paid_out"]),
        }
        for game in game_data["odds_prizes"]
    ]

    # Capturing odds this way due to inconsistency of reporting on site:
    # some are "1 in #.##" while some are "1 in\t#.##"
    odds = float(re.search(r"\d+.\d+", game_data["overall_odds"]).group(0))
    num_of_tix = int(sum(row["available"] + row["claimed"] for row in prizes) * odds)

    game = {
        "game_id": game_id,
        "name": name,
        "url": game_url,
        "state": "ny",
        "how_to_play": h.handle(how_to_play),
        "price": price,
        "num_tx_initial": num_of_tix,
        "prizes": prizes,
        "image_urls": [image_url],
    }

    return game


def main():
    game_info = get_games(API_URL)
    games = []

    for game in game_info:
        try:
            processed_game = process_game(game)
        except Exception as e:
            logger.error(f"Unable to process game: {GAME_URL}{game['game_number']}")
            logger.warning(e)
            traceback.print_exception(e)
        games.append(processed_game)
    return games


if __name__ == "__main__":
    games = main()
    schema = GameSchema(many=True)
    print(schema.dumps(games))
