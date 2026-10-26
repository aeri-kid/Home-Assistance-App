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
        self.root.geometry("900x680")
        self.root.minsize(700, 500)

        self.families = load_json("family.json")
        self.members = load_json("member.json")
        self.medicines = load_json("medicine.json")
        self.groceries = load_json("groceries.json")
        self.current_family = None

        self.undo_timer = None
        self.last_deleted_items = []
        self.dragged_item_info = None

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
        # 1. To-Do List Frame (Groceries to buy)
        todo_frame = ttk.LabelFrame(self.groceries_tab, text=" Groceries To-Buy (To-Do List) ", padding=10)
        todo_frame.pack(fill="x", pady=(0, 15))

        add_frame = ttk.Frame(todo_frame)
        add_frame.pack(fill="x", pady=(0, 10))

        self.todo_entry = ttk.Entry(add_frame, width=35)
        self.todo_entry.pack(side="left", padx=(0, 8))
        self.todo_entry.bind("<Return>", lambda e: self.add_todo_item())

        ttk.Button(add_frame, text="Add Item", command=self.add_todo_item).pack(side="left")

        # Scrollable area for checkboxed items
        canvas_container = ttk.Frame(todo_frame)
        canvas_container.pack(fill="x", expand=True)

        self.todo_canvas = tk.Canvas(canvas_container, height=120, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=self.todo_canvas.yview)
        self.todo_items_frame = ttk.Frame(self.todo_canvas)

        self.todo_items_frame.bind(
            "<Configure>",
            lambda e: self.todo_canvas.configure(scrollregion=self.todo_canvas.bbox("all"))
        )

        self.todo_canvas.create_window((0, 0), window=self.todo_items_frame, anchor="nw")
        self.todo_canvas.configure(yscrollcommand=scrollbar.set)

        self.todo_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        btn_frame = ttk.Frame(todo_frame)
        btn_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(btn_frame, text="Delete Selected (Bought)", command=self.delete_selected_todo).pack(side="left", padx=(0, 10))
        self.undo_btn = ttk.Button(btn_frame, text="Undo Delete", command=self.undo_delete, state="disabled")
        self.undo_btn.pack(side="left")

        # 2. Stock and Out-of-Stock Section
        stock_frame = ttk.LabelFrame(self.groceries_tab, text=" Stock for basic groceries ", padding=10)
        stock_frame.pack(fill="both", expand=True)

        ttk.Label(stock_frame, text="Drag items between In Stock and Out of Stock to update location:",
                  foreground="gray").pack(anchor="w", pady=(0, 8))

        tables_container = ttk.Frame(stock_frame)
        tables_container.pack(fill="both", expand=True)

        # In Stock Box
        stock_subframe = ttk.LabelFrame(tables_container, text="In Stock")
        stock_subframe.pack(side="left", fill="both", expand=True, padx=(0, 5))
        self.stock_listbox = tk.Listbox(stock_subframe, selectmode="single", font=("Arial", 11), bg="#222", fg="white")
        self.stock_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        # Out of Stock Box
        out_subframe = ttk.LabelFrame(tables_container, text="Out of Stock")
        out_subframe.pack(side="right", fill="both", expand=True, padx=(5, 0))
        self.out_listbox = tk.Listbox(out_subframe, selectmode="single", font=("Arial", 11), bg="#222", fg="white")
        self.out_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        # Bind Drag and Drop Events
        for lb, src in [(self.stock_listbox, "stock"), (self.out_listbox, "out_of_stock")]:
            lb.bind("<ButtonPress-1>", lambda e, s=src, widget=lb: self.start_stock_drag(e, s, widget))
            lb.bind("<B1-Motion>", self.motion_stock_drag)
            lb.bind("<ButtonRelease-1>", self.finish_stock_drag)

    def start_stock_drag(self, event, source_type, widget):
        index = widget.nearest(event.y)
        if index >= 0 and index < widget.size():
            item_text = widget.get(index)
            self.dragged_item_info = {"item": item_text, "source": source_type}

    def motion_stock_drag(self, event):
        pass

    def finish_stock_drag(self, event):
        if not self.dragged_item_info or not self.current_family:
            return

        x, y = self.root.winfo_pointerxy()
        target = self.root.winfo_containing(x, y)

        item = self.dragged_item_info["item"]
        source = self.dragged_item_info["source"]

        target_type = None
        if target in (self.stock_listbox, self.stock_listbox.master):
            target_type = "stock"
        elif target in (self.out_listbox, self.out_listbox.master):
            target_type = "out_of_stock"

        if target_type and target_type != source:
            family_id = str(self.current_family.get("family_id", ""))
            grocery = next((g for g in self.groceries if str(g.get("family_id")) == family_id), None)
            if grocery:
                grocery.setdefault("stock", [])
                grocery.setdefault("out_of_stock", [])

                if item in grocery[source]:
                    grocery[source].remove(item)
                    grocery[target_type].append(item)
                    save_json("groceries.json", self.groceries)
                    self.refresh_tables()

        self.dragged_item_info = None

    def get_current_family_grocery(self):
        if not self.current_family:
            return None
        family_id = str(self.current_family.get("family_id", ""))
        grocery = next((g for g in self.groceries if str(g.get("family_id")) == family_id), None)
        if not grocery:
            grocery = {"family_id": family_id, "stock": [], "out_of_stock": [], "to_buy": []}
            self.groceries.append(grocery)
        return grocery

    def add_todo_item(self):
        text = self.todo_entry.get().strip()
        if not text:
            return
        grocery = self.get_current_family_grocery()
        if grocery is not None:
            grocery.setdefault("to_buy", []).append(text)
            save_json("groceries.json", self.groceries)
            self.todo_entry.delete(0, "end")
            self.refresh_todo_list()

    def delete_selected_todo(self):
        grocery = self.get_current_family_grocery()
        if not grocery:
            return

        to_buy = grocery.get("to_buy", [])
        selected_indexes = [
            idx for idx, var in getattr(self, "todo_check_vars", []) if var.get()
        ]

        if not selected_indexes:
            messagebox.showinfo("No Selection", "Please check items to delete.")
            return

        self.last_deleted_items = [to_buy[idx] for idx in selected_indexes]
        selected_set = set(selected_indexes)
        grocery["to_buy"] = [
            item for idx, item in enumerate(to_buy) if idx not in selected_set
        ]
        save_json("groceries.json", self.groceries)
        self.refresh_todo_list()

        self.start_undo_timer(10)

    def start_undo_timer(self, seconds_left):
        if self.undo_timer:
            self.root.after_cancel(self.undo_timer)

        if seconds_left > 0:
            self.undo_btn.config(state="normal", text=f"Undo Delete ({seconds_left}s)")
            self.undo_timer = self.root.after(1000, self.start_undo_timer, seconds_left - 1)
        else:
            self.undo_btn.config(state="disabled", text="Undo Delete")
            self.last_deleted_items = []
            self.undo_timer = None

    def undo_delete(self):
        if not self.last_deleted_items:
            return

        grocery = self.get_current_family_grocery()
        if grocery is not None:
            grocery.setdefault("to_buy", []).extend(self.last_deleted_items)
            save_json("groceries.json", self.groceries)
            self.last_deleted_items = []
            if self.undo_timer:
                self.root.after_cancel(self.undo_timer)
                self.undo_timer = None
            self.undo_btn.config(state="disabled", text="Undo Delete")
            self.refresh_todo_list()

    def refresh_todo_list(self):
        for widget in self.todo_items_frame.winfo_children():
            widget.destroy()

        self.todo_check_vars = []
        if not self.current_family:
            return

        grocery = self.get_current_family_grocery()
        to_buy_items = grocery.get("to_buy", [])

        for idx, item in enumerate(to_buy_items):
            var = tk.BooleanVar(value=False)
            chk = ttk.Checkbutton(self.todo_items_frame, text=item, variable=var)
            chk.pack(anchor="w", pady=2)
            self.todo_check_vars.append((idx, var))

    @staticmethod
    def clear_table(table):
        for item in table.get_children():
            table.delete(item)

    def refresh_tables(self):
        if self.current_family is None:
            self.clear_table(self.medicine_table)
            self.stock_listbox.delete(0, "end")
            self.out_listbox.delete(0, "end")
            self.refresh_todo_list()
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

        # Refresh Groceries Stock & Out of Stock
        self.stock_listbox.delete(0, "end")
        self.out_listbox.delete(0, "end")

        grocery = next((g for g in self.groceries if str(g.get("family_id")) == family_id),
                      {"stock": [], "out_of_stock": []})

        for item in grocery.get("stock", []):
            self.stock_listbox.insert("end", item)

        for item in grocery.get("out_of_stock", []):
            self.out_listbox.insert("end", item)

        self.refresh_todo_list()

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
