import logging

logging.basicConfig(level=logging.INFO)

from quart import Quart

from bovine_herd import BovineHerd
from bovine_pubsub import BovinePubSub

app = Quart(__name__)
BovinePubSub(app)
BovineHerd(app)
