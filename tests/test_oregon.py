import unittest
import requests
from bs4 import BeautifulSoup as bs

from lottery_data_scraper import oregon
from lottery_data_scraper import schemas

class TestOregon(unittest.TestCase):
    def test_parse_game_html(self):
        # URL chosen arbitrarily -- first game returned in list
        url = 'https://www.oregonlottery.org//scratch-its/50-or-100/'
        html = oregon.fetch_html(url)
        soup = bs(html, 'lxml')
        game = oregon.process_game(['1482', url, soup])
        self.assertEqual(game['name'], "$50 or $100")
        self.assertEqual(game["price"], 10.0)
        self.assertEqual(game["game_id"], "1482")
        self.assertEqual(game["num_tx_initial"], 278019)
        self.assertEqual(game["prizes"][0]["prize"], "50.00")
        self.assertEqual(game["prizes"][0]["value"], 50.0)