import json
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent

def load_json(filename):
    try:
        with (DATA_DIR / filename).open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        messagebox.showerror("Missing file", f"Could not find {filename}. Put it beside index.py.")
        return []
    except json.JSONDecodeError:
        messagebox.showerror("Invalid JSON", f"{filename} is not valid JSON.")
        return []

class FamilyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Family Management")
        self.root.geometry("900x560")
        self.root.minsize(700, 420)

        self.families = load_json("family.json")
        self.members = load_json("member.json")
        self.medicines = load_json("medicine.json")
        self.groceries = load_json("groceries.json")
        self.current_family = None

        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=12)

        self.login_tab = ttk.Frame(self.tabs, padding=20)
        self.members_tab = ttk.Frame(self.tabs, padding=12)
        self.medicine_tab = ttk.Frame(self.tabs, padding=12)
        self.groceries_tab = ttk.Frame(self.tabs, padding=12)

        self.tabs.add(self.login_tab, text="Login")
        self.tabs.add(self.members_tab, text="Members 🔒")
        self.tabs.add(self.medicine_tab, text="Medicine 🔒")
        self.tabs.add(self.groceries_tab, text="Groceries 🔒")

        self.build_login()
        self.build_members()
        self.build_medicine()
        self.build_groceries()
        self.lock_tabs()

    def build_login(self):
        ttk.Label(self.login_tab, text="Family Management Login",
                  font=("Arial", 20, "bold")).pack(pady=(30, 8))
        ttk.Label(self.login_tab,
                  text="Enter your family name or family ID and password.").pack(pady=(0, 20))
        form = ttk.Frame(self.login_tab)
        form.pack()

        ttk.Label(form, text="Family name or ID:").grid(row=0, column=0, sticky="e", padx=8, pady=8)
        self.family_entry = ttk.Entry(form, width=32)
        self.family_entry.grid(row=0, column=1, padx=8, pady=8)

        ttk.Label(form, text="Family password:").grid(row=1, column=0, sticky="e", padx=8, pady=8)
        self.password_entry = ttk.Entry(form, width=32, show="*")
        self.password_entry.grid(row=1, column=1, padx=8, pady=8)
        self.password_entry.bind("<Return>", lambda event: self.login())

        ttk.Button(form, text="Log in", command=self.login).grid(
            row=2, column=0, columnspan=2, pady=14)
        ttk.Label(self.login_tab, text="Example accounts are in families.json.",
                  foreground="gray").pack(pady=10)

    def lock_tabs(self):
        for tab in (self.members_tab, self.medicine_tab, self.groceries_tab):
            self.tabs.tab(tab, state="disabled")
        self.tabs.select(self.login_tab)
        self.tabs.tab(self.members_tab, text="Members 🔒")
        self.tabs.tab(self.medicine_tab, text="Medicine 🔒")
        self.tabs.tab(self.groceries_tab, text="Groceries 🔒")

    def unlock_tabs(self):
        self.tabs.tab(self.members_tab, state="normal", text="Members")
        self.tabs.tab(self.medicine_tab, state="normal", text="Medicine")
        self.tabs.tab(self.groceries_tab, state="normal", text="Groceries")

    def login(self):
        entered = self.family_entry.get().strip().casefold()
        password = self.password_entry.get()
        if not entered or not password:
            messagebox.showwarning("Missing details", "Enter both family name/ID and password.")
            return

        family = next((f for f in self.families
                       if entered in (str(f.get("family_id", "")).casefold(),
                                      str(f.get("family_name", "")).casefold())
                       and password == str(f.get("family_password", ""))), None)
        if family is None:
            self.current_family = None
            self.lock_tabs()
            messagebox.showerror("Login failed", "Family name/ID or password is incorrect.")
            return

        self.current_family = family
        self.refresh_tables()
        self.unlock_tabs()
        self.tabs.select(self.members_tab)
        messagebox.showinfo("Login successful", f"Welcome, {family['family_name']}!")

    def make_table(self, parent, columns, headings):
        table = ttk.Treeview(parent, columns=columns, show="headings")
        for col, heading in zip(columns, headings):
            table.heading(col, text=heading)
            table.column(col, width=160, anchor="w")
        table.pack(fill="both", expand=True, pady=(8, 0))
        return table

    def build_members(self):
        ttk.Label(self.members_tab, text="Family Members",
                  font=("Arial", 16, "bold")).pack(anchor="w")
        self.members_table = self.make_table(
            self.members_tab, ("member_id", "member_name", "pin"),
            ("Member ID", "Member name", "4-digit PIN"))
        ttk.Label(self.members_tab,
                  text="Demo note: PINs are shown here; avoid exposing real PINs on shared screens.",
                  foreground="gray", wraplength=800).pack(anchor="w", pady=8)

    def build_medicine(self):
        ttk.Label(self.medicine_tab, text="Medicine List",
                  font=("Arial", 16, "bold")).pack(anchor="w")
        self.medicine_table = self.make_table(
            self.medicine_tab, ("medicine", "member", "left", "per_day"),
            ("Medicine", "Member", "Pills left", "Pills per day"))

    def build_groceries(self):
        ttk.Label(self.groceries_tab, text="Grocery List",
                  font=("Arial", 16, "bold")).pack(anchor="w")
        self.groceries_table = self.make_table(
            self.groceries_tab, ("status", "items"), ("Status", "Items"))
        ttk.Label(self.groceries_tab, text="Each row is a grocery stock category.",
                  foreground="gray").pack(anchor="w", pady=8)

    @staticmethod
    def clear_table(table):
        for item in table.get_children():
            table.delete(item)

    def refresh_tables(self):
        family_id = self.current_family["family_id"]
        family_members = [m for m in self.members if m.get("family_id") == family_id]
        member_names = {m.get("member_id"): m.get("member_name", "Unknown")
                        for m in family_members}

        self.clear_table(self.members_table)
        for m in family_members:
            self.members_table.insert("", "end", values=(
                m.get("member_id", ""), m.get("member_name", ""), m.get("pin", "")))

        self.clear_table(self.medicine_table)
        for med in self.medicines:
            if med.get("family_id") == family_id:
                self.medicine_table.insert("", "end", values=(
                    med.get("medicine_name", ""),
                    member_names.get(med.get("member_id"), "Unknown member"),
                    med.get("pills_left", 0), med.get("pills_per_day", 0)))

        self.clear_table(self.groceries_table)
        grocery = next((g for g in self.groceries if g.get("family_id") == family_id),
                       {"stock": [], "out_of_stock": []})
        self.groceries_table.insert("", "end", values=(
            "In stock", ", ".join(grocery.get("stock", [])) or "None"))
        self.groceries_table.insert("", "end", values=(
            "Out of stock", ", ".join(grocery.get("out_of_stock", [])) or "None"))

if __name__ == "__main__":
    root = tk.Tk()
    app = FamilyApp(root)
    root.mainloop()
