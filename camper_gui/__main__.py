import customtkinter
import matplotlib
from random import randrange
import requests
import pandas as pd

matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import (
    NavigationToolbar2Tk as NavigationToolbar2TkAgg,
)
from matplotlib.backend_bases import key_press_handler


class MyGraphFrame(customtkinter.CTkFrame):
    def __init__(self, master, title):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.title = title

        f = Figure(figsize=(5, 5), dpi=100)
        self.ax = f.add_subplot(111)
        self.plot_x = []
        self.plot_y = []

        self.canvas = FigureCanvasTkAgg(f, self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(
            side=customtkinter.TOP, fill=customtkinter.BOTH, expand=True
        )

        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self)
        self.toolbar.update()
        self.canvas._tkcanvas.pack(
            side=customtkinter.TOP, fill=customtkinter.BOTH, expand=True
        )

        self.canvas.mpl_connect("key_press_event", self.on_key_event)

        self.update_plot()

    def update_plot(self):
        entity_id = 7
        states_resp = requests.get(
            f"http://localhost:8000/entities/{entity_id}/states",
            params={"limit": 10000},
        )

        if len(states_resp.json()):
            states_df = pd.DataFrame(states_resp.json())
            states_df["created"] = pd.to_datetime(states_df["created"])
            states_df["state"] = pd.to_numeric(states_df["state"])
            states_df = states_df.set_index("created")
            del states_df["id"]

            self.ax.clear()
            states_df.plot(ax=self.ax)
            self.canvas.draw()

        self.after(1000, self.update_plot)

    def on_key_event(self, event):
        print("you pressed %s" % event.key)
        key_press_handler(event, self.canvas, self.toolbar)


class CamperInterfaceFrame(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
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

        self.starter_voltage.set("12 Volt")
        sensors_resp = requests.get(f"http://localhost:8000/sensors")
        self.sensor_id = None
        for sensor in sensors_resp.json():
            if sensor["name"] == "camper":
                self.sensor_id = sensor["id"]
                break

        entities_resp = requests.get(
            f"http://localhost:8000/sensors/{self.sensor_id}/entities"
        )
        self.entity_id_by_name = {e["name"]: e["id"] for e in entities_resp.json()}
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
        if self.entity_states["household_state"] == "OFF":
            data_dict = {"state": "ON"}
        else:
            data_dict = {"state": "OFF"}

        states_resp = requests.post(
            f"http://localhost:8000/action/{self.entity_id_by_name['household_state']}",
            json=data_dict,
        )

        self.entity_states["household_state"] = states_resp.json()["state"]
        self.update_camper_gui()

    def pump_callback(self):
        if self.entity_states["pump_state"] == "OFF":
            data_dict = {"state": "ON"}
        else:
            data_dict = {"state": "OFF"}

        states_resp = requests.post(
            f"http://localhost:8000/action/{self.entity_id_by_name['pump_state']}",
            json=data_dict,
        )

        self.entity_states["pump_state"] = states_resp.json()["state"]
        self.update_camper_gui()

    def update_camper_states(self):
        states_resp = requests.get(
            f"http://localhost:8000/sensors/{self.sensor_id}/states/"
        )
        state_by_id = {s["entity_id"]: s["state"] for s in states_resp.json()}

        for entity_name in self.entity_states.keys():
            entity_id = self.entity_id_by_name[entity_name]
            if entity_id in state_by_id.keys():
                self.entity_states[entity_name] = state_by_id[entity_id]

        self.update_camper_gui()

        self.after(10000, self.update_camper_states)

    def update_camper_gui(self):
        if self.entity_states["household_state"] == "OFF":
            self.household_button.configure(fg_color="red", text="Household [OFF]")
        elif self.entity_states["household_state"] == "ON":
            self.household_button.configure(fg_color="green", text="Household [ON]")
        else:
            self.household_button.configure(
                fg_color="orange", text="Household [PENDING]"
            )

        if self.entity_states["pump_state"] == "ON":
            self.pump_button.configure(fg_color="green", text="Pump [ON]")
        else:
            self.pump_button.configure(fg_color="red", text="Pump [OFF]")

        water_progress = 0
        if self.entity_states["water_state"]:
            water_progress = int(self.entity_states["water_state"]) / 100
        self.water_progress.set(water_progress)

        waste_progress = 0
        if self.entity_states["waste_state"]:
            waste_progress = int(self.entity_states["waste_state"]) / 100
        self.waste_progress.set(waste_progress)

        if (
            self.entity_states["mains_voltage"] is not None
            and int(self.entity_states["mains_voltage"]) > 7000
        ):
            self.mains_button.configure(fg_color="green", text="Mains [CONNECTED]")
        else:
            self.mains_button.configure(fg_color="red", text="Mains [NOT CONNECTED]")

        household_voltage = int(self.entity_states["household_voltage"]) / 1000
        self.household_voltage.set(household_voltage)

        if household_voltage > 12:
            self.household_voltage_entry.configure(fg_color="green")
        else:
            self.household_voltage_entry.configure(fg_color="red")

        starter_voltage = int(self.entity_states["starter_voltage"]) / 1000
        self.starter_voltage.set(household_voltage)

        if starter_voltage > 12:
            self.starter_voltage_entry.configure(fg_color="green")
        else:
            self.starter_voltage_entry.configure(fg_color="red")


class MyRadiobuttonFrame(customtkinter.CTkFrame):
    def __init__(self, master, title, values):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.values = values
        self.title = title
        self.radiobuttons = []
        self.variable = customtkinter.StringVar(value="")

        self.title = customtkinter.CTkLabel(
            self, text=self.title, fg_color="gray30", corner_radius=6
        )
        self.title.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")

        for i, value in enumerate(self.values):
            radiobutton = customtkinter.CTkRadioButton(
                self, text=value, value=value, variable=self.variable
            )
            radiobutton.grid(row=i + 1, column=0, padx=10, pady=(10, 0), sticky="w")
            self.radiobuttons.append(radiobutton)

    def get(self):
        return self.variable.get()

    def set(self, value):
        self.variable.set(value)


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("my app")
        self.geometry("1024x600")
        self.attributes("-fullscreen", True)
        self.grid_columnconfigure((0, 1, 2), weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.camper_interface_frame = CamperInterfaceFrame(self)
        self.camper_interface_frame.grid(
            row=0, column=0, padx=10, pady=(10, 0), sticky="nsew"
        )

        self.radiobutton_frame = MyRadiobuttonFrame(
            self, "Options", values=["option 1", "option 2"]
        )
        self.radiobutton_frame.grid(
            row=0, column=1, padx=(0, 10), pady=(10, 0), sticky="nsew"
        )

        self.graph_frame = MyGraphFrame(self, "Graph")
        self.graph_frame.grid(
            row=0, column=2, padx=(0, 10), pady=(10, 0), sticky="nsew"
        )


app = App()
app.mainloop()
