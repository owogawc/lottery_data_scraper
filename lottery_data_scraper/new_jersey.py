import logging
import os
from xmlrpc import client
import ssl
from urllib3 import poolmanager

import requests
from requests import adapters

from lottery_data_scraper.schemas import GameSchema

logger = logging.getLogger(__name__)


BASE_URL = "https://www.njlottery.com"
INDEX_URL = "https://www.njlottery.com/en-us/instant-games.html#tab-active"
GAMES_URL = (
    "https://www.njlottery.com" "/api/v1/instant-games/games/?size=1000&_=1537671212230"
)
GAME_URL_FMT = "https://www.njlottery.com/en-us/scratch-offs/0{}.html"


class TLSAdapter(adapters.HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        """Create and initialize the urllib3 PoolManager."""
        ctx = ssl.create_default_context()
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        self.poolmanager = poolmanager.PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_version=ssl.PROTOCOL_TLS,
            ssl_context=ctx,
        )

    def close(self):
        """Disposes of any internal state.

        Currently, this closes the PoolManager.
        """
        self.poolmanager.clear()


def fetch_games(games_url):
    response = requests.get(games_url).json()
    return response["games"]


def parse_game(game_data):
    game = {
        "name": game_data["gameName"],
        "game_id": game_data["gameId"],
        "url": GAME_URL_FMT.format(game_data["gameId"]),
        "price": float(game_data["ticketPrice"] / 100),
        "state": "nj",
        "num_tx_initial": game_data["totalTicketsPrinted"],
        "prizes": [
            {
                "value": p["prizeAmount"] / 100,
                "prize": p["prizeDescription"],
                "available": (p["winningTickets"] - p["paidTickets"]),
                "claimed": p["paidTickets"],
            }
            for p in game_data["prizeTiers"]
        ],
    }

    return game


def main():
    games_data = fetch_games(GAMES_URL)
    games = [
        parse_game(game) for game in games_data if game["validationStatus"] == "ACTIVE"
    ]
    return games


if __name__ == "__main__":
    games = main()
    schema = GameSchema(many=True)
    print(schema.dumps(games))
