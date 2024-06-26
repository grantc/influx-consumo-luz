import sys

from os import times
from influxdb_client.domain.write_precision import WritePrecision
from oligo import Iber
from oligo.iber import ResponseException
from datetime import date, time, timedelta, datetime

from config import *

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from rich.console import Console

from pprint import pprint

import pytz


class lector:
    def __init__(self, username, password) -> None:
        self.connection = Iber()
        self.connection.login(username, password)

    def lectura_periodo(self, start=7, end=1):
        """ """

        from_date = date.today() - timedelta(days=start)
        until_date = date.today() - timedelta(days=end)

        try:
            consumo = self.connection.consumption(from_date, until_date)
        except ResponseException as e:
            console.log(str(e.message))
            sys.exit(1)

        timeseries = []
        timestamp = datetime.combine(from_date, time()) - timedelta(hours=0)
        # Añadir el TZ al timestamp para que Influx sabe convertirlo a UTC
        madrid = pytz.timezone("Europe/Madrid")
        for kw in consumo:
            if kw is not None:
                local_timestamp = madrid.localize(timestamp)
                lector = {"timestamp": local_timestamp, "valor": kw}
                timeseries.append(lector)
            timestamp = timestamp + timedelta(hours=1)

        return timeseries

    def lectura_actual(self):
        watt = self.connection.watthourmeter()
        print(watt)


def influx_write(data):

    client = InfluxDBClient(url=influx["url"], token=influx["token"], org=influx["org"])

    write_api = client.write_api(write_options=SYNCHRONOUS)

    for row in data:
        console.log(row)
        p = (
            Point.measurement("distribución")
            .tag("lugar", "zaratan")
            .field("lectura", row["valor"])
            .time(
                row["timestamp"] + timedelta(seconds=0),
                write_precision=WritePrecision.S,
            )
        )
        write_api.write(bucket=influx["bucket"], record=p)


console = Console()


def main():

    l = lector(i_de["username"], i_de["password"])
    lecturas = l.lectura_periodo(start=i_de["days"])
    # console.log(lecturas)

    influx_write(lecturas)


if __name__ == "__main__":
    main()
