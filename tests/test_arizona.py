import unittest
import requests

from lottery_data_scraper import arizona
from lottery_data_scraper import schemas

class TestArizona(unittest.TestCase):
    def test_parse_game_html(self):
        # URL chosen arbitrarily -- first game returned in list
        url = 'https://www.arizonalottery.com/scratchers/1409-cash-drop/'
        game = arizona.process_game(url)
        self.assertEqual(game['name'], 'Cash Drop')
        self.assertEqual(game["price"], 2.0)
        self.assertEqual(game["game_id"], "1409")
        self.assertEqual(game["num_tx_initial"], 1820968)
        self.assertEqual(game["prizes"][0]["prize"], "10,000")
        self.assertEqual(game["prizes"][0]["value"], 10000)