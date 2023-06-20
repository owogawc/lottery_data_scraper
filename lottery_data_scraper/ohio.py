import logging
import os
import re
import traceback
from selenium import webdriver
from datetime import datetime, date


from bs4 import BeautifulSoup as bs
import html2text
import requests
import json

from lottery_data_scraper.util import fetch_html
from lottery_data_scraper.schemas import GameSchema

logger = logging.getLogger(__name__)
h = html2text.HTML2Text()

BASE_URL = 'https://www.ohiolottery.com'
INDEX_URL = 'https://www.ohiolottery.com/Games/ScratchOffs'

# Missing initial number of tickets per prize!

def get_games(site_url):
    html = fetch_html(site_url)
    soup = bs(html, "lxml")
    
    game_urls = [f"{BASE_URL}{game_soup.find('a')['href']}" for game_soup in soup.find_all('li', class_='igLandListItem')] 
    return game_urls

def process_game(game_url):
    html = fetch_html(game_url)
    soup = bs(html, "lxml")

    name = soup.find('h1').text.strip()

    game_id = re.search(r"\d+", soup.find('span', class_="number").text).group(0)

    price = int(re.search(r"\$(\d+)", game_url).group(1))


    game = {
        "name": name,
        "game_id": game_id,
        "price": price,
        # "how_to_play": how_to_play,
        # "prizes": prizes,
        # "num_tx_initial": num_of_tix,
        # "state": "nm",
        # "image_urls": f'["{image_url}"]',
    }

    print(game)


def main():
    game_urls = get_games(INDEX_URL)
    games = []

    for game in game_urls[:1]:
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