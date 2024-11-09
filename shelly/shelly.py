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

    def lectura_actual(self, config, sensor):
        """Leer del shelly"""
        url = f"http://{config['server']}/emeter/{sensor}"
        timestamp = datetime.now()
        lectura = {
            'power': 0.0,
            'reactive': 0.0,
            'voltage': 240.0,
            'timestamp': timestamp,
        }
        try:
            response = requests.get(url)
            lectura = response.json()
        except requests.exceptions.ConnectionError:
            print("Unable to connect to shelly")
        return [lectura][0]

    def lectura(self):
        """Leer datos de los sensores"""

        # Init
        neto = {"power": 0.0}
        consumo = {"power": 0.0}
        importacion = {"power": 0.0}
        excedentes = {"power": 0.0}

        try:
            # Neto de consumo actual y la generación de las placas
            luz_neto = self.lectura_actual(shelly, self.luz_neto)
            # console.log(f"{self.luz_neto} - {luz_neto}")
        except Exception:
            raise Exception("Error fetching shelly data")

        # Generacion de las placas
        solar = self.lectura_actual(shelly, self.solar)
        # console.log(f"{self.solar} - {solar}")
        if solar["power"] < 0:
            # Solar es un valor negativo
            solar["power"] = solar["power"] * -1

        # Consumo real = neto - solar
        consumo["power"] = round(luz_neto["power"] + solar["power"], 2)

        # Vertimos a la red?
        if luz_neto["power"] < 0:  # excedentes
            excedentes["power"] = luz_neto["power"] * -1
            importacion["power"] = 0.0
            neto["power"] = 0.0
        else:
            importacion["power"] = luz_neto["power"]
            excedentes["power"] = 0.0

        periodo = self.periodo()

        datos = {
            "consumo": consumo["power"],
            "excedentes": excedentes["power"],
            "importacion": importacion["power"],
            "solar": solar["power"],
            "neto": neto["power"],
            "luz_neto": luz_neto["power"],
            "periodo": periodo,
            "reactivo": luz_neto["reactive"],
            "voltaje": luz_neto["voltage"]
        }
        # console.log(f"{datos}")
        return datos

    def escritura(self, datos):

        client = InfluxDBClient(
            url=influx["url"], token=influx["token"], org=influx["org"]
        )
        write_api = client.write_api(write_options=SYNCHRONOUS)

        medidas = [
            "consumo",
            "excedentes",
            "importacion",
            "luz_neto",
            "neto",
            "solar",
        ]

        tz = pytz.timezone("Europe/Madrid")
        now_local = datetime.now(tz)
        for medida in medidas:
            p = (
                Point.measurement(medida)
                .tag("lugar", "casa")
                .field(datos["periodo"], datos[medida])
                .field("voltaje", datos["voltaje"])
                .field("reactivo", datos["reactivo"])
                .field("lectura", datos[medida])
                .time(
                  now_local + timedelta(seconds=0),
                  write_precision=WritePrecision.S,
                )
            )
            try:
                write_api.write(bucket=influx["bucket"], record=p)
            except OSError:
                raise Exception("Failed to connect to influx")

    def periodo(self):
        """Calcula el periodo de luz"""
        dow = datetime.today().weekday()
        if dow >= 5:
            lectura = "lectura_valle"
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
        return lectura


console = Console()


def main():

    shelly = lector()
    while True:
        datos = shelly.lectura()
        shelly.escritura(datos)
        time.sleep(1)


if __name__ == "__main__":
    main()
