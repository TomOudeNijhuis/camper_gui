import customtkinter
import subprocess
from datetime import datetime

MAX_MESSAGES = 14


class StatusBarFrame(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=11)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.message_list = []

        self.message_text = customtkinter.CTkLabel(
            self,
            text="No messages",
            fg_color="gray30",
            justify="left",
            anchor="w",
            font=("font2", 15),
            padx=10,
            text_color="black",
        )
        self.exit_button = customtkinter.CTkButton(
            self,
            text="Exit",
            command=self.exit_callback,
            height=45,
            text_color="black",
            font=("font2", 15),
        )
        self.screen_button = customtkinter.CTkButton(
            self,
            text="Screen",
            command=self.screen_off_callback,
            height=45,
            text_color="black",
            font=("font2", 15),
        )

        self.message_text.grid(row=0, column=0, padx=5, pady=(10, 0), sticky="nsew")
        self.screen_button.grid(row=0, column=1, padx=5, pady=(10, 0), sticky="nsew")
        self.exit_button.grid(row=0, column=2, padx=5, pady=(10, 0), sticky="nsew")

    def exit_callback(self):
        self.master.destroy()

    def screen_off_callback(self):
        subprocess.run(["xset", "dpms", "force", "off"])

    def add_message(self, message, state="error", details=None):
        self.message_list.insert(
            0,
            {
                "stamp": datetime.now(),
                "message": message,
                "state": state,
                "details": details,
            },
        )

        if len(self.message_list) > MAX_MESSAGES:
            self.message_list = self.message_list[0:10]

        active_message = self.message_list[0]

        if active_message["state"] == "info":
            message_color = "green"
        elif active_message["state"] == "warning":
            message_color = "orange"
        else:
            message_color = "red"

        self.message_text.configure(
            text=f"{active_message['stamp'].strftime('%Y-%m-%d %H:%M')}: {active_message['message']}",
            fg_color=message_color,
        )


class StatusMessagesFrame(customtkinter.CTkFrame):
    def __init__(self, master, statusbar):
        super().__init__(master)
        self.statusbar = statusbar

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=7)

        self.stamp_labels = []
        self.messages = []
        self.states = []

        for i in range(0, MAX_MESSAGES):
            self.grid_rowconfigure(i, weight=1)
            self.stamp_labels.append(
                customtkinter.CTkLabel(
                    self,
                    fg_color="transparent",
                    justify="left",
                    padx=5,
                    anchor="w",
                    text="",
                ),
            )
            self.stamp_labels[i].grid(row=i, column=0, padx=10, pady=2, sticky="nesw")

            self.messages.append(
                customtkinter.CTkLabel(
                    self,
                    fg_color="transparent",
                    justify="left",
                    padx=5,
                    anchor="w",
                    text="",
                ),
            )
            self.messages[i].grid(row=i, column=1, padx=10, pady=2, sticky="nesw")

        self.update_messages()

    def update_messages(self):
        current_tab = self.master.master.get()

        if current_tab == "Messages":
            for i in range(0, MAX_MESSAGES):
                if len(self.statusbar.message_list) > i:
                    if self.statusbar.message_list[i]["state"] == "info":
                        message_color = "green"
                    elif self.statusbar.message_list[i]["state"] == "warning":
                        message_color = "orange"
                    else:
                        message_color = "red"

                    stamp_str = self.statusbar.message_list[i]["stamp"].strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    text_str = self.statusbar.message_list[i]["message"]
                else:
                    message_color = "transparent"
                    stamp_str = ""
                    text_str = ""

                self.stamp_labels[i].configure(text=stamp_str, fg_color=message_color)
                self.messages[i].configure(text=text_str, fg_color=message_color)

            if len(self.statusbar.message_list) == 0:
                self.messages[0].configure(
                    text="Currently there are no messages", fg_color="transparent"
                )

        self.after(5000, self.update_messages)
