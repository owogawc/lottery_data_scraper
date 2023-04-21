import unittest
import requests

from lottery_data_scraper import louisiana
from lottery_data_scraper import schemas

class TestLouisiana(unittest.TestCase):
    def test_parse_game_html(self):
        # URL chosen arbitrarily
        url = 'https://louisianalottery.com/scratch-offs/1450/blazing-suits'
        html = louisiana.fetch_html(url)
        game = louisiana.parse_game(url, html)
        self.assertEqual(game['name'], 'Blazing Suits')
        self.assertEqual(game["price"], 10.0)
        self.assertEqual(
            game["url"],
           'https://louisianalottery.com/scratch-offs/1450/blazing-suits' ,
        )
        self.assertEqual(game["game_id"], "1450")
        self.assertEqual(game["prizes"][0]["prize"], "$200,000")
        self.assertEqual(game["prizes"][0]["value"], 200000.0)
        