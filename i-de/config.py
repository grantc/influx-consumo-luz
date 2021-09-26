import json

f = open("config.json", "r")
try:
    config = json.load(f)
except json.JSONDecodeError as exc:
    print(exc)

influx = config["influx"]
i_de = config["i-de"]
shelly = config["shelly"]
