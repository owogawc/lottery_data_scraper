"""Some marshmallow schemas to do data validation and serialization.

How to use:

Create your model as a plain old Python object.

Example:

    game = {}
    game["game_id"] = "5"
    game["price"] = 30
    game["state"] = "tx"

Then create an instance of the schema.

    schema = GameSchema()

Call `schema.dumps(game)` to "dump" your Python object to a string in JSON
format.

    >>> game = {"game_id": "5", "price": 30, "state": "tx", "created_at": datetime.utcnow()}
    >>> schema = GameSchema()
    >>> schema.dumps(game)
    '{"game_id": "5", "state": "tx", "created_at": "2023-04-08T05:58:49.494561", "price": 30.0, "image_urls": "[]"}'

And you can load a JSON string into a Python object with `schema.loads`.

    >>> schema.loads(schema.dumps(game))
    {'game_id': '5', 'state': 'tx', 'created_at': datetime.datetime(2023, 4, 8, 5, 58, 49, 494561), 'price': 30.0, 'image_urls': []}

Some fields, like `game_id`, are required. You can validate a Python object by calling `schema.validate`.

    >>> game = {"price": 30, "state": "tx", "created_at": datetime.utcnow()}
    >>> schema.dumps(game)
    '{"state": "tx", "created_at": "2023-04-08T06:02:32.126541", "price": 30.0, "image_urls": "[]"}'
    >>> schema.validate(game)
    {'created_at': ['Not a valid datetime.']}
"""
from datetime import datetime
import json
from marshmallow import Schema, fields


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


class GameSchema(Schema):
    class Meta:
        render_module = json

    id = fields.Integer()
    created_at = fields.DateTime(load_default=datetime.utcnow)
    game_id = fields.Str(required=True)
    name = fields.Str()
    description = fields.Str()
    image_urls = fields.Function(
        lambda x: json.dumps(x.get("image_urls", [])),
        deserialize=lambda x: json.loads(x),
    )
    how_to_play = fields.Str()
    num_tx_initial = fields.Integer()
    price = fields.Number()
    prizes = fields.Nested(PrizeSchema, many=True)
    state = fields.Str()
    updated_at = fields.DateTime()
    url = fields.Str()
