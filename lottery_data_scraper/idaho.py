import logging
import re

from bs4 import BeautifulSoup as bs
import html2text

from lottery_data_scraper.schemas import GameSchema 
from lottery_data_scraper.util import fetch_html

logger = logging.getLogger(__name__)

h = html2text.HTML2Text()
h.ignore_links = True

BASE = "https://www.idaholottery.com"
INDEX = "https://www.idaholottery.com/games/scratch"

def get_games(url):
    html = fetch_html(url)
    soup = bs(html, "lxml")
    game_urls = [BASE + n.attrs["href"] for n in soup.select(".game__inner a.image-link")]

    return game_urls

def parse_game(url):
    game_html = fetch_html(url)
    game_soup = bs(game_html, "lxml")

    name = game_soup.select(".section-game h5")[0].text

    image_url = game_soup.select(".section__image-holder img")[0].attrs["src"]

    game_id = image_url.split("/")[-1].split("_")[0]
   
    how_to_play = h.handle(str(game_soup.find(id="tab2")))

    price_str = game_soup.select(".list-badgets h4")[1].text
    price = float(price_str.replace("$", ""))

    table = game_soup.find(class_="full-rules-and-odds")
    rows_soup = table.tbody.find_all("tr")
    grand_prize_soup = rows_soup[0]
    total, prize, remaining, odds, _ = map(
        lambda x: x.text.strip(), grand_prize_soup.find_all("td")
    )
    
    odds = int(odds.replace("1:", ""))

    num_tx_initial = odds * int(total)
    
    most_recent_percent_remaining = 1

    prizes = []
    for total, prize, remaining, odds, _ in [
        map(lambda x: x.text.strip(), row.find_all("td")) for row in rows_soup
    ]:
        # Their data is dirty. Here are some hacks to try and fix it.
        # Sometimes, the total is missing.
        # Try to guess it.
        try:
            total = int(total)
        except ValueError:
            total = int(int(remaining) / most_recent_percent_remaining)

        value = float(prize.replace("$", "").replace(",", ""))

        try:
            remaining = int(remaining)
            # Sometimes, the total is less than the remaining.
            if total < remaining:
                total = int(remaining / most_recent_percent_remaining)
            most_recent_percent_remaining = remaining / total
        except ValueError:
            remaining = int(total * most_recent_percent_remaining)

        # There is a typo in the $1 prize of $5x the cash.
        if prize == "$1" and re.search(r"(?i)5x the cash", name):
            total = 276000  # num tx / odds
            remaining = total * most_recent_percent_remaining

        prizes.append(
            {
                "prize": prize,
                "available": remaining,
                "claimed": total - remaining,
                "value": value,
            }
        )
   
    game = {
        "name": name,
        "url": url,
        "image_urls": [image_url],
        "state": "id",
        "game_id": game_id,
        "how_to_play": how_to_play,
        "price": price,
        "num_tx_initial": num_tx_initial,
        "prizes": prizes
    }
    
    return game

def main():
    game_urls = get_games(INDEX)
    games = []
    for url in game_urls:
        try:
            game = parse_game(url)
        except Exception as e:
            logger.error("Unable to parse {}.\n{}".format(url, e))
        games.append(game)
    return games

if __name__ == "__main__":
    games = main()
    schema = GameSchema(many=True)
    print(schema.dumps(games))

