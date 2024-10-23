import customtkinter
import tkinter
import requests
from datetime import timedelta
import matplotlib

matplotlib.use("TkAgg")

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import (
    NavigationToolbar2Tk as NavigationToolbar2TkAgg,
)
from matplotlib.backend_bases import key_press_handler
import pandas as pd

from config import settings


class ApiException(Exception):
    pass


class EntityFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master, statusbar):
        super().__init__(master)
        self.statusbar = statusbar
        self.radio_var = tkinter.StringVar(value=None)
        self.radiobuttons = []

    def add(self, text):
        self.radiobuttons.append(
            customtkinter.CTkRadioButton(
                self, text=text.replace("_", " "), variable=self.radio_var, value=text
            )
        )
        self.radiobuttons[-1].grid(
            row=len(self.radiobuttons) - 1,
            column=0,
            padx=10,
            pady=(10, 0),
            sticky="w",
        )

    def get(self):
        return self.radio_var.get()


class GraphFrame(customtkinter.CTkFrame):
    def __init__(self, master, statusbar, api_sensors):
        super().__init__(master)
        self.statusbar = statusbar

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)

        f = Figure(figsize=(4, 4.7), dpi=100)
        self.ax = f.add_subplot(111)
        self.plot_x = []
        self.plot_y = []

        self.canvas = FigureCanvasTkAgg(f, self)
        self.canvas.draw()
        """
        self.canvas.get_tk_widget().pack(
            side=customtkinter.TOP, fill=customtkinter.BOTH, expand=True
        )
        """
        self.canvas.get_tk_widget().grid(
            row=0, column=1, padx=10, pady=2, sticky="ew", columnspan=1
        )
        """
        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self)
        self.toolbar.update()
        self.canvas._tkcanvas.pack(
            side=customtkinter.TOP, fill=customtkinter.BOTH, expand=True
        )
        """
        self.canvas.mpl_connect("key_press_event", self.on_key_event)
        self.entity_id_by_name = {}
        self.entity_frame = EntityFrame(self, self.statusbar)
        self.entity_frame.grid(
            row=0, column=0, padx=10, pady=2, sticky="nsew", columnspan=1
        )

        try:
            for sensor in api_sensors:
                for entity in sensor["entities"]:
                    self.entity_id_by_name[f"{sensor['name']}_{entity['name']}"] = {
                        "entity_id": entity["id"],
                        "entity_name": entity["name"],
                        "unit": entity["unit"],
                        "sensor_id": entity["sensor_id"],
                        "sensor_name": sensor["name"],
                    }

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

        self.checkboxes = []

        for k, v in self.entity_id_by_name.items():
            self.entity_frame.add(k)

        self.update_plot_runner()

    def update_plot_runner(self):
        current_tab = self.master.master.get()

        if current_tab == "History":
            self.update_plot()
        else:
            self.ax.clear()
            self.canvas.draw()

        self.after(5000, self.update_plot_runner)

    def update_plot(self):
        entity = None

        entity_name = self.entity_frame.get()
        if entity_name:
            entity = self.entity_id_by_name[entity_name]

        if entity is None:
            states_resp = None
        else:
            try:
                states_resp = requests.get(
                    f"{settings.api_base}/entities/{entity['entity_id']}/states",
                    params={"limit": 10000},
                    timeout=3,
                )
            except (
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
                ApiException,
            ) as ex:
                states_resp = None
                self.statusbar.add_message(
                    f"Could not retrieve entity data from API: {ex.__class__.__name__}",
                    details=str(ex),
                )

        if states_resp and len(states_resp.json()):
            try:
                states_df = pd.DataFrame(states_resp.json())
                states_df["created"] = pd.to_datetime(states_df["created"])
                states_df["state"] = pd.to_numeric(states_df["state"])
                states_df = states_df.set_index("created")
                states_df = states_df.resample(timedelta(minutes=5)).mean()
                del states_df["id"]
                del states_df["entity_id"]

                self.ax.clear()
                states_df.plot(ax=self.ax, legend=False)
                self.ax.set_title(entity["sensor_name"])
                if entity["unit"]:
                    self.ax.set_ylabel(f"{entity['entity_name']} [{entity['unit']}]")
                else:
                    self.ax.set_ylabel(entity["entity_name"])

                self.canvas.draw()
            except ValueError as ex:
                self.ax.clear()
                self.canvas.draw()
                self.statusbar.add_message(
                    f"Could not convert data for {entity_name}: {ex.__class__.__name__}",
                    details=str(ex),
                )
        else:
            self.ax.clear()
            self.canvas.draw()

    def on_key_event(self, event):
        print("you pressed %s" % event.key)
        key_press_handler(event, self.canvas, self.toolbar)
