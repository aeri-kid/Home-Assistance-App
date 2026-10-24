import json
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent

MEMBERS_FILE = DATA_DIR / "member.json"

AVATARS = [
    "👤", "👶🏻", "👧🏻", "🧒🏻",
    "👱🏻‍♀️", "👱🏻", "👵🏻", "🧓🏻"
]

BG = "#141414"
CARD = "#292929"
ACCENT = "#E50914"

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

def save_json(filename, data):
    path = DATA_DIR / filename
    temp_path = path.with_suffix(path.suffix + ".tmp")

    with temp_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    temp_path.replace(path)

class FamilyApp:
    def render_profiles(self):
        if not hasattr(self, "profile_area"):
            return

        for widget in self.profile_area.winfo_children():
            widget.destroy()

        if self.current_family is None:
            return

        family_id = str(self.current_family.get("family_id", ""))
        family_members = [
            m for m in self.members
            if str(m.get("family_id")) == family_id
        ]

        self.dragged_member = None

        for index, member in enumerate(family_members):
            row, col = divmod(index, 4)

            card = tk.Frame(
                self.profile_area,
                bg=BG,
                cursor="hand2"
            )
            card.grid(
                row=row,
                column=col,
                padx=10,
                pady=10,
                sticky="n"
            )

            avatar = tk.Label(
                card,
                text=member.get("avatar", "👤"),
                bg=CARD,
                fg="white",
                font=("Arial", 36),
                width=4,
                height=2
            )
            avatar.pack()

            name = tk.Label(
                card,
                text=member.get("member_name", "Member"),
                bg=BG,
                fg="white",
                font=("Arial", 10),
                wraplength=110
            )
            name.pack(pady=6)

            for widget in (card, avatar, name):
                widget.bind(
                    "<ButtonPress-1>",
                    lambda event, m=member: self.start_drag(m)
                )
                widget.bind("<B1-Motion>", self.drag_motion)
                widget.bind("<ButtonRelease-1>", self.finish_drag)

        add_card = tk.Frame(
            self.profile_area,
            bg=BG,
            cursor="hand2"
        )
        add_row, add_col = divmod(len(family_members), 4)
        add_card.grid(
            row=add_row,
            column=add_col,
            padx=10,
            pady=10
        )

        plus = tk.Label(
            add_card,
            text="+",
            bg=CARD,
            fg="white",
            font=("Arial", 36),
            width=4,
            height=2
        )
        plus.pack()

        tk.Label(
            add_card,
            text="Add Profile",
            bg=BG,
            fg="white"
        ).pack(pady=6)

        for widget in (add_card, plus):
            widget.bind("<Button-1>", lambda event: self.add_member_dialog())

    def start_drag(self, member):
        self.dragged_member = member
        self.trash.configure(bg="#7A1515")

    def drag_motion(self, event):
        x, y = self.root.winfo_pointerxy()
        target = self.root.winfo_containing(x, y)

        if target is self.trash:
            self.trash.configure(bg="#7A1515")
        else:
            self.trash.configure(bg=CARD)

    def finish_drag(self, event):
        if not self.dragged_member:
            return

        x, y = self.root.winfo_pointerxy()
        target = self.root.winfo_containing(x, y)

        if target is self.trash:
            self.drop_on_trash(event)

        self.dragged_member = None
        self.trash.configure(bg=CARD)

    def drop_on_trash(self, event):
        member = getattr(self, "dragged_member", None)

        if member is None:
            return

        name = member.get("member_name", "this member")

        confirmed = messagebox.askyesno(
            "Delete profile?",
            f"Are you sure you want to delete {name}?"
        )

        if not confirmed:
            self.dragged_member = None
            return

        member_id = member.get("member_id")

        self.members = [
            m for m in self.members
            if not (
                str(m.get("family_id")) == str(self.current_family["family_id"])
                and str(m.get("member_id")) == str(member_id)
            )
        ]

        try:
            save_json("member.json", self.members)
        except OSError as exc:
            self.members = load_json("member.json")
            messagebox.showerror(
                "Save failed",
                f"Could not save the updated member list:\n{exc}"
            )
            self.render_profiles()
            return

        self.dragged_member = None
        self.refresh_tables()
        self.render_profiles()

        messagebox.showinfo(
            "Profile deleted",
            f"{name} was deleted successfully."
        )

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
        self.render_profiles()

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
        self.render_profiles()
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
        header = tk.Frame(self.members_tab)
        header.pack(fill="x", pady=(0, 12))

        ttk.Label(
            header,
            text="Who's in your family?",
            font=("Arial", 22, "bold")
        ).pack(anchor="w")

        ttk.Label(
            header,
            text="Select a profile, add a member, or drag a profile to the trash."
        ).pack(anchor="w", pady=5)

        self.profile_area = tk.Frame(self.members_tab, bg=BG)
        self.profile_area.pack(fill="both", expand=True)

        self.trash = tk.Label(
            self.members_tab,
            text="🗑️  Drag a profile here to delete",
            bg=CARD,
            fg="white",
            font=("Arial", 12, "bold"),
            pady=15
        )
        self.trash.pack(fill="x", pady=(12, 0))
        self.trash.bind("<ButtonRelease-1>", self.drop_on_trash)

    def build_medicine(self):
        ttk.Label(self.medicine_tab, text="Medicine List",
                  font=("Arial", 16, "bold")).pack(anchor="w")
        self.medicine_table = self.make_table(
            self.medicine_tab, ("medicine", "member", "left", "per_day"),
            ("Medicine", "Member", "Pills left", "Pills per day")
        )

    def build_groceries(self):
        ttk.Label(self.groceries_tab, text="Grocery List",
                  font=("Arial", 16, "bold")).pack(anchor="w")
        self.groceries_table = self.make_table(
            self.groceries_tab, ("status", "items"), ("Status", "Items")
        )
        ttk.Label(self.groceries_tab, text="Each row is a grocery stock category.",
                  foreground="gray").pack(anchor="w", pady=8)

    @staticmethod
    def clear_table(table):
        for item in table.get_children():
            table.delete(item)

    def refresh_tables(self):
        if self.current_family is None:
            self.clear_table(self.medicine_table)
            self.clear_table(self.groceries_table)
            return

        family_id = str(self.current_family.get("family_id", ""))
        family_members = [
            m for m in self.members
            if str(m.get("family_id")) == family_id
        ]
        member_names = {m.get("member_id"): m.get("member_name", "Unknown")
                        for m in family_members}

        self.clear_table(self.medicine_table)
        for med in self.medicines:
            if str(med.get("family_id")) == family_id:
                self.medicine_table.insert("", "end", values=(
                    med.get("medicine_name", ""),
                    member_names.get(med.get("member_id"), "Unknown member"),
                    med.get("pills_left", 0),
                    med.get("pills_per_day", 0),
                ))

        self.clear_table(self.groceries_table)
        grocery = next((g for g in self.groceries if str(g.get("family_id")) == family_id),
                      {"stock": [], "out_of_stock": []})
        self.groceries_table.insert("", "end", values=(
            "In stock", ", ".join(grocery.get("stock", [])) or "None"
        ))
        self.groceries_table.insert("", "end", values=(
            "Out of stock", ", ".join(grocery.get("out_of_stock", [])) or "None"
        ))

    def add_member_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Family Member")
        dialog.configure(bg=BG)
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        body = tk.Frame(dialog, bg=BG, padx=22, pady=22)
        body.pack(fill="both", expand=True)

        tk.Label(
            body,
            text="Create a profile",
            bg=BG,
            fg="white",
            font=("Arial", 19, "bold")
        ).pack(anchor="w", pady=(0, 12))

        avatar_var = tk.StringVar(value=AVATARS[0])

        tk.Label(body, text="Choose an avatar", bg=BG, fg="white").pack(anchor="w")

        avatar_frame = tk.Frame(body, bg=BG)
        avatar_frame.pack(pady=8)

        for i, emoji in enumerate(AVATARS):
            tk.Radiobutton(
                avatar_frame,
                text=emoji,
                variable=avatar_var,
                value=emoji,
                indicatoron=False,
                font=("Arial", 19),
                bg=CARD,
                fg="white",
                selectcolor="#555555",
                width=3
            ).grid(
                row=i // 4,
                column=i % 4,
                padx=3,
                pady=3
            )

        def make_entry(label, show=None):
            tk.Label(
                body,
                text=label,
                bg=BG,
                fg="white"
            ).pack(anchor="w", pady=(7, 3))

            entry = tk.Entry(
                body,
                show=show or "",
                width=30,
                font=("Arial", 12)
            )
            entry.pack(ipady=5, fill="x")
            return entry

        name_entry = make_entry("Member name")
        pin_entry = make_entry("Create a 4-digit PIN", "*")
        confirm_entry = make_entry("Confirm PIN", "*")

        def submit():
            name = name_entry.get().strip()
            pin = pin_entry.get()
            confirm = confirm_entry.get()

            if not name:
                messagebox.showerror(
                    "Missing name",
                    "Please enter a member name.",
                    parent=dialog
                )
                return

            if len(pin) != 4 or not pin.isdigit():
                messagebox.showerror(
                    "Invalid PIN",
                    "Enter exactly four digits.",
                    parent=dialog
                )
                return

            if pin != confirm:
                messagebox.showerror(
                    "PIN mismatch",
                    "The two PINs do not match.",
                    parent=dialog
                )
                return

            family_id = self.current_family["family_id"]

            if any(
                str(m.get("family_id")) == str(family_id)
                and m.get("member_name", "").casefold() == name.casefold()
                for m in self.members
            ):
                messagebox.showerror(
                    "Duplicate name",
                    "This member name already exists in your family.",
                    parent=dialog
                )
                return

            existing_ids = [
                int(m["member_id"])
                for m in self.members
                if str(m.get("family_id")) == str(family_id)
                and str(m.get("member_id", "")).isdigit()
            ]

            new_member = {
                "family_id": family_id,
                "member_id": max(existing_ids, default=0) + 1,
                "member_name": name,
                "pin": pin,
                "avatar": avatar_var.get()
            }

            self.members.append(new_member)

            try:
                save_json("member.json", self.members)
            except OSError as exc:
                self.members.pop()
                messagebox.showerror(
                    "Save failed",
                    f"Could not save the member:\n{exc}",
                    parent=dialog
                )
                return

            dialog.destroy()
            self.refresh_tables()
            self.render_profiles()

            messagebox.showinfo(
                "Profile created",
                f"{name} was added successfully."
            )

        tk.Button(
            body,
            text="CREATE PROFILE",
            command=submit,
            bg=ACCENT,
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            pady=10
        ).pack(fill="x", pady=(16, 0))

if __name__ == "__main__":
    root = tk.Tk()
    app = FamilyApp(root)
    root.mainloop()
