import tkinter as tk

import db
from ui.login_window import LoginWindow
from ui.vault_window import VaultWindow

AUTO_LOCK_MS = 5 * 60 * 1000  # 5 minutes of inactivity
LOGIN_GEOMETRY = "420x320"
VAULT_GEOMETRY = "780x480"


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Encrypted Password Manager")
        self.conn = db.get_connection()
        self.fernet = None
        self.lock_timer = None
        self.current_frame = None

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.show_login()

    def show_login(self):
        self._cancel_auto_lock()
        self._unbind_activity()
        self._clear_frame()
        self.fernet = None
        self.root.geometry(LOGIN_GEOMETRY)
        self.current_frame = LoginWindow(self.root, self.conn, on_unlock=self._on_unlock)
        self.current_frame.pack(fill="both", expand=True)

    def _on_unlock(self, fernet):
        self.fernet = fernet
        self.show_vault()

    def show_vault(self):
        self._clear_frame()
        self.root.geometry(VAULT_GEOMETRY)
        self.current_frame = VaultWindow(self.root, self.conn, self.fernet, on_lock=self.lock)
        self.current_frame.pack(fill="both", expand=True)
        self._bind_activity()
        self._reset_auto_lock()

    def lock(self):
        self.show_login()

    def _bind_activity(self):
        for sequence in ("<Key>", "<Motion>", "<Button>"):
            self.root.bind_all(sequence, self._on_activity, add="+")

    def _unbind_activity(self):
        for sequence in ("<Key>", "<Motion>", "<Button>"):
            self.root.unbind_all(sequence)

    def _on_activity(self, _event=None):
        self._reset_auto_lock()

    def _reset_auto_lock(self):
        self._cancel_auto_lock()
        self.lock_timer = self.root.after(AUTO_LOCK_MS, self.lock)

    def _cancel_auto_lock(self):
        if self.lock_timer is not None:
            self.root.after_cancel(self.lock_timer)
            self.lock_timer = None

    def _clear_frame(self):
        if isinstance(self.current_frame, VaultWindow):
            self.current_frame.cancel_pending_jobs()
        if self.current_frame is not None:
            self.current_frame.destroy()
            self.current_frame = None

    def _on_close(self):
        self._cancel_auto_lock()
        if isinstance(self.current_frame, VaultWindow):
            self.current_frame.cancel_pending_jobs()
        self.conn.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
