import json
import os

if os.path.isfile("config.json"):
    f = open("config.json", "r")
else:
    f = open(f"{os.path.dirname(os.path.realpath(__file__))}/config.json")

try:
    config = json.load(f)
except json.JSONDecodeError as exc:
    print(exc)

influx = config["influx"]
i_de = config["i-de"]
