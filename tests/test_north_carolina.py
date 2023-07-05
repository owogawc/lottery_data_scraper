import unittest
import requests

from lottery_data_scraper import north_carolina
from lottery_data_scraper import schemas

class TestNorthCarolina(unittest.TestCase):
    def test_parse_game_html(self):
        # URL chosen arbitrarily
        game_url = "/scratch-off/892/black-titanium"
        game = north_carolina.process_game(game_url)
        self.assertEqual(game['name'], "Black titanium")
        self.assertEqual(game["price"], 30)
        self.assertEqual(game["game_id"], "892")
        self.assertEqual(game["prizes"][0]["prize"], "$4,000,000")
        self.assertEqual(game["prizes"][0]["value"], 4000000)
        self.assertEqual(game["num_tx_initial"], 11899738)
