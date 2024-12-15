import requests

from config import settings
from frame_base import FrameBase


class ApiException(Exception):
    pass


class TemperatureFrame(FrameBase):
    def __init__(self, master, statusbar, api_sensors, executor):
        super().__init__(master)
        self.master = master
        self.statusbar = statusbar
        self.executor = executor
        self.entity_id_by_name = {}

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(0, weight=0)

        self.title_label = self._add_title("Temperature & Humidity")
        (
            self.outside_temperature,
            self.outside_temperature_label,
            self.outside_temperature_entry,
        ) = self._add_entry("Outside [C]", 1, 0)
        (
            self.inside_temperature,
            self.inside_temperature_label,
            self.inside_temperature_entry,
        ) = self._add_entry("Inside [C]", 1, 1)
        (
            self.outside_humidity,
            self.outside_humidity_label,
            self.outside_humidity_entry,
        ) = self._add_entry("Outside Humidity [%]", 3, 0)
        self.inside_humidity, self.inside_humidity_label, self.inside_humidity_entry = (
            self._add_entry("Inside Humidity [%]", 3, 1)
        )

        self.sensor_outside_id = None
        self.sensor_inside_id = None
        for sensor in api_sensors:
            if sensor["name"] == "outside":
                self.sensor_outside_id = sensor["id"]

                self.entity_id_by_name.update(
                    {f"outside_{e['name']}": e["id"] for e in sensor["entities"]}
                )

            elif sensor["name"] == "inside":
                self.sensor_inside_id = sensor["id"]

                self.entity_id_by_name.update(
                    {f"inside_{e['name']}": e["id"] for e in sensor["entities"]}
                )

        self.entity_states = {
            "outside_temperature": None,
            "outside_humidity": None,
            "inside_temperature": None,
            "inside_humidity": None,
        }
        self.update_states_runner()

    def update_states_runner(self):
        current_tab = self.master.master.get()

        if current_tab == "Status":
            self.executor.submit(self.update_states)
        else:
            for entity_name in self.entity_states.keys():
                self.entity_states[entity_name] = None

            self.update_gui()

        self.after(5000, self.update_states_runner)

    def update_states(self):
        try:
            if self.sensor_outside_id is None:
                raise ApiException("sensor_outside_id not set")

            if self.sensor_inside_id is None:
                raise ApiException("sensor_inside_id not set")

            for sensor_id in (self.sensor_outside_id, self.sensor_inside_id):
                states_resp = requests.get(
                    f"{settings.api_base}/sensors/{sensor_id}/states/", timeout=3
                )
                state_by_id = {s["entity_id"]: s["state"] for s in states_resp.json()}

                for entity_name in self.entity_states.keys():
                    entity_id = self.entity_id_by_name[entity_name]
                    if entity_id in state_by_id.keys():
                        self.entity_states[entity_name] = state_by_id[entity_id]
        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            ApiException,
        ) as ex:
            for entity_name in self.entity_states.keys():
                self.entity_states[entity_name] = None

            self.statusbar.add_message(
                f"Could not retrieve status from API: {ex.__class__.__name__}",
                details=str(ex),
            )
        except Exception as ex:
            for entity_name in self.entity_states.keys():
                self.entity_states[entity_name] = None

            self.statusbar.add_message(
                f"General exception: {ex.__class__.__name__}",
                details=str(ex),
            )

        self.update_gui()

    def update_gui(self):
        if self.entity_states["outside_temperature"]:
            self.outside_temperature.set(
                float(self.entity_states["outside_temperature"])
            )
            self.outside_temperature_entry.configure(fg_color="white")
        else:
            self.outside_temperature_entry.configure(fg_color="grey")

        if self.entity_states["inside_temperature"]:
            self.inside_temperature.set(float(self.entity_states["inside_temperature"]))
            self.inside_temperature_entry.configure(fg_color="white")
        else:
            self.inside_temperature_entry.configure(fg_color="grey")

        if self.entity_states["outside_humidity"]:
            self.outside_humidity.set(float(self.entity_states["outside_humidity"]))
            self.outside_humidity_entry.configure(fg_color="white")
        else:
            self.outside_humidity_entry.configure(fg_color="grey")

        if self.entity_states["inside_humidity"]:
            self.inside_humidity.set(float(self.entity_states["inside_humidity"]))
            self.inside_humidity_entry.configure(fg_color="white")
        else:
            self.inside_humidity_entry.configure(fg_color="grey")
