import unittest
import requests

from lottery_data_scraper import arkansas
from lottery_data_scraper import schemas

class TestArkansas(unittest.TestCase):
    def test_parse_game_html(self):
        # URL chosen arbitrarily -- first game returned in list
        url = 'https://www.myarkansaslottery.com/games/200000-jackpot-1'
        html = arkansas.fetch_html(url)
        game = arkansas.parse_game(url, html)
        self.assertEqual(game['name'], '$200,000 Jackpot')
        self.assertEqual(game["price"], 10)
        self.assertEqual(game["game_id"], "732")
        self.assertEqual(game["num_tx_initial"], 1132310)
        self.assertEqual(game["prizes"][0]["prize"], "200,000")
        self.assertEqual(game["prizes"][0]["value"], 200000)