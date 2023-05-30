import unittest
import requests

from lottery_data_scraper import new_york
from lottery_data_scraper import schemas

class TestNewYork(unittest.TestCase):
    def test_parse_game_html(self):
        # URL chosen arbitrarily
        url = "https://nylottery.ny.gov/drupal-api/api/v2/scratch_off_data?_format=json"
        game_info = new_york.get_games(url)
        game = new_york.process_game(game_info[0])
        self.assertEqual(game['name'], "CASH X20 BINGO")
        self.assertEqual(game["price"], 5.0)
        self.assertEqual(game["game_id"], "1572")
        self.assertEqual(game["prizes"][0]["prize"], "$300,000")
        self.assertEqual(game["prizes"][0]["value"], 300000)
        self.assertEqual(game["num_tx_initial"], 12341684)