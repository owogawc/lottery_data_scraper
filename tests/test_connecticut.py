import unittest
import requests

from lottery_data_scraper import connecticut
from lottery_data_scraper import schemas

class TestConnecticut(unittest.TestCase):
    def test_parse_game_html(self):
        # URL chosen arbitrarily
        url = 'https://www.ctlottery.org/ScratchGames/1740/'
        game = connecticut.parse_game(url)
        self.assertEqual(game['name'], 'Extreme Green')
        self.assertEqual(game["price"], 10)
        self.assertEqual(game["game_id"], "1740")
        self.assertEqual(game["prizes"][0]["prize"], "$100,000")
        self.assertEqual(game["prizes"][0]["value"], 100000)
        self.assertEqual(game["num_tx_initial"], 2230800)