import tkinter as tk
from tkinter import ttk

import generator

STRENGTH_COLORS = {"Weak": "#c0392b", "Medium": "#d68910", "Strong": "#1e8449", "Very Strong": "#117a65"}


class EntryDialog(tk.Toplevel):
    def __init__(self, parent, title="Entry", site="", username="", password="", notes=""):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result = None
        self.transient(parent)
        self.grab_set()

        self._build_ui(site, username, password, notes)
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.bind("<Escape>", lambda e: self._cancel())

    def _build_ui(self, site, username, password, notes):
        pad = {"padx": 10, "pady": 6}
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Site / App:").grid(row=0, column=0, sticky="w", **pad)
        self.site_var = tk.StringVar(value=site)
        ttk.Entry(frame, textvariable=self.site_var, width=36).grid(row=0, column=1, columnspan=2, sticky="we", **pad)

        ttk.Label(frame, text="Username:").grid(row=1, column=0, sticky="w", **pad)
        self.username_var = tk.StringVar(value=username)
        ttk.Entry(frame, textvariable=self.username_var, width=36).grid(row=1, column=1, columnspan=2, sticky="we", **pad)

        ttk.Label(frame, text="Password:").grid(row=2, column=0, sticky="w", **pad)
        self.password_var = tk.StringVar(value=password)
        self.password_var.trace_add("write", lambda *a: self._update_strength())
        self.show_password = tk.BooleanVar(value=False)
        self.password_entry = ttk.Entry(frame, textvariable=self.password_var, show="*", width=28)
        self.password_entry.grid(row=2, column=1, sticky="we", **pad)
        ttk.Checkbutton(frame, text="Show", variable=self.show_password, command=self._toggle_show).grid(
            row=2, column=2, sticky="w"
        )

        self.strength_var = tk.StringVar(value="")
        self.strength_label = ttk.Label(frame, textvariable=self.strength_var)
        self.strength_label.grid(row=3, column=1, sticky="w", padx=10)

        gen_frame = ttk.LabelFrame(frame, text="Password Generator")
        gen_frame.grid(row=4, column=0, columnspan=3, sticky="we", pady=(8, 8), padx=10)

        ttk.Label(gen_frame, text="Length:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.length_var = tk.IntVar(value=16)
        ttk.Spinbox(gen_frame, from_=8, to=64, textvariable=self.length_var, width=5).grid(row=0, column=1, sticky="w")

        self.use_upper = tk.BooleanVar(value=True)
        self.use_lower = tk.BooleanVar(value=True)
        self.use_digits = tk.BooleanVar(value=True)
        self.use_symbols = tk.BooleanVar(value=True)
        ttk.Checkbutton(gen_frame, text="Upper", variable=self.use_upper).grid(row=0, column=2, padx=4)
        ttk.Checkbutton(gen_frame, text="Lower", variable=self.use_lower).grid(row=0, column=3, padx=4)
        ttk.Checkbutton(gen_frame, text="Digits", variable=self.use_digits).grid(row=0, column=4, padx=4)
        ttk.Checkbutton(gen_frame, text="Symbols", variable=self.use_symbols).grid(row=0, column=5, padx=4)
        ttk.Button(gen_frame, text="Generate", command=self._generate).grid(row=0, column=6, padx=8)

        ttk.Label(frame, text="Notes:").grid(row=5, column=0, sticky="nw", **pad)
        self.notes_text = tk.Text(frame, width=36, height=4)
        self.notes_text.grid(row=5, column=1, columnspan=2, sticky="we", **pad)
        if notes:
            self.notes_text.insert("1.0", notes)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=6, column=0, columnspan=3, pady=(10, 0))
        ttk.Button(btn_frame, text="Save", command=self._save).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Cancel", command=self._cancel).pack(side="left", padx=6)

        self._update_strength()

    def _toggle_show(self):
        self.password_entry.config(show="" if self.show_password.get() else "*")

    def _generate(self):
        try:
            pwd = generator.generate_password(
                length=self.length_var.get(),
                use_upper=self.use_upper.get(),
                use_lower=self.use_lower.get(),
                use_digits=self.use_digits.get(),
                use_symbols=self.use_symbols.get(),
            )
        except ValueError as exc:
            self.strength_var.set(str(exc))
            self.strength_label.config(foreground="#c0392b")
            return
        self.password_var.set(pwd)
        self.show_password.set(True)
        self._toggle_show()

    def _update_strength(self):
        password = self.password_var.get()
        if not password:
            self.strength_var.set("")
            return
        strength = generator.rate_strength(password)
        self.strength_label.config(foreground=STRENGTH_COLORS.get(strength, "black"))
        self.strength_var.set(f"Strength: {strength}")

    def _save(self):
        site = self.site_var.get().strip()
        if not site:
            self.strength_var.set("Site name is required.")
            self.strength_label.config(foreground="#c0392b")
            return
        username = self.username_var.get().strip()
        password = self.password_var.get()
        notes = self.notes_text.get("1.0", "end").strip()
        self.result = (site, username, password, notes)
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()
