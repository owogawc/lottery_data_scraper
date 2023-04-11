"""
Scrapes the Pennsylvania lottery website for scratch-off ticket
data and calculates the expected value for each game.

Pennsylvania publishes the number of tickets printed and how many
tickets are printed at each prize level.

We can calculated the expected value of a game by summing
the value of all the prizes and dividing that by the cost
of all the tickets.

The palottery website has an "index" page that has links to every game.
Each individual game has a link to a "game rules" page.
We can start at the index and visit every game rules page, then we
can find the html table on that page which has the detailed prize
information and run our calculations.

Website that we'll be scraping:
https://www.palottery.state.pa.us/Scratch-Offs/Active-Games.aspx

Example usage:
    python -m pennsylvania
Or:
    LOGLEVEL=DEBUG USE_CACHE=True python -m pennsylvania

The following behavior is configurable through shell environment variables.

Set LOGLEVEL to print useful debug info to console.
LOGLEVEL=[DEBUG,INFO,WARNING,ERROR,CRITICAL]
Defaults to WARNING.

Set USE_CACHE to cache responses. This speeds up development
and is nice to the servers we're hitting.
USE_CACHE=[True]
Defaults to False. Note: Setting this env variable to the string False
will cause it to use cache because the string "False" evaluates to Truthy.
Either set it to True or don't set it.
"""
import base64
import sys
import traceback
from copy import deepcopy
import locale
import logging
import os
import re
from tempfile import gettempdir
from bs4 import BeautifulSoup as bs
import requests
from lottery_data_scraper.schemas import GameSchema
from lottery_data_scraper.util import fetch_html

logger = logging.getLogger(__name__)
locale.setlocale(locale.LC_MONETARY, "en_US.UTF-8")

# It's worth assigning to constants values that are used in many
# places throughout a script.
BASE_URL = "https://www.palottery.state.pa.us"
INDEX_URL = f"{BASE_URL}/Scratch-Offs/Active-Games.aspx"


def find_game_names(html):
    """
    Game names can be found on the index page
    in the text of anchor elements
    which have the class "activeGame_li".
    """
    soup = bs(html, "lxml")
    game_elements = soup.find_all("a", class_="activeGame_li")
    return [
        re.sub(r"\s+", " ", g.find("div", class_="info").text) for g in game_elements
    ]


def find_game_urls(html):
    """
    Luckily, all of the Pennsylvania games are listed on a single html page.
    We don't have to mess around with any pagination and making multiple requests.

    The links are "href" attributes of anchor tags with the class "activeGame_li".
    """
    soup = bs(html, "lxml")
    game_elements = soup.find_all("a", class_="activeGame_li")
    return ["{}{}".format(BASE_URL, e.attrs["href"]) for e in game_elements]


def find_complete_game_rules_url(html):
    """
    Game pages have a link to the complete game rules.
    The complete game rules have a table of all prizes for a game.

    The link to the game rules page is in an anchor tag
    nested under a div with the class "instant-games-games-info".
    """
    soup = bs(html, "lxml")
    games_info_div = soup.find("div", class_="instant-games-games-info")
    games_info_anchor = games_info_div.find_all("a")[1]
    games_info_url = games_info_anchor.attrs["href"]
    return games_info_url


