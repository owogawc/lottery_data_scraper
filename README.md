# Parsing of lottery websites

## Demo

The following script should put you in a state where the last line will make a
bunch of requests to the Pennsylvania lottery website, parse the tables of
games/prizes, and print to your terminal a JSON structure of all of the games.

``` sh
git clone https://github.com/owogawc/lottery_data_scraper
cd lottery_data_scraper
python3 -m venv ~/.virtualenvs/lottery_data_scraper
. ~/.virtualenvs/lottery_data_scraper
pip3 install -e .

PY_LOG_LVL=DEBUG USE_CACHE=true python3 -m lottery_data_scraper.pennsylvania 
```

If you have [jq](https://stedolan.github.io/jq/) installed, you can get some
formatted output by piping it to `jq` (and redirecting STDERR to /dev/null).

``` sh
PY_LOG_LVL=DEBUG USE_CACHE=True python3 -m lottery_data_scraper.pennsylvania 2> /dev/null | jq
```

Set `LOGLEVEL` to print useful debug info to console. Defaults to WARNING.

`LOGLEVEL=[DEBUG,INFO,WARNING,ERROR,CRITICAL]`

Set `USE_CACHE` to cache responses. This speeds up development
and is nice to the servers we're hitting.

`USE_CACHE=[True]`

Defaults to False. Note: Setting this env variable to the string False will
cause it to use cache because the string "False" evaluates to Truthy. Either set
it to True or don't set it.

# Methodology

Most states publish the total number of tickets printed and how many tickets are
printed at each prize level.

We can calculated the expected value of a game by summing the value of all the
prizes and dividing that by the cost of all the tickets.

Most state websites have an "index" page that has links to every game. Each
individual game has a link to a "game rules" page. We start at the index and
visit every game rules page, then we can find the html table on that page which
has the detailed prize information and run our calculations.

For example:
https://www.palottery.state.pa.us/Scratch-Offs/Active-Games.aspx

# Data models

We're using [`marshmallow`](https://marshmallow.readthedocs.io/en/stable/index.html) to validate and serialize data.

I'm including the schemas here just so you can quickly get a general idea of
what data fields we're able to scrape from most lottery websites. What you see
in this README might not be up-to-date with what's in
[schemas.py](./lottery_data_scraper/schemas.py).

As of 2023-04-07 the schemas are a work-in-progress. The remaining TODO is to
determine and specify which fields are absolutely required and which are
optional.

## Game Schema

``` python
class GameSchema(Schema):
    class Meta:
        render_module = json

    id = fields.Integer()
    created_at = fields.DateTime(load_default=datetime.utcnow)
    game_id = fields.Str()
    name = fields.Str()
    description = fields.Str()
    image_urls = fields.Function(
        lambda x: json.loads(x.image_urls) if x.image_urls else [],
        deserialize=lambda x: None if x.image_urls == [] else json.dumps(x.image_urls),
    )
    how_to_play = fields.Str()
    num_tx_initial = fields.Integer()
    price = fields.Number()
    prizes = fields.Nested(PrizeSchema, many=True)
    state = fields.Str()
    updated_at = fields.DateTime()
    url = fields.Str()
```

## Prize Schema

``` python
class PrizeSchema(Schema):
    class Meta:
        render_module = json

    id = fields.Integer()
    game_id = fields.Integer()
    available = fields.Integer()
    claimed = fields.Integer()
    created_at = fields.DateTime(load_default=datetime.utcnow)
    value = fields.Number()
    prize = fields.Str()
```

# Tests

Testing is kind of tricky because you can't rely on _just_ python with its
`requests` library. Some states have some scrape protections that require you
actually run JavaScript. Some states have extreme scrape protection that require
you to actually run a _display_. They check for some rendering context that
doesn't exist when you run a headless browser in Selenium. To scrape those
sites, you actually have to run a [X virtual
framebuffer](https://en.wikipedia.org/wiki/Xvfb). Testing in these cases isn't
as simple as running `python3 -m unittest discover`.

# Contributing

``` sh
git clone https://github.com/owogawc/lottery_data_scraper
cd lottery_data_scraper
python3 -m venv ~/.virtualenvs/lottery_data_scraper
. ~/.virtualenvs/lottery_data_scraper
pip3 install -e .
```

Then you should be able to run `make test` and see the tests pass.

## Style

> "Any color you like."

From the root directory of the repository, run `python3 -m black lottery_data_scraper`.

That will format your code according to [Black](https://pypi.org/project/black/).
