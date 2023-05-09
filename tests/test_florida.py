import unittest
import requests

from lottery_data_scraper import florida
from lottery_data_scraper import schemas

class TestFlorida(unittest.TestCase):
    def test_parse_game_html(self):
        # URL chosen arbitrarily
        url = "https://flalottery.com/scratch-offsGameDetails?gameNumber=7025"
        game = florida.parse_game(url)
        self.assertEqual(game['name'], "MYSTERY MULTIPLIER")
        self.assertEqual(game["price"], 10)
        self.assertEqual(game["num_tx_initial"], 20513700)
        self.assertEqual(game["game_id"], "7025")
        self.assertEqual(game["prizes"][0]["prize"], "$1,000,000.00")
        self.assertEqual(game["prizes"][0]["value"], 1000000)