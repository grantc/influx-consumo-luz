from datetime import datetime, timedelta

from config import shelly, influx

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.domain.write_precision import WritePrecision

from rich.console import Console

import requests
import time
import pytz


class lector:
    def __init__(self) -> None:
        self.luz_neto = 0  # consumo y placas combinado
        self.solar = 1  # Placas


    def precios(self):
        """Emitir datos de los sensores"""

        # Init
        precio_excedentes = 0.08
        precio_valle = 0.097
        precio_llano = 0.126
        precio_punta = 0.172

        datos = {
            "precio_excedentes" : precio_excedentes,
            "precio_valle" : precio_valle,
            "precio_llano" : precio_llano,
            "precio_punta" : precio_punta,
        }
        # console.log(f"{datos}")
        return datos

    def escritura(self, datos):

        client = InfluxDBClient(
            url=influx["url"], token=influx["token"], org=influx["org"]
        )
        write_api = client.write_api(write_options=SYNCHRONOUS)

        medidas = [
            "precio_excedentes",
            "precio_valle",
            "precio_llano",
            "precio_punta",
        ]

        tz = pytz.timezone("Europe/Madrid")
        now_local = datetime.now(tz)
        for medida in medidas:
            p = (
                Point.measurement("precios_luz")
                .tag("lugar", "casa")
                .field(medida, datos[medida])
                .time(
                  now_local + timedelta(seconds=0),
                  write_precision=WritePrecision.S,
                )
            )
            write_api.write(bucket=influx["bucket"], record=p)

console = Console()


def main():

    shelly = lector()
    while True:
        datos = shelly.precios()
        shelly.escritura(datos)
        time.sleep(3600)


if __name__ == "__main__":
    main()
