import logging
import os
import re
from xmlrpc import client

from bs4 import BeautifulSoup as bs
import pandas as pd
import requests
from lottery_data_scraper.schemas import GameSchema 
from lottery_data_scraper.util import fetch_html

logger = logging.getLogger(__name__)

BASE_URL = "https://www.myarkansaslottery.com"
INDEX_URL = "https://www.myarkansaslottery.com/games/instant?amount=All"


def game_urls():
    index = requests.get(INDEX_URL).text
    soup = bs(index, "lxml")
    page_hrefs = soup.find_all("a", title=re.compile("Go to page"))
    page_links = [BASE_URL + l.attrs["href"] for l in page_hrefs]
    page_htmls = [index] + [requests.get(page_link).text for page_link in page_links]
    game_links = []
    for page_html in page_htmls:
        page_soup = bs(page_html, "lxml")
        game_hrefs = page_soup.select(
            'article[class~="node-instant-game"] \
            div[class~="field-name-title-field"] a'
        )
        game_links += [BASE_URL + l.attrs["href"] for l in game_hrefs]
    return game_links


def num_tickets(soup):
    els = soup.select('[data-cell-title="Total Prizes:"]')
    num_winning_tx = sum(map(lambda x: int(x.text.replace(",", "")), els))
    odds = float(
        soup.find(class_="field-name-field-game-odds").text.split(" in ")[1].strip()
    )
    return num_winning_tx * odds


def parse_game(url, html):
    logger.debug(f"Parsing {url}")
    soup = bs(html, "lxml")
    price = soup.find(class_="field-name-field-ticket-price").text.split("$")[1].strip()
    name = soup.find("div", class_="field-name-title-field").text.strip()
    num = soup.find(class_="field-name-field-game-number").text.split("No.")[1].strip()
    num_tx = int(num_tickets(soup))
    table = soup.find("table")
    df = pd.read_html(str(table))[0]
    df.iloc[:, 0] = df.iloc[:, 0].str.replace("$", "")
    prizes = [
        {
            "prize": prize,
            "value": float(prize.replace(",", "")),
            "claimed": int(claimed),
            "available": int(total) - int(claimed),
        }
        for prize, total, claimed in [
            [r[1][0], r[1][1], r[1][1] - r[1][2]] for r in df.iterrows()
        ]
    ]

    game = {
        "name": name,
        "game_id": num,
        "url": url,
        "state": "ar",
        "price": float(price),
        "num_tx_initial": num_tx,
        "prizes": prizes,
    }
    return game


def main():
    urls = game_urls()
    url_htmls = zip(urls, [fetch_html(url) for url in urls])
    games = []
    for url, html in url_htmls:
        try:
            game = parse_game(url, html)
        except Exception as e:
            logger.error("Unable to parse {}.\n>{}".format(url, e))
            continue
        games.append(game)
    return games




if __name__ == "__main__":
    games = main()
    schema = GameSchema(many=True)
    print(schema.dumps(games))