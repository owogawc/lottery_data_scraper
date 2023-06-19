import unittest

from lottery_data_scraper import massachusetts
from lottery_data_scraper import schemas

class TestMassachusetts(unittest.TestCase):
    def test_parse_game_html(self):
        # URL chosen arbitrarily
        url = 'https://www.masslottery.com/games/draw-and-instants/5000000-100x-cashword-2023'
        game = massachusetts.process_game([url, '382'])
        self.assertEqual(game['name'], '$5,000,000 100X CASHWORD')
        self.assertEqual(game["price"], 20.0)
        self.assertEqual(game["game_id"], "382")
        self.assertEqual(game["prizes"][0]["prize"], "$5,000,000 ($250K/YR/20YRS)")
        self.assertEqual(game["prizes"][0]["value"], 5000000.0)