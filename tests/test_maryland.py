import unittest
import requests

from lottery_data_scraper import maryland
from lottery_data_scraper import schemas

s = requests.Session()

class TestMaryland(unittest.TestCase):
    # TODO: figure out a way to check specific games
    def test_parse_game_html(self):
        url = "https://www.mdlottery.com/wp-admin/admin-ajax.php?action=jquery_shortcode&shortcode=scratch_offs"
        game = maryland.games(s, url)
        self.assertIs(type(game[0]['name']), str)
        self.assertIs(type(game[0]["price"]), int)
        self.assertIs(type(game[0]['game_id']), str)
        self.assertIs(type(game[0]['num_tx_initial']), int)
        self.assertIs(type(game[0]["prizes"][0]["prize"]), str)
        self.assertIs(type(game[0]["prizes"][0]["value"]), float)
