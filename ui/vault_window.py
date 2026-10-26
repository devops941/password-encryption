import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import crypto_utils
import db
from ui.entry_dialog import EntryDialog

CLIPBOARD_CLEAR_MS = 20_000


class VaultWindow(tk.Frame):
    def __init__(self, parent, conn, fernet, on_lock):
        super().__init__(parent, padx=12, pady=12)
        self.parent = parent
        self.conn = conn
        self.fernet = fernet
        self.on_lock = on_lock
        self.clipboard_job = None
        self._build_ui()
        self.refresh_entries()

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 8))
        ttk.Label(top, text="Vault", font=("Segoe UI", 14, "bold")).pack(side="left")
        ttk.Button(top, text="Lock Now", command=self.on_lock).pack(side="right")
        ttk.Button(top, text="Backup...", command=self._backup).pack(side="right", padx=(0, 8))

        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(search_frame, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.refresh_entries())
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side="left", fill="x", expand=True, padx=(8, 8))
        ttk.Button(search_frame, text="Add Entry", command=self._add_entry).pack(side="right")

        columns = ("site", "username", "updated_at")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("site", text="Site")
        self.tree.heading("username", text="Username")
        self.tree.heading("updated_at", text="Last Updated")
        self.tree.column("site", width=220)
        self.tree.column("username", width=220)
        self.tree.column("updated_at", width=160)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self._edit_selected())

        btns = ttk.Frame(self)
        btns.pack(fill="x", pady=(8, 0))
        ttk.Button(btns, text="Copy Password", command=self._copy_selected).pack(side="left")
        ttk.Button(btns, text="View / Edit", command=self._edit_selected).pack(side="left", padx=8)
        ttk.Button(btns, text="Delete", command=self._delete_selected).pack(side="left")

        self.status_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.status_var, foreground="#1e8449").pack(anchor="w", pady=(8, 0))

    def refresh_entries(self):
        query = self.search_var.get().strip()
        rows = db.search_entries(self.conn, query) if query else db.get_all_entries(self.conn)
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            entry_id, site, username, _password_enc, _notes_enc, _created_at, updated_at = row
            self.tree.insert("", "end", iid=str(entry_id), values=(site, username or "", updated_at))

    def _selected_entry_id(self):
        selection = self.tree.selection()
        if not selection:
            return None
        return int(selection[0])

    def _get_entry_row(self, entry_id):
        for row in db.get_all_entries(self.conn):
            if row[0] == entry_id:
                return row
        return None

    def _add_entry(self):
        dialog = EntryDialog(self.parent, title="Add Entry")
        self.wait_window(dialog)
        if dialog.result is None:
            return
        site, username, password, notes = dialog.result
        password_enc = crypto_utils.encrypt_text(self.fernet, password)
        notes_enc = crypto_utils.encrypt_text(self.fernet, notes)
        db.add_entry(self.conn, site, username, password_enc, notes_enc)
        self.refresh_entries()
        self.status_var.set(f"Added entry for {site}.")

    def _edit_selected(self):
        entry_id = self._selected_entry_id()
        if entry_id is None:
            messagebox.showinfo("No selection", "Select an entry first.")
            return
        row = self._get_entry_row(entry_id)
        if row is None:
            return
        _, site, username, password_enc, notes_enc, _, _ = row
        password = crypto_utils.decrypt_text(self.fernet, password_enc)
        notes = crypto_utils.decrypt_text(self.fernet, notes_enc)

        dialog = EntryDialog(self.parent, title="Edit Entry", site=site, username=username or "", password=password, notes=notes)
        self.wait_window(dialog)
        if dialog.result is None:
            return
        site, username, password, notes = dialog.result
        password_enc = crypto_utils.encrypt_text(self.fernet, password)
        notes_enc = crypto_utils.encrypt_text(self.fernet, notes)
        db.update_entry(self.conn, entry_id, site, username, password_enc, notes_enc)
        self.refresh_entries()
        self.status_var.set(f"Updated entry for {site}.")

    def _delete_selected(self):
        entry_id = self._selected_entry_id()
        if entry_id is None:
            messagebox.showinfo("No selection", "Select an entry first.")
            return
        values = self.tree.item(str(entry_id), "values")
        site = values[0] if values else "this entry"
        if messagebox.askyesno("Confirm Delete", f"Delete the entry for {site}?"):
            db.delete_entry(self.conn, entry_id)
            self.refresh_entries()
            self.status_var.set(f"Deleted entry for {site}.")

    def _copy_selected(self):
        entry_id = self._selected_entry_id()
        if entry_id is None:
            messagebox.showinfo("No selection", "Select an entry first.")
            return
        row = self._get_entry_row(entry_id)
        if row is None:
            return
        password = crypto_utils.decrypt_text(self.fernet, row[3])

        self.clipboard_clear()
        self.clipboard_append(password)
        self.status_var.set("Password copied. Clipboard clears in 20 seconds.")

        if self.clipboard_job is not None:
            self.after_cancel(self.clipboard_job)
        self.clipboard_job = self.after(CLIPBOARD_CLEAR_MS, self._clear_clipboard)

    def _clear_clipboard(self):
        try:
            self.clipboard_clear()
        except tk.TclError:
            pass
        self.clipboard_job = None
        self.status_var.set("Clipboard cleared.")

    def _backup(self):
        dest = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("SQLite Database", "*.db")],
            title="Backup encrypted vault",
            initialfile="vault_backup.db",
        )
        if not dest:
            return
        self.conn.commit()
        shutil.copyfile(db.DB_PATH, dest)
        messagebox.showinfo("Backup complete", f"Encrypted vault backed up to:\n{dest}")

    def cancel_pending_jobs(self):
        if self.clipboard_job is not None:
            self.after_cancel(self.clipboard_job)
            self.clipboard_job = None
