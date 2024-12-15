import customtkinter
import tkinter
import requests
import matplotlib

matplotlib.use("TkAgg")

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
import pandas as pd

from config import settings


class ApiException(Exception):
    pass


class EntityFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master, statusbar, click_callback=None):
        super().__init__(master)
        self.statusbar = statusbar
        self.radio_var = tkinter.StringVar(value=None)
        self.radiobuttons = []
        self.click_callback = click_callback

    def _clicked(self):
        if self.click_callback:
            self.click_callback()

    def add(self, text):
        self.radiobuttons.append(
            customtkinter.CTkRadioButton(
                self,
                text=text.replace("_", " "),
                variable=self.radio_var,
                value=text,
                command=self._clicked,
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

    def reset(self):
        self.radio_var.set(-1)


class GraphFrame(customtkinter.CTkFrame):
    def __init__(self, master, statusbar, api_sensors, executor):
        super().__init__(master)
        self.statusbar = statusbar
        self.executor = executor

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)

        f = Figure(figsize=(4, 4.7), dpi=100)
        self.ax = f.add_subplot(111)
        self.plot_x = []
        self.plot_y = []

        self.canvas = FigureCanvasTkAgg(f, self)

        self.canvas.draw()
        self.canvas.get_tk_widget().grid(
            row=0, column=1, padx=10, pady=2, sticky="ew", columnspan=1
        )
        self.entity_id_by_name = {}
        self.entity_frame = EntityFrame(
            self, self.statusbar, self._change_plot_callback
        )
        self.entity_frame.grid(
            row=0, column=0, padx=10, pady=2, sticky="nsew", columnspan=1
        )

        for sensor in api_sensors:
            for entity in sensor["entities"]:
                self.entity_id_by_name[f"{sensor['name']}_{entity['name']}"] = {
                    "entity_id": entity["id"],
                    "entity_name": entity["name"],
                    "unit": entity["unit"],
                    "sensor_id": entity["sensor_id"],
                    "sensor_name": sensor["name"],
                }

        self.checkboxes = []

        for k, v in self.entity_id_by_name.items():
            self.entity_frame.add(k)

        # self.update_plot_runner()

    def _change_plot_callback(self):
        self.executor.submit(self.update_plot)

    def update_plot_runner(self):
        current_tab = self.master.master.get()

        if current_tab == "History":
            self.executor.submit(self.update_plot)
        else:
            self.ax.clear()
            self.canvas.draw()

        self.after(5000, self.update_plot_runner)

    def reset(self):
        self.entity_frame.reset()
        self.ax.clear()
        self.canvas.draw()

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

                try:
                    states_df["state"] = pd.to_numeric(states_df["state"])
                    is_numeric = True
                except ValueError:
                    is_numeric = False

                if is_numeric is False:
                    # Handle string states
                    states_df["state"] = states_df["state"].astype(str)
                    states_df = states_df.set_index("created")

                    # Plot string states over time
                    self.ax.clear()
                    for state in states_df["state"].unique():
                        state_df = states_df[states_df["state"] == state]
                        self.ax.plot(
                            state_df.index, [state] * len(state_df), "o", label=state
                        )

                    self.ax.set_title(entity["sensor_name"])
                    self.ax.set_ylabel(entity["entity_name"])
                    self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=24))
                    self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))

                    self.ax.grid()
                    self.canvas.draw()
                else:
                    states_df["state"] = pd.to_numeric(states_df["state"])
                    states_df = states_df.set_index("created")

                    # Resample to 8-hour intervals and calculate min, max, and mean
                    hourly_df = states_df.resample("4h").agg(["min", "max", "mean"])

                    # Plot the average values
                    self.ax.clear()
                    hourly_df["state"]["mean"].plot(
                        ax=self.ax, label="Avg", color="green"
                    )
                    self.ax.fill_between(
                        hourly_df.index,
                        hourly_df["state"]["min"],
                        hourly_df["state"]["max"],
                        color="gray",
                        alpha=0.2,
                    )

                    # Plot the min and max values as darker gray lines
                    hourly_df["state"]["min"].plot(
                        ax=self.ax, label="Min", color="darkgray", linestyle="--"
                    )
                    hourly_df["state"]["max"].plot(
                        ax=self.ax, label="Max", color="darkgray", linestyle="--"
                    )

                    self.ax.set_title(entity["sensor_name"])
                    self.ax.grid()

                    if entity["unit"]:
                        self.ax.set_ylabel(
                            f"{entity['entity_name']} [{entity['unit']}]"
                        )
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
            except Exception as ex:
                self.ax.clear()
                self.canvas.draw()
                self.statusbar.add_message(
                    f"Could not plot data for {entity_name}: {ex.__class__.__name__}",
                    details=str(ex),
                )
        else:
            self.ax.clear()
            self.canvas.draw()
