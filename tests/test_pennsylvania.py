import unittest

from lottery_data_scraper import pennsylvania
from lottery_data_scraper import schemas


class TestPennsylvania(unittest.TestCase):
    def test_parse_game_html(self):
        # URL chosen arbitrarily
        url = "https://www.palottery.state.pa.us/Scratch-Offs/View-Scratch-Off.aspx?id=3201"
        html = pennsylvania.fetch_html(url)
        game = pennsylvania.parse_game_html("$3 Million Mega Stacks", url, html)
        self.assertEqual(game["name"], "$3 Million Mega Stacks")
        self.assertEqual(game["price"], 30)
        self.assertEqual(
            game["url"],
            "https://www.palottery.state.pa.us/Scratch-Offs/View-Scratch-Off.aspx?id=3201",
        )
        self.assertEqual(game["game_id"], "3201")
        self.assertEqual(game["prizes"][0]["prize"], "$3,000,000.00")
        # Perhaps unfortunately in dollars. Cents would be better, eh?
        self.assertEqual(game["prizes"][0]["value"], 3000000)
