import unittest
import requests

from lottery_data_scraper import new_mexico
from lottery_data_scraper import schemas

class TestNewMexico(unittest.TestCase):
    def test_parse_game_html(self):
        # URL chosen arbitrarily
        url = "https://www.nmlottery.com/games/scratchers"
        html = new_mexico.fetch_html(url)
        game = new_mexico.get_games(url)[0]
        game = new_mexico.process_game(game)
        self.assertEqual(game["name"], "Match 3 Tripler")
        self.assertEqual(game["price"], 1)
        self.assertEqual(game["game_id"], "521")
        self.assertEqual(game["prizes"][0]["prize"], "$900")
        # Perhaps unfortunately in dollars. Cents would be better, eh?
        self.assertEqual(game["prizes"][0]["value"], 900)
        self.assertEqual(game["num_tx_initial"], 670800)
