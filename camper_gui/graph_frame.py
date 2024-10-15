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


class GraphFrame(customtkinter.CTkFrame):
    def __init__(self, master, statusbar, api_sensors):
        super().__init__(master)
        self.statusbar = statusbar

        self.grid_columnconfigure(0, weight=1)

        f = Figure(figsize=(4, 4), dpi=100)
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
        current_tab = self.master.master.get()

        if current_tab == "History":
            entity_id = 7

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

        self.after(10000, self.update_plot)

    def on_key_event(self, event):
        print("you pressed %s" % event.key)
        key_press_handler(event, self.canvas, self.toolbar)
