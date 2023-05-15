import unittest
import requests

from lottery_data_scraper import new_jersey
from lottery_data_scraper import schemas

GAMES_URL = (
    "https://www.njlottery.com" "/api/v1/instant-games/games/?size=1000&_=1537671212230"
)


class TestNewJersey(unittest.TestCase):
    # TODO: figure out a way to check specific games
    def test_parse_game_html(self):
        games = new_jersey.fetch_games(GAMES_URL)
        game = new_jersey.parse_game(games[0])
        self.assertIs(type(game['name']), str)
        self.assertIs(type(game["price"]), float)
        self.assertIs(type(game['game_id']), str)
        self.assertIs(type(game['num_tx_initial']), int)
        self.assertIs(type(game["prizes"][0]["prize"]), str)
        self.assertIs(type(game["prizes"][0]["value"]), float)
    


