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


class MyCheckboxFrame(customtkinter.CTkFrame):
    def __init__(self, master, title, values):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.values = values
        self.title = title
        self.checkboxes = []

        self.title = customtkinter.CTkLabel(
            self, text=self.title, fg_color="gray30", corner_radius=6
        )
        self.title.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")

        for i, value in enumerate(self.values):
            checkbox = customtkinter.CTkCheckBox(self, text=value)
            checkbox.grid(row=i + 1, column=0, padx=10, pady=(10, 0), sticky="w")
            self.checkboxes.append(checkbox)

    def get(self):
        checked_checkboxes = []
        for checkbox in self.checkboxes:
            if checkbox.get() == 1:
                checked_checkboxes.append(checkbox.cget("text"))
        return checked_checkboxes


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
        # self.attributes("-fullscreen", True)
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.checkbox_frame = MyCheckboxFrame(
            self, "Values", values=["value 1", "value 2", "value 3"]
        )
        self.checkbox_frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsew")
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

        self.button = customtkinter.CTkButton(
            self, text="my button", command=self.button_callback
        )
        self.button.grid(row=3, column=0, padx=10, pady=10, sticky="ew", columnspan=3)

    def button_callback(self):
        print("checkbox_frame:", self.checkbox_frame.get())
        print("radiobutton_frame:", self.radiobutton_frame.get())


app = App()
app.mainloop()
