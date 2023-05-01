import locale
import logging
import json
import operator
import html2text

from lottery_data_scraper.schemas import GameSchema
from lottery_data_scraper.util import fetch_html

# Set local for currency conversion and formatting
# because California only gives prize values and our schema
# expects a string representation of the prize.
# https://docs.python.org/3/library/locale.html
locale.setlocale(locale.LC_ALL, "en_US.utf8")

logger = logging.getLogger(__name__)
h = html2text.HTML2Text()

BASE_URL = "https://www.calottery.com"
SCRATCHER_URL = "https://www.calottery.com/api/games/scratchers"


def num_tx_initial(game):
    grand_prize = game["topPrizeTier"]
    return grand_prize["odds"] * grand_prize["totalNumberOfPrizes"]


def fetch_games():
    response = json.loads(fetch_html(SCRATCHER_URL))
    games = []
    for game_ in response["games"]:
        prizes = []
        for prize_ in game_["prizeTiers"]:
            prize = {
                "available": prize_["numberOfPrizesPending"],
                "claimed": prize_["numberOfPrizesCashed"],
                "value": prize_["value"],
                "prize": locale.currency(prize_["value"], grouping=True)[
                    :-3
                ],  # -3 to drop the cents
            }
            prizes.append(prize)
        grand_prize = sorted(game_["prizeTiers"], key=operator.itemgetter("value"))[-1]
        game = {
            "game_id": game_["gameNumber"],
            "name": game_["name"],
            "desription": h.handle(game_["description"]),
            "image_urls": [game_["unScratchedImage"], game_["scratchedImage"]],
            "how_to_play": h.handle(game_["howToPlay"]),
            "num_tx_initial": num_tx_initial(game_),
            "price": game_["price"],
            "prizes": prizes,
            "state": "tx",
            "url": BASE_URL + game_["productPage"],
        }
        games.append(game)
    return games


if __name__ == "__main__":
    games = fetch_games()
    schema = GameSchema(many=True)
    print(schema.dumps(games))