def find_rows(html):
    """
    From a game rules page, find the rows of the table
    that have the number of tickets and the value of each prize.
    """
    soup = bs(html, "lxml")

    # Some game rules pages have multiple tables.
    # The first table has the prizes.
    # soup.find returns the first matching element
    # soup.find_all returns a list of all matching elements.
    prize_table = soup.find("table")
    row_elements = prize_table.find_all("tr")

    # The first row is headers so we sort of want
    # to skip it for the calculations, but it includes
    # an important bit of information that we want.
    # The rows only contain winning ticket info.
    # We also care about a row for the losing prize tier.
    # It will have a value of "0" but we want to know
    # how many losing tickets there are.
    #
    # We can calculate that from the first header. It
    # contains the total number of tickets printed.
    # Let's get the total number of tickets printed so
    # we can subtract the sum of the number of winning
    # giving us the number of losing tickets.
    header_row = row_elements[0]
    header_columns = header_row.find_all("th")
    total_number_tickets = int(re.sub(r"\D", "", header_columns[-1].text))

    row_elements = row_elements[1:]

    # We only care about the last and second to last columns.
    # The following helper functions will help us parse
    # the data we care about from each row.
    #
    # The last column is the number of tickets at this prize level.
    # The number of tickets has commas, like 1,350,500.
    # We'll have to parse them out.
    #
    # The second to last column is the prize value.
    # Prize value is usually "$" followed by a number.
    # Those are easy to parse.
    # But for the free ticket prize it's "FREE $1 TICKET"
    def parse_value(row_element):
        columns = row_element.find_all("td")
        try:
            value_element = columns[-3]
            value_text = value_element.text
            return int(re.sub(r"\D", "", value_text))
        except Exception:
            # This is an exception we can handle.
            # We can simply return a value of 0 if
            # the row doesn't have what we expect.
            # Our result might be inaccurate, but
            # I'll consider that acceptable.
            # I'll log something useful so I know
            # to look into it.
            logger.warning("Exception parsing value for a row :%s", row_element.text)
            return 0

    def parse_num_tickets(row_element):
        columns = row_element.find_all("td")
        try:
            num_tickets_element = columns[-1]
            num_tickets_text = num_tickets_element.text
            return int(num_tickets_text.replace(",", ""))
        except:
            # Same as above, we can handle this.
            # Logging and returning 0 is better than blowing up.
            logger.warning(
                "Exception parsing num_tickets for a row.\n{}".format(row_element.text)
            )
            return 0

    # Iterate over each row and parse out the value of the prize tier
    # and the number of remaining tickets at that prize tier.
    rows = [(parse_value(e), parse_num_tickets(e)) for e in row_elements]
    number_winning_tickets = sum(r[1] for r in rows)

    # Insert the losing ticket value, $0, and the number
    # of losing tickets into our rows.
    rows.insert(0, (0, total_number_tickets - number_winning_tickets))
    return rows


def find_price(html):
    """
    Price is hard to find. It seems to always be a sibling to an
    <i> tag which has the text "Price". So, we can find that <i>
    tag, get the text of it's parent, find the last word of that text,
    and that will be the price of the ticket as a string that looks like
    "$10.", which we can then strip of the non-digits.
    """
    soup = bs(html, "lxml")
    price_element = soup.find(string="Price")
    price_text = price_element.parent.parent.text.split(" ")[-1]
    price = int(re.sub(r"\D", "", price_text))
    return price


def calculate_original_ev(game_url):
    """
    The "expected value" or "return on investment" of a game
    will be the total value of the remaining prizes
    divided by the total cost of the remaining tickets.

    Imagine you bought every ticket that was printed.

    How much money would you spend? How much money would you get back in prizes?

    If you won $1,500,000 and spent $2,000,000
    then your expected value is 1,500,000 / 2,000,000 = 0.75.

    For every $1 spent on the game, you'll get back $0.75
    for an average loss of $0.25.
    """
    game_html = fetch_html(game_url)
    game_rules_url = find_complete_game_rules_url(game_html)
    game_rules_html = fetch_html(game_rules_url)
    price = find_price(game_rules_html)
    rows = find_rows(game_rules_html)
    total_number_tickets = sum(r[1] for r in rows)
    total_value_tickets = sum(r[1] * r[0] for r in rows)
    total_cost_tickets = total_number_tickets * price
    ev = total_value_tickets / total_cost_tickets
    return ev


def combine_prizes(prizes):
    combined = []
    last_prize = prizes[0]
    for prize in prizes[1:]:
        if last_prize[-1] == prize[-1]:
            last_prize[0] += prize[0]
        else:
            combined.append(last_prize)
            last_prize = prize
    combined.append(last_prize)
    return combined


