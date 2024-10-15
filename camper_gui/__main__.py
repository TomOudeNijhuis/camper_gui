import customtkinter
import platform
import requests

from camper_interface_frame import CamperInterfaceFrame
from graph_frame import GraphFrame
from statusbar_frame import StatusBarFrame


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Camper GUI")
        self.geometry("1024x600")

        if platform.machine() == "x86_64":
            pass
        else:
            self.attributes("-fullscreen", True)

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(0, weight=1)

        tabview = customtkinter.CTkTabview(master=self)
        tabview.pack(padx=5, pady=5)
        tabview._segmented_button.configure(font=("font2", 15))
        tabview.add("Status")
        tabview.add("History")
        tabview.add("Messages")

        self.statusbar_frame = StatusBarFrame(self)

        try:
            sensors_resp = requests.get(f"http://localhost:8000/sensors")
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
            tabview.tab("Status"), self.statusbar_frame, api_sensors
        )
        self.graph_frame = GraphFrame(
            tabview.tab("History"), self.statusbar_frame, api_sensors
        )

        tabview.grid(row=0, column=0, padx=5, pady=0, sticky="nsew", columnspan=2)
        self.camper_interface_frame.grid(
            row=1, column=0, padx=10, pady=(10, 0), sticky="nsew"
        )
        self.graph_frame.grid(
            row=1, column=1, padx=(0, 10), pady=(10, 0), sticky="nsew"
        )
        self.statusbar_frame.grid(
            row=2, column=0, padx=(0, 0), pady=(10, 0), sticky="nsew", columnspan=2
        )


app = App()
app.mainloop()
