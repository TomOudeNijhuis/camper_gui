import requests
import tkinter as tk

from config import settings
from frame_base import FrameBase


class ApiException(Exception):
    pass


class CamperInterfaceFrame(FrameBase):
    def __init__(self, master, statusbar, api_sensors, executor):
        super().__init__(master)
        self.master = master
        self.statusbar = statusbar
        self.executor = executor

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(0, weight=0)

        self.title_label = self._add_title("Camper")
        self.household_button = self._add_button(
            "Household", 1, 0, columnspan=2, command=self.household_callback
        )
        self.pump_button = self._add_button(
            "Pump", 2, 0, columnspan=2, command=self.pump_callback
        )
        self.household_button.configure(state=tk.DISABLED)
        self.pump_button.configure(state=tk.DISABLED)

        self.water_label, self.water_progress = self._add_progress(
            "Water", 3, 0, columnspan=2
        )
        self.waste_label, self.waste_progress = self._add_progress(
            "Waste", 5, 0, columnspan=2
        )
        self.mains_button = self._add_button(
            "Mains", 7, 0, columnspan=2, state="disabled", hover=False
        )

        self.starter_voltage, self.starter_voltage_label, self.starter_voltage_entry = (
            self._add_entry("Starter [V]", 8, 0)
        )
        (
            self.household_voltage,
            self.household_voltage_label,
            self.household_voltage_entry,
        ) = self._add_entry("Household [V]", 8, 1)

        self.sensor_id = None
        for sensor in api_sensors:
            if sensor["name"] == "camper":
                self.sensor_id = sensor["id"]
                self.entity_id_by_name = {
                    e["name"]: e["id"] for e in sensor["entities"]
                }
                break

        self.entity_states = {
            "household_voltage": None,
            "starter_voltage": None,
            "mains_voltage": None,
            "household_state": None,
            "water_state": None,
            "waste_state": None,
            "pump_state": None,
        }

        self.update_states_runner()

    def _api_action(self, entity_name, state):
        try:
            if entity_name not in self.entity_id_by_name:
                raise ApiException(f"No entity_id for `{entity_name}`")

            data_dict = {"state": state}
            states_resp = requests.post(
                f"{settings.api_base}/action/{self.entity_id_by_name[entity_name]}",
                json=data_dict,
            )

            self.entity_states[entity_name] = states_resp.json()["state"]
        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            ApiException,
        ) as ex:
            self.entity_states["household_state"] = None

            self.statusbar.add_message(
                f"Could not retrieve household state from API: {ex.__class__.__name__}",
                details=str(ex),
            )
        except Exception as ex:
            self.entity_states["household_state"] = None

            self.statusbar.add_message(
                f"General exception: {ex.__class__.__name__}",
                details=str(ex),
            )
        self.update_camper_gui()

    def household_callback(self):
        self.household_button.configure(state=tk.DISABLED)
        self.pump_button.configure(state=tk.DISABLED)

        if self.entity_states["household_state"] == "OFF":
            self.executor.submit(self._api_action, "household_state", "ON")
        else:
            self.executor.submit(self._api_action, "household_state", "OFF")

    def pump_callback(self):
        self.household_button.configure(state=tk.DISABLED)
        self.pump_button.configure(state=tk.DISABLED)

        if self.entity_states["pump_state"] == "OFF":
            self.executor.submit(self._api_action, "pump_state", "ON")
        else:
            self.executor.submit(self._api_action, "pump_state", "OFF")

    def update_states_runner(self):
        current_tab = self.master.master.get()

        if current_tab == "Status":
            self.executor.submit(self.update_states)
        else:
            for entity_name in self.entity_states.keys():
                self.entity_states[entity_name] = None

            self.update_camper_gui()

        self.after(5000, self.update_states_runner)

    def update_states(self):
        try:
            if self.sensor_id is None:
                raise ApiException("sensor_id not set")

            states_resp = requests.get(
                f"{settings.api_base}/sensors/{self.sensor_id}/states/", timeout=3
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

        self.update_camper_gui()

    def update_camper_gui(self):
        match self.entity_states["household_state"]:
            case "OFF":
                self.household_button.configure(
                    fg_color="darkred", text="Household [OFF]"
                )
            case "ON":
                self.household_button.configure(fg_color="green", text="Household [ON]")
            case "PENDING":
                self.household_button.configure(
                    fg_color="orange", text="Household [PENDING]"
                )
            case _:
                self.household_button.configure(
                    fg_color="gray", text="Household [Unknown]"
                )

        match self.entity_states["pump_state"]:
            case "ON":
                self.pump_button.configure(fg_color="green", text="Pump [ON]")
            case "OFF":
                self.pump_button.configure(fg_color="darkred", text="Pump [OFF]")
            case _:
                self.pump_button.configure(fg_color="gray", text="Pump [Unknown]")

        self.household_button.configure(state=tk.NORMAL)
        self.pump_button.configure(state=tk.NORMAL)

        water_progress = 0
        if self.entity_states["water_state"]:
            water_progress = int(self.entity_states["water_state"]) / 100
        self.water_progress.set(water_progress)

        waste_progress = 0
        if self.entity_states["waste_state"]:
            waste_progress = int(self.entity_states["waste_state"]) / 100
        self.waste_progress.set(waste_progress)

        if self.entity_states["mains_voltage"] is not None:
            if int(self.entity_states["mains_voltage"]) > 7000:
                self.mains_button.configure(fg_color="green", text="Mains [CONNECTED]")
            else:
                self.mains_button.configure(
                    fg_color="darkred", text="Mains [NOT CONNECTED]"
                )
        else:
            self.mains_button.configure(fg_color="gray", text="Mains [Unknown]")

        if self.entity_states["household_voltage"]:
            household_voltage = int(self.entity_states["household_voltage"]) / 1000
            self.household_voltage.set(household_voltage)

            if household_voltage > 12:
                self.household_voltage_entry.configure(fg_color="green")
            else:
                self.household_voltage_entry.configure(fg_color="red")
        else:
            self.household_voltage_entry.configure(fg_color="grey")

        if self.entity_states["starter_voltage"]:
            starter_voltage = int(self.entity_states["starter_voltage"]) / 1000
            self.starter_voltage.set(starter_voltage)

            if starter_voltage > 12:
                self.starter_voltage_entry.configure(fg_color="green")
            else:
                self.starter_voltage_entry.configure(fg_color="red")
        else:
            self.starter_voltage_entry.configure(fg_color="grey")
