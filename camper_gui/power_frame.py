import requests

from config import settings
from frame_base import FrameBase


class ApiException(Exception):
    pass


class PowerFrame(FrameBase):
    def __init__(self, master, statusbar, api_sensors):
        super().__init__(master)
        self.master = master
        self.statusbar = statusbar
        self.entity_id_by_name = {}

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(0, weight=0)

        self.title_label = self._add_title("Power")
        self.soc, self.soc_label, self.soc_entry = self._add_entry(
            "State Of Charge [%]", 1, 0
        )
        self.remaining_mins, self.remaining_mins_label, self.remaining_mins_entry = (
            self._add_entry("Remaining [min]", 1, 1)
        )
        self.consumed_ah, self.consumed_ah_label, self.consumed_ah_entry = (
            self._add_entry("Consumed [Ah]", 3, 0)
        )
        self.solar_power, self.solar_power_label, self.solar_power_entry = (
            self._add_entry("Solar [W]", 3, 1)
        )
        self.yield_today, self.yield_today_label, self.yield_today_entry = (
            self._add_entry("Yield today", 5, 0)
        )
        self.charge_state, self.charge_state_label, self.charge_state_entry = (
            self._add_entry("Charge stage", 5, 1)
        )

        try:
            self.sensor_shunt_id = None
            self.sensor_solar_id = None
            for sensor in api_sensors:
                if sensor["name"] == "SmartSolar":
                    self.sensor_solar_id = sensor["id"]
                    self.entity_id_by_name.update(
                        {e["name"]: e["id"] for e in sensor["entities"]}
                    )
                elif sensor["name"] == "SmartShunt":
                    self.sensor_shunt_id = sensor["id"]
                    self.entity_id_by_name.update(
                        {e["name"]: e["id"] for e in sensor["entities"]}
                    )

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            ApiException,
        ) as ex:
            self.sensor_shunt_id = None
            self.sensor_solar_id = None
            self.entity_id_by_name = {}
            self.statusbar.add_message(
                f"Could not communicatie with API: {ex.__class__.__name__}",
                details=str(ex),
            )

        self.entity_states = {
            "soc": None,
            "remaining_mins": None,
            "consumed_ah": None,
            "solar_power": None,
            "yield_today": None,
            "charge_state": None,
        }
        self.update_states_runner()

    def update_states_runner(self):
        current_tab = self.master.master.get()

        if current_tab == "Status":
            self.update_states()
        else:
            for entity_name in self.entity_states.keys():
                self.entity_states[entity_name] = None

            self.update_gui()

        self.after(5000, self.update_states_runner)

    def update_states(self):
        try:
            if self.sensor_shunt_id is None:
                raise ApiException("sensor_shunt_id not set")

            if self.sensor_solar_id is None:
                raise ApiException("sensor_solar_id not set")

            for sensor_id in (self.sensor_shunt_id, self.sensor_solar_id):
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

        self.update_gui()

    def update_gui(self):
        if self.entity_states["soc"]:
            self.soc.set(float(self.entity_states["soc"]))
            self.soc_entry.configure(fg_color="white")
        else:
            self.soc_entry.configure(fg_color="grey")

        if self.entity_states["remaining_mins"]:
            self.remaining_mins.set(float(self.entity_states["remaining_mins"]))
            self.remaining_mins_entry.configure(fg_color="white")
        else:
            self.remaining_mins_entry.configure(fg_color="grey")

        if self.entity_states["consumed_ah"]:
            self.consumed_ah.set(float(self.entity_states["consumed_ah"]))
            self.consumed_ah_entry.configure(fg_color="white")
        else:
            self.consumed_ah_entry.configure(fg_color="grey")

        if self.entity_states["solar_power"]:
            self.solar_power.set(float(self.entity_states["solar_power"]))
            self.solar_power_entry.configure(fg_color="white")
        else:
            self.solar_power_entry.configure(fg_color="grey")

        if self.entity_states["yield_today"]:
            self.yield_today.set(float(self.entity_states["yield_today"]))
            self.yield_today_entry.configure(fg_color="white")
        else:
            self.yield_today_entry.configure(fg_color="grey")

        if self.entity_states["charge_state"]:
            self.charge_state.set(self.entity_states["charge_state"])
            self.charge_state_entry.configure(fg_color="white")
        else:
            self.charge_state_entry.configure(fg_color="grey")
