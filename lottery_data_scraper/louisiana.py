import logging
from bs4 import BeautifulSoup as bs
import pandas as pd
from lottery_data_scraper.schemas import GameSchema
from lottery_data_scraper.util import fetch_html

logger = logging.getLogger(__name__)

# It's worth assigning to constants values that are used in many
# places throughout a script.
BASE_URL = "http://www.louisianalottery.com"
INDEX_URL = "https://louisianalottery.com/scratch-offs/top-prizes-remaining"


def parse_index(html):
    soup = bs(html, "lxml")
    table = soup.find("table")
    game_hrefs = table.select("tr > td > a")
    game_urls = list(map(lambda x: "https:" + x.attrs["href"], game_hrefs))
    return game_urls


# TODO: convert pandas to beautiful soup
def parse_game(url, html):
    soup = bs(html, "lxml")
    price = soup.select('div[id="scratch-off-prize-info"] td')[1].text.replace("$", "")
    name = soup.find(class_="scratch-off-title").text
    num = url.split("/")[-2]
    grand_prize_row = soup.select(
        'div[id="scratch-off-table-tier"] table > tbody > tr'
    )[0]
    grand_prize_odds = float(
        grand_prize_row.select("td")[1]
        .text.split(" in ")[1]
        .replace(
            ",",
            "",
        )
    )
    grand_prize_num = int(grand_prize_row.select("td")[2].text)
    num_tx = int(grand_prize_odds * grand_prize_num)
    table = soup.find_all("table")[2]
    df = pd.read_html(str(table))[0]
    df = df.replace("TICKET", price)
    prizes = [
        {
            "prize": prize,
            "value": float(prize.replace("$", "").replace(",", "")),
            "claimed": int(claimed),
            "available": int(total) - int(claimed),
        }
        for prize, _, total, claimed in [list(r[1])[:4] for r in df.iterrows()]
    ]
    game = {
        "name": name,
        "game_id": num,
        "url": url,
        "state": "la",
        "price": float(price),
        "num_tx_initial": num_tx,
        "prizes": prizes,
    }
    return game


def main():
    index_html = fetch_html(INDEX_URL)
    game_urls = parse_index(index_html)
    url_htmls = zip(game_urls, [fetch_html(url) for url in game_urls])
    games = []
    for url, html in url_htmls:
        try:
            game = parse_game(url, html)
        except Exception as e:
            logger.error("Unable to parse {}.\n{}".format(url, e))
            continue
        games.append(game)
    return games


if __name__ == "__main__":
    games = main()
    schema = GameSchema(many=True)
    print(schema.dumps(games))
