import json
import subprocess
import unittest


class TestCalifornia(unittest.TestCase):
    def test_all(self):
        result = subprocess.run(
            ["python3", "-m", "lottery_data_scraper.california"], capture_output=True
        )
        data = json.loads(result.stdout)
        self.assertEqual(
            data[0]["game_id"], "1405", "Expected the first game to be PAC-MAN, #1405."
        )
        self.assertEqual(
            data[0]["num_tx_initial"],
            37080000,
            "Expected 37,080,000 tickets for PAC-MAN #1405.",
        )
