import unittest
import requests

from lottery_data_scraper import texas
from lottery_data_scraper import schemas

class TestTexas(unittest.TestCase):
    def test_parse_game_html(self):
        # URL chosen arbitrarily
        url = "http://www.txlottery.org/export/sites/lottery/Games/Scratch_Offs/details.html_252701533.html"
        html = texas.fetch_html(url)
        game = texas._parse_game(url, html)
        self.assertEqual(game['name'], "$1,000,000 Cash Blowout")
        self.assertEqual(game["price"], 20.0)
        self.assertEqual(
            game["url"],
           'http://www.txlottery.org/export/sites/lottery/Games/Scratch_Offs/details.html_252701533.html' ,
        )
        self.assertEqual(game["game_id"], "2442")
        self.assertEqual(game["prizes"][0]["prize"], "$1,000,000")
        self.assertEqual(game["prizes"][0]["value"], 1000000.0)