def parse_game_html(name, url, html):
    game = {}
    game_soup = bs(html, "lxml")
    game["name"] = name.strip()
    game["url"] = url
    game["game_id"] = re.match(r".*?(\d+$)", url).group(1)
    game_rules_url = find_complete_game_rules_url(html)
    game_rules_html = fetch_html(game_rules_url)
    game_rules_soup = bs(game_rules_html, "lxml")
    game["price"] = find_price(game_rules_html)
    prize_table = game_rules_soup.find("table", class_="miscr")

    def prize_value(p, price):
        p = p.text.strip()
        if re.search(r"FREE", p):
            return price
        else:
            return p.replace("$", "").replace(",", "")

    prize_tuples = [
        [
            int(tds[-1].text.replace(",", "").strip()),
            float(tds[-2].text.replace(",", "").strip()),
            float(prize_value(tds[-3], game["price"])),
            # float(tds[-3].text.replace("$", "").replace(",", "").strip()),
        ]
        for tds in [tr.find_all("td") for tr in prize_table.find_all("tr")[1:]]
    ]
    game["num_tx_initial"] = prize_tuples[-1][0] * prize_tuples[-1][1]
    game["state"] = "pa"
    combined_prizes = sorted(combine_prizes(deepcopy(prize_tuples)), key=lambda x: x[2])
    prizes_remaining_table = game_soup.find("table", class_="table-global").find(
        "tbody"
    )
    prizes_remaining = [
        [
            int(tds[1].text.strip()),
            float(tds[0].text.replace("$", "").replace(",", "").strip()),
        ]
        for tds in [tr.find_all("td") for tr in prizes_remaining_table.find_all("tr")]
    ]
    percent_tx_remain = sum(p[0] for p in prizes_remaining) / sum(
        p[0] for p in combined_prizes[: -len(prizes_remaining) - 1 : -1]
    )
    combined_prizes = sorted(
        [[p[0], p[2]] for p in combined_prizes], key=lambda x: -x[1]
    )
    prizes = sorted(deepcopy(combined_prizes), key=lambda x: -x[1])
    prizes[: len(prizes_remaining)] = prizes_remaining
    for prize in prizes[len(prizes_remaining) :]:
        prize[0] = int(prize[0] * percent_tx_remain)
    game_prizes = []
    for p, orig in zip(prizes, combined_prizes):
        prize = {}
        prize["available"] = p[0]
        prize["claimed"] = orig[0] - p[0]
        prize["value"] = p[1]
        prize["prize"] = locale.currency(p[1], grouping=True)
        game_prizes.append(prize)
    game["prizes"] = game_prizes
    return game


def main():
    index_html = fetch_html(INDEX_URL)
    game_urls = find_game_urls(index_html)
    game_names = find_game_names(index_html)
    # Data will be a list of tuples that looks like:
    # [(Ticket Price, Game Name, Expected Value), ...]
    #
    # The first element of the tuple of the list comprehension below
    # is kind of confusing. We are iterating over game urls.
    # We first fetch the html for the game url. Then we find the
    # game rules url in that page. Then we fetch the html of the game rules
    # page, then we find the price from that html.
    # Hence:
    #     `find_price(fetch_html(find_complete_game_rules_url(fetch_html(url))))`
    games = []

    for name, url in list(zip(game_names, game_urls)):
        try:
            game_html = fetch_html(url)
        except Exception as e:
            logger.error("Error fetching %s: %s", url, e)
            continue
        try:
            games.append(parse_game_html(name, url, game_html))
        except Exception as e:
            t, b, tb = sys.exc_info()
            tb_msg = "\n".join(traceback.format_tb(tb))
            logger.error("Unable to parse game {}.\n{}\n{}".format(name, e, tb_msg))

    return games


if __name__ == "__main__":
    games = main()
    schema = GameSchema(many=True)
    print(schema.dumps(games))
