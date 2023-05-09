import unittest
import requests

from lottery_data_scraper import idaho
from lottery_data_scraper import schemas

class TestIdaho(unittest.TestCase):
    def test_parse_game_html(self):
        # URL chosen arbitrarily
        url = "https://www.idaholottery.com/games/scratch/lucky-rooster-bingo"
        game = idaho.parse_game(url)
        self.assertEqual(game['name'], "Lucky Rooster Bingo")
        self.assertEqual(game["price"], 10)
        self.assertEqual(game["game_id"], "1716")
        self.assertEqual(game["prizes"][0]["prize"], "$100,000")
        self.assertEqual(game["prizes"][0]["value"], 100000)
        self.assertEqual(game["num_tx_initial"], 339900)
