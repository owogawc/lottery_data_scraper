import logging
import re

from bs4 import BeautifulSoup as bs
import requests
from lottery_data_scraper.schemas import GameSchema
from lottery_data_scraper.util import fetch_html

# from lotto_site_parsers.util import save_image

logger = logging.getLogger(__name__)

BASE_URL = "http://www.molottery.com"
INDEX_URL = "http://www.molottery.com/scratchers.do"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:70.0) Gecko/20100101 Firefox/70.0",
}

def process_game(url):
    """
    takes a url

    parses html text for game info

    saves game data to database
    """

    html = requests.get(url, headers=HEADERS).text

    # soup is the HTML from the page
    soup = bs(html, "html5lib")

    # name = title of game
    name = soup.find("h1").text.strip()

    game_id = (
        soup.find("div", class_="scratchers-single__id").text.split("Game #")[1].strip()
    )

    price = float(
        soup.find(
            string=re.compile("Ticket Price:")
        ).parent.next_sibling.next_sibling.text.replace("$", "")
    )

    image_url_fetched = soup.find("div", class_="scratchers-single__right").find_next(
        "img"
    )["src"]
    image_url = f"{BASE_URL}{image_url_fetched}"

    image_location = save_image("mo", game_id, image_url, headers=HEADERS)

    how_to_play_unedited = soup.find(
        "div", class_="scratchers-single__text"
    ).text.strip()
    how_to_play = re.sub(r"(?m)^\W+", "", how_to_play_unedited)

    odds = float(
        re.search(
            r"1 in (\d+(\.\d+)?)",
            soup.find(
                string=re.compile("Average Chances\*:")
            ).parent.next_sibling.next_sibling.text,
        ).group(1)
    )

    prizes = [
        {
            "prize": row[0],
            "value": price
            if row[0] == "TICKET"
            else int(re.sub("[^\d\.]", "", row[0])),
            "claimed": int(row[1].replace(",", "")) - int(row[2].replace(",", "")),
            "available": int(row[2].replace(",", "")),
        }
        for row in [
            [cell.text.strip() for cell in row.find_all("td")]
            for row in soup.table.find_all("tr")[1:]
        ]
    ]

    num_tx_initial = int(odds * sum(p["available"] + p["claimed"] for p in prizes))

    game = {
        "name": name,
        "game_id": game_id,
        "price": price,
        "num_tx_initial": num_tx_initial,
        "how_to_play": how_to_play,
        "image_urls": '["{}"]'.format(image_location) if image_location else "[]",
        "url": url,
        "state": "mo",
        "prizes": prizes,
    }

    # save_game(game)  do something different with game, we're not saving it anymore
    return game


def main():
    games = []
    try:
        index_response = requests.get(INDEX_URL, headers=HEADERS)
        index_soup = bs(index_response.text, "html.parser")
        game_urls = [
            BASE_URL + el.attrs["href"]
            for el in index_soup.find_all("a", text=re.compile(r"Game Details"))
        ]
    except Exception as e:
        logger.error("Unable to fetch MO index.\n{}".format(e))
        exit(1)

    for url in game_urls:
        try:
            game = process_game(url)
            games.append(game)
        except Exception as e:
            logger.warning("Unable to process game {}.\n{}".format(url, e))
    
    return games


if __name__ == "__main__":
    games = main()
    schema = GameSchema(many=True)
    print(schema.dumps(games))
