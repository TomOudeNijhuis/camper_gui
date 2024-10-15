import customtkinter
import requests


class ApiException(Exception):
    pass


class CamperInterfaceFrame(customtkinter.CTkFrame):
    def __init__(self, master, statusbar, api_sensors):
        super().__init__(master)
        self.master = master
        self.statusbar = statusbar

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(0, weight=0)

        self.title = customtkinter.CTkLabel(
            self, text="Camper", fg_color="gray30", corner_radius=6
        )
        self.title.grid(
            row=0, column=0, padx=10, pady=(10, 0), sticky="ew", columnspan=2
        )

        self.household_button = customtkinter.CTkButton(
            self,
            text="Household",
            command=self.household_callback,
            height=45,
            text_color="black",
            font=("font2", 15),
        )
        self.household_button.grid(
            row=1, column=0, padx=10, pady=10, sticky="ew", columnspan=2
        )

        self.pump_button = customtkinter.CTkButton(
            self,
            text="Pump",
            command=self.pump_callback,
            height=45,
            text_color="black",
            font=("font2", 15),
        )
        self.pump_button.grid(
            row=2, column=0, padx=10, pady=10, sticky="ew", columnspan=2
        )
        self.water_label = customtkinter.CTkLabel(
            self, text="Water", fg_color="transparent", justify="left"
        )
        self.water_label.grid(
            row=3, column=0, padx=10, pady=2, sticky="sw", columnspan=2
        )
        self.water_progress = customtkinter.CTkProgressBar(
            self, orientation="horizontal"
        )
        self.water_progress.grid(
            row=4, column=0, padx=10, pady=2, sticky="ew", columnspan=2
        )

        self.waste_label = customtkinter.CTkLabel(
            self, text="Waste", fg_color="transparent", justify="left"
        )
        self.waste_label.grid(
            row=5, column=0, padx=10, pady=2, sticky="sw", columnspan=2
        )
        self.waste_progress = customtkinter.CTkProgressBar(
            self, orientation="horizontal"
        )
        self.waste_progress.grid(
            row=6, column=0, padx=10, pady=2, sticky="ew", columnspan=2
        )

        self.mains_button = customtkinter.CTkButton(
            self,
            text="Mains",
            height=45,
            text_color_disabled="black",
            font=("font2", 15),
            hover=False,
            state="disabled",
        )
        self.mains_button.grid(
            row=7, column=0, padx=10, pady=10, sticky="ew", columnspan=2
        )

        self.starter_voltage_label = customtkinter.CTkLabel(
            self, text="Starter [V]", fg_color="transparent", justify="left"
        )
        self.starter_voltage_label.grid(
            row=8, column=0, padx=10, pady=2, sticky="sw", columnspan=1
        )
        self.starter_voltage = customtkinter.StringVar()
        self.starter_voltage_entry = customtkinter.CTkEntry(
            self,
            textvariable=self.starter_voltage,
            text_color="black",
            font=("font2", 15),
            height=45,
            state="disabled",
        )
        self.starter_voltage_entry.grid(
            row=9, column=0, padx=10, pady=2, sticky="ew", columnspan=1
        )

        self.household_voltage_label = customtkinter.CTkLabel(
            self, text="Household [V]", fg_color="transparent", justify="left"
        )
        self.household_voltage_label.grid(
            row=8, column=1, padx=10, pady=2, sticky="sw", columnspan=1
        )
        self.household_voltage = customtkinter.StringVar()
        self.household_voltage_entry = customtkinter.CTkEntry(
            self,
            textvariable=self.household_voltage,
            text_color="black",
            font=("font2", 15),
            height=45,
            state="disabled",
        )
        self.household_voltage_entry.grid(
            row=9, column=1, padx=10, pady=2, sticky="ew", columnspan=1
        )

        try:
            self.sensor_id = None
            for sensor in api_sensors:
                if sensor["name"] == "camper":
                    self.sensor_id = sensor["id"]
                    break

            if self.sensor_id is None:
                raise ApiException("No sensor_id for `camper` in API sensor list.")

            entities_resp = requests.get(
                f"http://localhost:8000/sensors/{self.sensor_id}/entities", timeout=3
            )
            self.entity_id_by_name = {e["name"]: e["id"] for e in entities_resp.json()}

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            ApiException,
        ) as ex:
            self.sensor_id = None
            self.entity_id_by_name = {}
            self.statusbar.add_message(
                f"Could not communicatie with API: {ex.__class__.__name__}",
                details=str(ex),
            )

        self.entity_states = {
            "household_voltage": None,
            "starter_voltage": None,
            "mains_voltage": None,
            "household_state": None,
            "water_state": None,
            "waste_state": None,
            "pump_state": None,
        }
        self.update_camper_states()

    def household_callback(self):
        try:
            if "household_state" not in self.entity_id_by_name:
                raise ApiException(f"No entity_id for `household_state`")

            if self.entity_states["household_state"] == "OFF":
                data_dict = {"state": "ON"}
            else:
                data_dict = {"state": "OFF"}

            states_resp = requests.post(
                f"http://localhost:8000/action/{self.entity_id_by_name['household_state']}",
                json=data_dict,
            )

            self.entity_states["household_state"] = states_resp.json()["state"]

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            ApiException,
        ) as ex:
            self.entity_states["household_state"] = None

            self.statusbar.add_message(
                f"Could not update household state in API: {ex.__class__.__name__}",
                details=str(ex),
            )

        self.update_camper_gui()

    def pump_callback(self):
        try:
            if "pump_state" not in self.entity_id_by_name:
                raise ApiException(f"No entity_id for `pump_state`")

            if self.entity_states["pump_state"] == "OFF":
                data_dict = {"state": "ON"}
            else:
                data_dict = {"state": "OFF"}

            states_resp = requests.post(
                f"http://localhost:8000/action/{self.entity_id_by_name['pump_state']}",
                json=data_dict,
            )

            self.entity_states["pump_state"] = states_resp.json()["state"]

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            ApiException,
        ) as ex:
            self.entity_states["household_state"] = None

            self.statusbar.add_message(
                f"Could not update pump state in API: {ex.__class__.__name__}",
                details=str(ex),
            )

        self.update_camper_gui()

    def update_camper_states(self):
        current_tab = self.master.master.get()

        if current_tab == "Status":
            try:
                if self.sensor_id is None:
                    raise ApiException("sensor_id not set")

                states_resp = requests.get(
                    f"http://localhost:8000/sensors/{self.sensor_id}/states/", timeout=3
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

        else:
            for entity_name in self.entity_states.keys():
                self.entity_states[entity_name] = None

        self.after(5000, self.update_camper_states)

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
