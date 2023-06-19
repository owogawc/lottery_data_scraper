import logging
import os
import re
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import json

from bs4 import BeautifulSoup as bs
from lottery_data_scraper.schemas import GameSchema
from lottery_data_scraper.util import fetch_html

logger = logging.getLogger(__name__)

BASE_URL = "https://www.masslottery.com"
INDEX_URL = "https://www.masslottery.com/games/draw-and-instants"
API_URL = "https://www.masslottery.com/api/v1/games"

#Got almost every game working. Will come back.  


def get_game_urls(url):
    api_response = json.loads(requests.get(API_URL).text)

    game_urls_ids = [
        [f'{INDEX_URL}/{game["identifier"]}', game['id']]
        for game in api_response
        if game["gameType"] == "Scratch"
    ]

    return game_urls_ids


def process_game(game_url_id):
    """
    Using Selenium to run JavaScript
    """
    options = webdriver.chrome.options.Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    driver.get(game_url_id[0])
    try:
        elem = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "h3"))
        )
    except Exception as e:
        logger.warning(e)
        traceback.print_exception(e)
    
    html = driver.page_source
    soup = bs(html, "lxml")

    # game title
    if soup.find('h3').text:
        name = soup.find("h3").text
    else:
        name = soup.find("h3").textContent
    print(name)

    game_id = game_url_id[1]

    how_to_play = ""
    for elm in soup.find("div", class_="cms-text").find_all("p")[3:]:
        how_to_play += f"{elm.string} "

    price = float((soup.find("div", class_="scratch-game-detail-card-price-text").text).replace("$",""))

    image_url = f'https:{soup.find("div", class_= "cms-text").find_next("img")["src"]}'

    prizes = [
        {
            "prize": row_array.find(
                "p", class_="game-prizes-remaining-prize-value"
            ).text.strip(),
            "value": (
                row_array.find("p", class_="game-prizes-remaining-prize-value").text
            )
            .replace("$", "")
            .replace(",", ""),
            "available": int(
                re.search(
                    "\d*",
                    (
                        row_array.find(
                            "p", class_="game-prizes-remaining-remaining"
                        ).text
                    ).replace(",", ""),
                ).group(0)
            ),
            "claimed": int(
                re.search(
                    "\d*",
                    (
                        row_array.find(
                            "p", class_="game-prizes-remaining-claimed"
                        ).text
                    ).replace(",", ""),
                ).group(0)
            )
        }
        for row_array in soup.find_all("tr")[1:]
    ]

    odds = float(re.search(r"\d+.\d+", soup.find('div', class_='game-prizes-remaining-odds').text).group(0))

    num_of_tix = int(sum(row["available"] + row["claimed"] for row in prizes) * odds)

    game = {
        "name": name,
        "game_id": game_id,
        "url": game_url_id[0],
        "state": "ma",
        "how_to_play": how_to_play,
        "price": price,
        "prizes": prizes,
        "num_of_tix_initial":num_of_tix,
        "image_urls": [image_url],
    }

    # One off game situations
    for tier in game['prizes']:
        if 'million' in tier['prize'].lower():
            value = int(tier['prize'].split(' ')[0])
            tier['value'] = value * 1000000
        if 'a month for 10 years' in tier['prize'].lower():
            value = float(tier['prize'].split(' a')[0].replace('$', '').replace(',',''))
            tier['value'] = value * 12 * 10
        if '/YR/20YRS' in tier['prize']:
            value = float(tier['prize'].split(' ')[0].replace('$','').replace(',',''))
            tier['value'] = value
        else:
            tier['value'] = float(tier['value'])

    return game


def main():
    game_urls_ids = get_game_urls(API_URL)
    games = []

    for game in game_urls_ids:
        try:
            processed_game = process_game(game)
        except Exception as e:
            logger.error(f"Unable to process game: {game}")
            logger.warning(e)
            traceback.print_exception(e)
        games.append(processed_game)
    return games


if __name__ == "__main__":
    games = main()
    schema = GameSchema(many=True)
    print(schema.dumps(games))
