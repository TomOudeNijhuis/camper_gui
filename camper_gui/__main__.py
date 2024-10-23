import customtkinter
import platform
import requests

from camper_interface_frame import CamperInterfaceFrame
from temperature_frame import TemperatureFrame
from graph_frame import GraphFrame
from status_frames import StatusBarFrame, StatusMessagesFrame
from power_frame import PowerFrame
from config import settings


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Camper GUI")
        self.geometry("1024x600")

        if platform.machine() == "x86_64":
            pass
        else:
            self.attributes("-fullscreen", True)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.tabview = customtkinter.CTkTabview(
            master=self, command=self.main_tab_changed
        )
        self.tabview._segmented_button.configure(font=("font2", 15))
        self.tabview.add("Status")
        self.tabview.add("History")
        self.tabview.add("Messages")

        self.statusbar_frame = StatusBarFrame(self)

        try:
            sensors_resp = requests.get(f"{settings.api_base}/sensors")
            api_sensors = sensors_resp.json()
        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ) as ex:
            api_sensors = []
            self.statusbar_frame.add_message(
                f"Could not communicatie with API: {ex.__class__.__name__}",
                details=str(ex),
            )

        self.camper_interface_frame = CamperInterfaceFrame(
            self.tabview.tab("Status"), self.statusbar_frame, api_sensors
        )
        self.power_frame = PowerFrame(
            self.tabview.tab("Status"), self.statusbar_frame, api_sensors
        )
        self.temperture_frame = TemperatureFrame(
            self.tabview.tab("Status"), self.statusbar_frame, api_sensors
        )
        self.graph_frame = GraphFrame(
            self.tabview.tab("History"), self.statusbar_frame, api_sensors
        )
        self.status_messages_frame = StatusMessagesFrame(
            self.tabview.tab("Messages"), self.statusbar_frame
        )
        self.tabview.grid(row=0, column=0, padx=5, pady=0, sticky="nsew")

        self.tabview.tab("Status").grid_columnconfigure((0, 1), weight=1)
        self.tabview.tab("Status").grid_rowconfigure(1, weight=1)
        self.tabview.tab("History").grid_columnconfigure(0, weight=1)
        self.tabview.tab("History").grid_rowconfigure(1, weight=1)
        self.tabview.tab("Messages").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Messages").grid_rowconfigure(1, weight=1)

        self.camper_interface_frame.grid(
            row=1, column=0, padx=10, pady=(10, 0), sticky="nsew", rowspan=2
        )
        self.power_frame.grid(row=1, column=1, padx=10, pady=(10, 0), sticky="nsew")
        self.temperture_frame.grid(
            row=2, column=1, padx=10, pady=(10, 0), sticky="nsew"
        )
        self.graph_frame.grid(
            row=1, column=0, padx=(0, 10), pady=(10, 0), sticky="nsew"
        )
        self.status_messages_frame.grid(
            row=1, column=0, padx=(0, 0), pady=(10, 0), sticky="nsew"
        )
        self.statusbar_frame.grid(
            row=3, column=0, padx=(0, 0), pady=(10, 0), sticky="nsew"
        )

    def main_tab_changed(self):
        current_tab = self.tabview.get()

        match current_tab:
            case "Status":
                self.camper_interface_frame.update_states()
                self.power_frame.update_states()
            case "History":
                self.graph_frame.update_plot()
            case "Messages":
                self.status_messages_frame.update_messages()
            case _:
                raise Exception(f"Unknown tab {current_tab}")


app = App()
app.mainloop()
