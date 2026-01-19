

import tkinter as tk
from tkinter import messagebox, Scrollbar, ttk
from tkinter.simpledialog import askstring
import os
import getpass
import subprocess
import tarfile
import json
from pathlib import Path
import platform
import shutil


IS_WINDOWS = os.name == 'nt'
PACKAGE_DIR = Path("C:/Packages") if IS_WINDOWS else Path("/packages")
INSTALL_DIR = Path("C:/DPMS/Installed") if IS_WINDOWS else Path("/opt")
INSTALL_DB = Path("installed_windows.json") if IS_WINDOWS else Path("/var/lib/dpms/installed.json")


def init_db():
    INSTALL_DB.parent.mkdir(parents=True, exist_ok=True)
    if not INSTALL_DB.exists():
        with open(INSTALL_DB, "w") as f:
            json.dump([], f)

def load_db():
    with open(INSTALL_DB) as f:
        return json.load(f)

def save_db(data):
    with open(INSTALL_DB, "w") as f:
        json.dump(data, f, indent=2)

def get_available_packages():
    if not PACKAGE_DIR.exists():
        return []
    return [f.stem for f in PACKAGE_DIR.glob("*.tar.xz")]

class DPMSGUI:
    def __init__(self, root):
        init_db()
        self.root = root
        self.root.title("DPMS Package Manager")
        self.root.geometry("650x540")
        self.selected_package = None
        self.dark_mode = False

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.update_listbox)

        # Search Bar
        self.search_entry = tk.Entry(root, textvariable=self.search_var, font=("Arial", 14))
        self.search_entry.pack(pady=10, padx=10, fill=tk.X)

        # Main Frame
        frame = tk.Frame(root)
        frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.scrollbar = Scrollbar(frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(frame, font=("Courier", 14), selectmode=tk.SINGLE, yscrollcommand=self.scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.listbox.yview)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        # Buttons
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)

        self.install_btn = tk.Button(btn_frame, text="Install", command=self.install_selected, font=("Arial", 12), width=10)
        self.install_btn.pack(side=tk.LEFT, padx=5)

        self.uninstall_btn = tk.Button(btn_frame, text="Uninstall", command=self.uninstall_selected, font=("Arial", 12), width=10)
        self.uninstall_btn.pack(side=tk.LEFT, padx=5)

        self.theme_btn = tk.Button(btn_frame, text="Toggle Theme", command=self.toggle_theme, font=("Arial", 12), width=12)
        self.theme_btn.pack(side=tk.LEFT, padx=5)

        # Progress Bar
        self.progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=10)

        self.update_listbox()
        self.auto_refresh()

    def auto_refresh(self):
        self.update_listbox()
        self.root.after(3000, self.auto_refresh)  # Refresh every 3 seconds

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        bg = "#1e1e1e" if self.dark_mode else "white"
        fg = "white" if self.dark_mode else "black"
        self.root.configure(bg=bg)
        self.listbox.configure(bg=bg, fg=fg)
        self.search_entry.configure(bg=bg, fg=fg, insertbackground=fg)
        self.install_btn.configure(bg=bg, fg=fg)
        self.uninstall_btn.configure(bg=bg, fg=fg)
        self.theme_btn.configure(bg=bg, fg=fg)

    def update_listbox(self, *args):
        search_term = self.search_var.get().lower()
        self.listbox.delete(0, tk.END)
        for pkg in get_available_packages():
            if search_term in pkg.lower():
                self.listbox.insert(tk.END, pkg)

    def on_select(self, event):
        selection = self.listbox.curselection()
        if selection:
            self.selected_package = self.listbox.get(selection[0])
        else:
            self.selected_package = None

    def ask_password(self):
        if IS_WINDOWS:
            return True, None
        username = getpass.getuser()
        password = askstring("Authentication Required", f"Password for {username}:", show="*")
        if not password:
            return False, None
        result = subprocess.run(
            ["sudo", "-kS", "true"],
            input=password + "\n",
            text=True,
            capture_output=True
        )
        if result.returncode != 0:
            messagebox.showerror("Authentication Failed", "Incorrect password.")
            return False, None
        return True, password

    def install_selected(self):
        if not self.selected_package:
            messagebox.showwarning("No Package Selected", "Please select a package to install.")
            return

        confirm = messagebox.askyesno("Confirm", f"Do you want to install '{self.selected_package}'?")
        if not confirm:
            return

        ok, password = self.ask_password()
        if not ok:
            return

        pkg_path = PACKAGE_DIR / f"{self.selected_package}.xz"
        target_path = INSTALL_DIR / self.selected_package.lower()

        try:
            target_path.mkdir(parents=True, exist_ok=True)
            self.simulate_progress()

            with tarfile.open(pkg_path, "r:xz") as tar:
                tar.extractall(path=target_path)

            installed = load_db()
            if self.selected_package not in installed:
                installed.append(self.selected_package)
                save_db(installed)

            messagebox.showinfo("Success", f"{self.selected_package} installed successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Installation failed: {e}")

    def uninstall_selected(self):
        if not self.selected_package:
            messagebox.showwarning("No Package Selected", "Please select a package to uninstall.")
            return

        confirm = messagebox.askyesno("Confirm", f"Do you want to uninstall '{self.selected_package}'?")
        if not confirm:
            return

        ok, password = self.ask_password()
        if not ok:
            return

        target_path = INSTALL_DIR / self.selected_package.lower()

        try:
            if target_path.exists():
                shutil.rmtree(target_path)

            installed = load_db()
            installed = [p for p in installed if p.lower() != self.selected_package.lower()]
            save_db(installed)

            messagebox.showinfo("Uninstalled", f"{self.selected_package} has been uninstalled.")
        except Exception as e:
            messagebox.showerror("Error", f"Uninstallation failed: {e}")

    def simulate_progress(self):
        self.progress["value"] = 0
        self.root.update_idletasks()
        for i in range(101):
            self.progress["value"] = i
            self.root.update_idletasks()
            self.root.after(5)

if __name__ == "__main__":
    root = tk.Tk()
    app = DPMSGUI(root)
    root.mainloop()
