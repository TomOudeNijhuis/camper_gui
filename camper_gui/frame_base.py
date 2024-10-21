import customtkinter


class FrameBase(customtkinter.CTkFrame):
    def _add_title(self, label_text, row=0, column=0, columnspan=2):
        title_label = customtkinter.CTkLabel(
            self, text=label_text, fg_color="gray30", corner_radius=6
        )
        title_label.grid(
            row=row,
            column=column,
            padx=10,
            pady=(10, 0),
            sticky="ew",
            columnspan=columnspan,
        )

        return title_label

    def _add_entry(self, label_text, row, column, columnspan=1):
        var = customtkinter.StringVar()

        var_label = customtkinter.CTkLabel(
            self, text=label_text, fg_color="transparent", justify="left"
        )
        var_label.grid(
            row=row,
            column=column,
            padx=10,
            pady=(5, 0),
            sticky="sw",
            columnspan=columnspan,
        )

        var_entry = customtkinter.CTkEntry(
            self,
            textvariable=var,
            text_color="black",
            font=("font2", 15),
            height=45,
            state="disabled",
        )
        var_entry.grid(
            row=row + 1,
            column=column,
            padx=10,
            pady=(0, 5),
            sticky="ew",
            columnspan=columnspan,
        )

        return var, var_label, var_entry

    def _add_button(self, button_text, row, column, columnspan=1, **kwargs):
        button = customtkinter.CTkButton(
            self,
            text=button_text,
            height=45,
            text_color_disabled="black",
            font=("font2", 15),
            **kwargs
        )
        button.grid(
            row=row, column=column, padx=10, pady=10, sticky="ew", columnspan=columnspan
        )

        return button

    def _add_progress(self, label_text, row, column, columnspan=2):
        var_label = customtkinter.CTkLabel(
            self, text=label_text, fg_color="transparent", justify="left"
        )
        var_label.grid(
            row=row, column=column, padx=10, pady=2, sticky="sw", columnspan=columnspan
        )
        var_progress = customtkinter.CTkProgressBar(self, orientation="horizontal")
        var_progress.grid(
            row=row + 1,
            column=column,
            padx=10,
            pady=2,
            sticky="ew",
            columnspan=columnspan,
        )

        return var_label, var_progress
