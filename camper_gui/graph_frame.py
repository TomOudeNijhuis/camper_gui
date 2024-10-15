import customtkinter
import requests
import matplotlib

matplotlib.use("TkAgg")

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import (
    NavigationToolbar2Tk as NavigationToolbar2TkAgg,
)
from matplotlib.backend_bases import key_press_handler
import pandas as pd


class ApiException(Exception):
    pass


class EntityFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master, statusbar):
        super().__init__(master)
        self.statusbar = statusbar

        self.checkboxes = []

    def add(self, text):
        self.checkboxes.append(customtkinter.CTkCheckBox(self, text=text))
        self.checkboxes[-1].grid(
            row=len(self.checkboxes) - 1,
            column=0,
            padx=10,
            pady=(10, 0),
            sticky="w",
        )

    def get(self):
        entity_names = []
        for cb in self.checkboxes:
            if cb.get():
                entity_names.append(cb.cget("text"))

        return entity_names


class GraphFrame(customtkinter.CTkFrame):
    def __init__(self, master, statusbar, api_sensors):
        super().__init__(master)
        self.statusbar = statusbar

        self.grid_columnconfigure((0, 1), weight=1)

        f = Figure(figsize=(4, 4), dpi=100)
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
                entities_resp = requests.get(
                    f"http://localhost:8000/sensors/{self.sensor_id}/entities",
                    timeout=3,
                )
                for entity in entities_resp.json():
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

        self.update_plot()

    def update_plot(self):
        current_tab = self.master.master.get()
        entity_id = None

        if current_tab == "History":
            entity_names = self.entity_frame.get()
            if entity_names:
                entity_id = self.entity_id_by_name[entity_names[0]]

            if entity_id is None:
                states_resp = None
            else:
                try:
                    states_resp = requests.get(
                        f"http://localhost:8000/entities/{entity_id}/states",
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
                states_df = pd.DataFrame(states_resp.json())
                states_df["created"] = pd.to_datetime(states_df["created"])
                states_df["state"] = pd.to_numeric(states_df["state"])
                states_df = states_df.set_index("created")
                del states_df["id"]

                self.ax.clear()
                states_df.plot(ax=self.ax)
                self.canvas.draw()
            else:
                self.ax.clear()
                self.canvas.draw()
        else:
            self.ax.clear()
            self.canvas.draw()

        self.after(5000, self.update_plot)

    def on_key_event(self, event):
        print("you pressed %s" % event.key)
        key_press_handler(event, self.canvas, self.toolbar)
