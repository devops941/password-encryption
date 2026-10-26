import tkinter as tk
from tkinter import ttk

import crypto_utils
import db


class LoginWindow(tk.Frame):
    def __init__(self, parent, conn, on_unlock):
        super().__init__(parent, padx=24, pady=24)
        self.conn = conn
        self.on_unlock = on_unlock
        self.is_setup = not db.is_initialized(self.conn)
        self.confirm_entry = None
        self._build_ui()

    def _build_ui(self):
        title = "Create Master Password" if self.is_setup else "Unlock Vault"
        ttk.Label(self, text="Encrypted Password Manager", font=("Segoe UI", 16, "bold")).pack(pady=(0, 4))
        ttk.Label(self, text=title, font=("Segoe UI", 11)).pack(pady=(0, 16))

        form = ttk.Frame(self)
        form.pack(fill="x")

        ttk.Label(form, text="Master Password:").grid(row=0, column=0, sticky="w", pady=4)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(form, textvariable=self.password_var, show="*", width=28)
        self.password_entry.grid(row=0, column=1, pady=4, padx=(8, 0))
        self.password_entry.focus_set()

        if self.is_setup:
            ttk.Label(form, text="Confirm Password:").grid(row=1, column=0, sticky="w", pady=4)
            self.confirm_var = tk.StringVar()
            self.confirm_entry = ttk.Entry(form, textvariable=self.confirm_var, show="*", width=28)
            self.confirm_entry.grid(row=1, column=1, pady=4, padx=(8, 0))
            ttk.Label(
                self, text="This password is never stored. If you forget it, the vault cannot be recovered.",
                wraplength=340, foreground="#666",
            ).pack(pady=(12, 0))

        self.status_label = ttk.Label(self, text="", foreground="red", wraplength=340)
        self.status_label.pack(pady=(8, 0))

        action_text = "Create Vault" if self.is_setup else "Unlock"
        ttk.Button(self, text=action_text, command=self._submit).pack(pady=(16, 0))

        self.password_entry.bind("<Return>", lambda e: self._submit())
        if self.confirm_entry is not None:
            self.confirm_entry.bind("<Return>", lambda e: self._submit())

    def _submit(self):
        password = self.password_var.get()
        if self.is_setup:
            self._handle_setup(password)
        else:
            self._handle_login(password)

    def _handle_setup(self, password):
        if len(password) < 8:
            self.status_label.config(text="Master password must be at least 8 characters.")
            return
        if password != self.confirm_var.get():
            self.status_label.config(text="Passwords do not match.")
            return

        salt = crypto_utils.generate_salt()
        key = crypto_utils.derive_key(password, salt)
        fernet = crypto_utils.make_fernet(key)
        check_token = crypto_utils.create_check_token(fernet)
        db.save_master_record(self.conn, salt, check_token, crypto_utils.ITERATIONS)
        self.on_unlock(fernet)

    def _handle_login(self, password):
        record = db.load_master_record(self.conn)
        if record is None:
            self.status_label.config(text="Vault not initialized.")
            return
        salt, check_token, iterations = record
        key = crypto_utils.derive_key(password, salt, iterations)
        fernet = crypto_utils.make_fernet(key)
        if not crypto_utils.verify_check_token(fernet, check_token):
            self.status_label.config(text="Incorrect master password.")
            self.password_var.set("")
            return
        self.on_unlock(fernet)
