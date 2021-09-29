import sys

from os import times
from datetime import date, time, datetime

from config import *

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from rich.console import Console

import requests
import time
import pytz


class lector:
    def __init__(self) -> None:
        pass

    def lectura_actual(self, config, sensor):

        url = f"http://{config['server']}/emeter/{sensor}"
        response = requests.get(url)
        lectura = response.json()
        timestamp = datetime.now()
        lectura["timestamp"] = timestamp
        return [lectura]


def influx_write(data):

    client = InfluxDBClient(url=influx["url"], token=influx["token"], org=influx["org"])

    write_api = client.write_api(write_options=SYNCHRONOUS)

    for row in data:
        dow = datetime.today().weekday()
        if dow >= 5:
            lectura = "lectura_valle"
            console.log(f"{dow} - {lectura} - {row['power']}")
        else:
            tz = pytz.timezone("Europe/Madrid")
            now_local = datetime.now(tz)
            current_hour = int(now_local.strftime("%H"))
            if current_hour < 8:  # 00:00-07:59 valle
                lectura = "lectura_valle"
            elif current_hour < 10:  # 8:00-09:59 llano
                lectura = "lectura_llano"
            elif current_hour < 14:  # 10:00-13:59 punto
                lectura = "lectura_punto"
            elif current_hour < 18:  # 14:00-17:59 llano
                lectura = "lectura_llano"
            elif current_hour < 22:  # 18:00-21:59 punto
                lectura = "lectura_punto"
            else:  # 22:00-23:59 punto llano
                lectura = "lectura_llano"
            console.log(f"{dow} - {current_hour} - {lectura} - {row['power']}")

        p = (
            Point.measurement("shelly")
            .tag("lugar", "casa")
            .field(lectura, row["power"])
            .field("voltaje", row["voltage"])
            .field("reactivo", row["reactive"])
        )
        write_api.write(bucket=influx["bucket"], record=p)


console = Console()


def main():

    l = lector()
    while True:
        lecturas = l.lectura_actual(shelly, 0)
        influx_write(lecturas)
        time.sleep(1)


if __name__ == "__main__":
    main()
