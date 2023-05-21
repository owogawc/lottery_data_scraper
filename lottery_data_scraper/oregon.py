import logging
import os
import re
import traceback
from selenium import webdriver
from datetime import datetime, date


from bs4 import BeautifulSoup as bs
import requests
import json

from lottery_data_scraper.util import fetch_html
from lottery_data_scraper.schemas import GameSchema

logger = logging.getLogger(__name__)

# TODO: add a length value to check the number of urls being returned

BASE_URL = "https://www.oregonlottery.org"
INDEX_URL = "https://www.oregonlottery.org/scratch-its/grid/"

API_URL = "https://api2.oregonlottery.org/instant/GetAll"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:70.0) Gecko/20100101 Firefox/70.0",
}
SINGLE_GAME_API_URL = (
    "https://api2.oregonlottery.org/instant/GetGame?includePrizeTiers=true&gameNumber="
)
SINGLE_GAME_URL = "https://www.oregonlottery.org/scratch-its/"


# Oregon uses API to store game data
# API requires api key for access
def get_api_key(site_url):
    response = requests.get(site_url, headers=HEADERS).text
    api_key = re.search(r"\"apikey\":\"(.+)\"", response).group(1)

    return api_key


api_headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:70.0) Gecko/20100101 Firefox/70.0",
    "Ocp-Apim-Subscription-Key": get_api_key(INDEX_URL),
}


def get_api_game_list(api_url):
    """
    Makes a call to the game api, with retrieved api key

    retrieves a list of game data
        {
            ["GameNumber", "1",
            "GameNameTitle": "Game's Name",
            "TicketPrice": float,
            "DateAvalailable": "Date_Time_Format",
            "GameEndDate": "Date_Time_Format",
            "ValidationEndDate": "Date_Time_Format" ,
            "PlayStyle": "String",
            "OverallOdds": float,
            "TopPrize": float,
            "SellThroughRate": float,
            "SecondChancePrizeAmount": "",
            "SecondChanceDrawDate"" "Date_Time_Format",
            "TopPrizesRemaining": int], ...
        }
        Games name is turned into kebab case for use in URL

        returns a list of game info [[game_ID, 'game's_name', game end date]...]
    """
    response = requests.get(api_url, headers=api_headers).text
    games_json = json.loads(response)
    game_list = {}

    for game in games_json:
        game_list[game["GameNumber"]] = [
            game["GameEndDate"],
            game["GameNameTitle"].lower().replace(" ", "-"),
        ]

    return game_list

# did not work with firefox
def get_game_list(site_url):
    '''
    Using Selenium to run JavaScript
    '''
    options = webdriver.chrome.options.Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    driver.get(site_url)
    html = driver.page_source
    soup = bs(html, "lxml")

    games_soup = soup.find_all("div", class_="ol-grid-scratchits__game")

    game_urls = [game.find_next("a")["href"] for game in games_soup]

    return game_urls


def filter_games_by_expired(api_games_list):
    """
    Takes a list of games {game_ID: [game end date, 'game's-name',]...}

    game date formate = 'YYYY-MM-DDTHH:MM:SS'
    isoformat = 'YYYY-MM-DD'

    filters games based on Game End Date

    returns a lists of games that are dated older than the present day
    """

    today_date = str(date.today().isoformat())
    filtered_games = {}

    for key in api_games_list:
        if api_games_list[key][0] == None or datetime.strptime(
            api_games_list[key][0], "%Y-%m-%dT%H:%M:%S"
        ) >= datetime.strptime(today_date, "%Y-%m-%d"):
            filtered_games[key] = api_games_list[key]


    return filtered_games


def get_full_game_list():
    # list of urls
    games_list = get_game_list(INDEX_URL)
    # dictionary using game_id as key {gameId = [], ....}
    api_games_list = filter_games_by_expired(get_api_game_list(API_URL))

    final_games_list = []

    for game in games_list:
        html = fetch_html(game)
        soup = bs(html, "lxml")
        game_id = soup.find(
            "div", class_="ol-gamedata-scratchit ol-gamedata-scratchit--short"
        )["data-game"]
        if api_games_list.get(game_id):
            final_games_list.append([game_id, game, soup])
    
    return final_games_list


def process_game(game_info):
    """
    Takes game info [game_ID, game_url, game_soup]

    Retrieves api info
        {
            "DateAvailable": "Date_Time_Format",
            "GameNameTitle": "Game's Name",
            "GameNumber": "game_id",
            "OverallOdds": float,
            "PlayStyle": "string",
            "TicketPrice": int,
            "PrizeTiers" [{
                "Description": "float",
                "PrizeAmount": int,
                "TierLever": int,
                "Odds": float,
                "PrizesRemaining": int,
                "PrizesTotal": int,
                "PrizesWon" : int
                }]
        }

    Parses game info from json info

    Retrieves 'games image' and 'how to play' from game_soup

    Saves game to database
    """

    game_id = game_info[0]
    url = game_info[1]
    soup = game_info[2]
    game_api_info = json.loads(
        requests.get(f"{SINGLE_GAME_API_URL}{game_id}", headers=api_headers).text
    )

    game_name = game_api_info[0]["GameNameTitle"]

    price = game_api_info[0]["TicketPrice"]

    odds = game_api_info[0]["OverallOdds"]

    prizes = [
        {
            "prize": tier["Description"],
            "value": tier["PrizeAmount"],
            "claimed": tier["PrizesWon"],
            "available": tier["PrizesRemaining"],
            "total": tier["PrizesTotal"],
            "odds": tier["Odds"],
        }
        for tier in game_api_info[0]["PrizeTiers"]
    ]
    
    num_of_tix = int(float(odds) * sum(p["total"] for p in prizes))

    how_to_play = soup.find('div', class_='ol-typography')
    how_to_play.h2.decompose()
    how_to_play = how_to_play.text.strip()

    image_url_fetched = soup.find(
        "div", class_="ol-gamedata-scratchit__slide"
    ).find_next("img")["src"]
    image_url = f"{BASE_URL}{image_url_fetched}"

    game = {
        "name": game_name,
        "game_id": game_id,
        "url": url,
        "price": price,
        "prizes": prizes,
        "num_tx_initial": num_of_tix,
        "how_to_play": how_to_play,
        "state": "or",
        "image_urls": [image_url],
    }
    return game


def main():
    # [[game_id, game_url, game_soup], ...]
    games_list = get_full_game_list()

    games = []

    for game in games_list:
        try:
            game = process_game(game)
        except Exception as e:
            logger.warning(f"Unable to process game: {game[0]}-{game[1]}")
            logger.warning(e)
            traceback.print_exception(e)
        games.append(game)
    
    return games


if __name__ == "__main__":
    games = main()
    schema = GameSchema(many=True)
    print(schema.dumps(games))
