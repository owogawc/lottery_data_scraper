import logging
from functools import partial
import os
import re

from bs4 import BeautifulSoup as bs
import html2text
import requests

from lottery_data_scraper.schemas import GameSchema
from lottery_data_scraper.util import fetch_html

logger = logging.getLogger(__name__)

BASE = "https://flalottery.com/"
INDEX = "https://flalottery.com/remainingPrizes"
h = html2text.HTML2Text()


def parse_game(url):
    html = fetch_html(url)
    soup = bs(html, 'lxml')

    title = soup.select("#scratch-offs > h1")[0].text
    uid, name = title[1:].split(" – ")

    details_content = soup.find("div", "ticketDetailsContent")

    how_to_play = h.handle(str(details_content.find_all("p")[1]))

    price_paragraph = details_content.find(
        string=re.compile(r"Ticket Price:")
    ).parent.parent
    price = float(re.search(r"\$(\d+\.\d+)", price_paragraph.text).group(1))
    table = soup.find("table", "scratchOdds").find("tbody")
    prize_rows = table.select("tr")

    # Some FL tickets are $X/Year for life.
    # "Life" in Florida is 20 years.
    def get_value(prize):
        if re.search(r"(Year|Yr)", prize, re.IGNORECASE):
            return float(re.sub(r'[^\d\.]', '', prize)) * 20
        elif re.search(r"(Week|Wk)", prize, re.IGNORECASE):
            return float(re.sub(r'[^\d\.]', '', prize)) * 52 * 20
        else:
            return float(re.sub(r'[^\d\.]', '', prize))

    prizes = [
        {
            "prize": row[0].text,
            "value": get_value(row[0].text),
            "available": int(row[3].text.replace(",", "")),
            "claimed": int(row[2].text.replace(",", "")) - int(row[3].text.replace(",", "")),
        }
        for row in [row.find_all("td") for row in prize_rows]
    ]
    top_prize_odds = float(
        prize_rows[0].find_all("td")[1].text.split("-in-")[1].replace(",", "")
    )
    num_tx_initial = (prizes[0]["available"] + prizes[0]["claimed"]) * top_prize_odds
    image_url = soup.find("img", "ticketPicture").attrs["src"]
    
    game = {
        "name": name,
        "game_id": uid,
        "how_to_play": how_to_play,
        "price": price,
        "state": "fl",
        "num_tx_initial": num_tx_initial,
        "image_urls": [image_url],
        "url": url,
        "prizes": prizes,
    }
    return game


def main():
    index = fetch_html(INDEX)
    soup = bs(index, "lxml")
    game_urls = [BASE + t["href"] for t in soup.select(".gameNameLink > a")]
    games = []

    for url in game_urls:
        try:
            game = parse_game(url)
        except Exception as e:
            logger.error("Unable to process {}.\n{}".format(url, e))
        games.append(game)
    return games

if __name__ == "__main__":
    games = main()
    schema = GameSchema(many=True)
    print(schema.dumps(games))
