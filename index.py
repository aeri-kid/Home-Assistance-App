import json
import calendar
from datetime import date, datetime
import tkinter as tk
from tkinter import simpledialog
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
        self.drag_moved = False
        self.trash.configure(bg="#7A1515")

    def drag_motion(self, event):
        self.drag_moved = True
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
        elif not getattr(self, "drag_moved", False):
            self.ask_member_pin(self.dragged_member)

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

    def ask_member_pin(self, member):
        if not member or not self.current_family:
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("Member PIN")
        dialog.configure(bg=BG)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        tk.Label(dialog, text=f"{member.get('avatar', '👤')}  {member.get('member_name', 'Member')}",
                 bg=BG, fg="white", font=("Arial", 18, "bold")).pack(padx=24, pady=(20, 8))
        tk.Label(dialog, text="Enter your 4-digit PIN to continue", bg=BG, fg="white").pack(padx=24)
        pin_entry = tk.Entry(dialog, show="*", justify="center", font=("Arial", 16), width=12)
        pin_entry.pack(padx=24, pady=12)

        def verify(event=None):
            if pin_entry.get() == str(member.get("pin", "")):
                dialog.destroy()
                self.open_member_dashboard(member)
            else:
                messagebox.showerror("Incorrect PIN", "That PIN is incorrect. Please try again.", parent=dialog)
                pin_entry.delete(0, "end")
                pin_entry.focus_set()
        tk.Button(dialog, text="UNLOCK PROFILE", command=verify, bg=ACCENT, fg="white",
                  relief="flat", padx=16, pady=8).pack(padx=24, pady=(0, 20))
        pin_entry.bind("<Return>", verify)
        pin_entry.focus_set()

    def open_member_dashboard(self, member):
        """Open a separate, PIN-protected member dashboard."""
        family = self.current_family
        family_id = str(family.get("family_id", ""))
        member_id = str(member.get("member_id", ""))
        schedule_file = "schedule.json"
        dashboard = tk.Toplevel(self.root)
        dashboard.title(f"{member.get('member_name', 'Member')} — Personal Dashboard")
        dashboard.geometry("1120x760")
        dashboard.minsize(900, 650)
        dashboard.configure(bg="#F3F5FC")
        dashboard.protocol("WM_DELETE_WINDOW", dashboard.destroy)

        selected_date = {"value": date.today()}
        shown_month = {"year": date.today().year, "month": date.today().month}
        schedules = load_json(schedule_file) if (DATA_DIR / schedule_file).exists() else []
        if not isinstance(schedules, list):
            schedules = []

        def member_tasks(day_string=None):
            return [item for item in schedules
                    if str(item.get("family_id")) == family_id
                    and str(item.get("member_id")) == member_id
                    and (day_string is None or item.get("date") == day_string)]

        top = tk.Frame(dashboard, bg="#F3F5FC")
        top.pack(fill="x", padx=24, pady=(18, 8))
        tk.Label(top, text=f"{member.get('avatar', '👤')}  {member.get('member_name', 'Member')}",
                 bg="#F3F5FC", fg="#171923", font=("Arial", 24, "bold")).pack(side="left")

        def logout():
            dashboard.destroy()
            self.render_profiles()
            self.tabs.select(self.members_tab)
        tk.Button(top, text="Log Out", command=logout, bg=ACCENT, fg="white",
                  relief="flat", padx=18, pady=8).pack(side="right")
        tk.Label(dashboard, text=family.get("family_name", "Family"), bg="#F3F5FC",
                 fg="#626778", font=("Arial", 11)).pack(anchor="w", padx=28)

        content = tk.Frame(dashboard, bg="#F3F5FC")
        content.pack(fill="both", expand=True, padx=22, pady=14)
        left = tk.Frame(content, bg="white", highlightbackground="#D9DDE8", highlightthickness=1)
        left.pack(side="left", fill="y", padx=(0, 14), ipadx=12, ipady=12)
        right = tk.Frame(content, bg="#F3F5FC")
        right.pack(side="left", fill="both", expand=True)

        detail_labels = {}
        detail_frame = tk.Frame(left, bg="white", padx=18, pady=18)
        detail_frame.pack(fill="x")
        tk.Label(detail_frame, text="Personal Details", bg="white", fg="#171923",
                 font=("Arial", 16, "bold")).pack(anchor="w", pady=(0, 14))
        fields = [("birthday", "Birthday"), ("age", "Age"), ("job", "Job"), ("hobby", "Hobby")]
        for key, label in fields:
            tk.Label(detail_frame, text=label, bg="white", fg="#72778A",
                     font=("Arial", 10, "bold")).pack(anchor="w", pady=(5, 0))
            value = tk.Label(detail_frame, text=str(member.get(key, "—") or "—"), bg="white",
                             fg="#202333", font=("Arial", 11), wraplength=220, justify="left")
            value.pack(anchor="w", pady=(1, 4))
            detail_labels[key] = value

        def edit_details():
            edit = tk.Toplevel(dashboard)
            edit.title("Edit Personal Details")
            edit.transient(dashboard)
            edit.grab_set()
            body = ttk.Frame(edit, padding=16)
            body.pack(fill="both", expand=True)
            entries = {}
            for row, (key, label) in enumerate(fields):
                ttk.Label(body, text=label + ":").grid(row=row, column=0, sticky="w", padx=(0, 12), pady=6)
                ent = ttk.Entry(body, width=32)
                ent.insert(0, str(member.get(key, "") or ""))
                ent.grid(row=row, column=1, pady=6)
                entries[key] = ent
            def save_details():
                birthday = entries["birthday"].get().strip()
                if birthday:
                    try:
                        datetime.strptime(birthday, "%Y-%m-%d")
                    except ValueError:
                        messagebox.showerror("Invalid birthday", "Use YYYY-MM-DD for the birthday.", parent=edit)
                        return
                old = {key: member.get(key) for key, _ in fields}
                for key, _ in fields:
                    member[key] = entries[key].get().strip()
                try:
                    save_json("member.json", self.members)
                except OSError as exc:
                    for key, value in old.items():
                        if value is None:
                            member.pop(key, None)
                        else:
                            member[key] = value
                    messagebox.showerror("Save failed", str(exc), parent=edit)
                    return
                for key, _ in fields:
                    value = member.get(key, "") or "—"
                    detail_labels[key].config(text=value)
                edit.destroy()
            ttk.Button(body, text="Save", command=save_details).grid(row=len(fields), column=1, sticky="e", pady=(12, 0))
        ttk.Button(detail_frame, text="Edit Details", command=edit_details).pack(anchor="w", pady=(12, 0))

        # Calendar panel
        calendar_frame = tk.Frame(right, bg="white", highlightbackground="#D9DDE8", highlightthickness=1)
        calendar_frame.pack(fill="both", expand=True)
        month_header = tk.Frame(calendar_frame, bg="white")
        month_header.pack(fill="x", padx=12, pady=10)
        month_title = tk.Label(month_header, text="", bg="white", fg="#171923", font=("Arial", 15, "bold"))
        month_title.pack(side="left", expand=True)
        tk.Button(month_header, text="‹", command=lambda: shift_month(-1), bg="white", relief="flat").pack(side="left")
        tk.Button(month_header, text="›", command=lambda: shift_month(1), bg="white", relief="flat").pack(side="right")
        days_frame = tk.Frame(calendar_frame, bg="white")
        days_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        task_check_vars = []

        def refresh_tasks():
            for widget in task_items_frame.winfo_children():
                widget.destroy()
            task_check_vars.clear()

            day_string = selected_date["value"].isoformat()
            selected_label.config(text=f"Selected day: {day_string}")
            day_tasks = member_tasks(day_string)

            for task in day_tasks:
                var = tk.BooleanVar(value=bool(task.get("completed")))
                def on_toggle(t=task, v=var):
                    t["completed"] = v.get()
                    persist_schedule()
                    refresh_calendar()
                
                chk = tk.Checkbutton(
                    task_items_frame, text=task.get("title", "Task"),
                    variable=var, command=on_toggle, bg="white",
                    fg="#202333", activebackground="white",
                    font=("Arial", 11), anchor="w"
                )
                chk.pack(fill="x", anchor="w", pady=2)
                task_check_vars.append((task, var))
            refresh_medicines()

        def choose_day(day):
            selected_date["value"] = date(shown_month["year"], shown_month["month"], day)
            refresh_calendar()
            refresh_tasks()

        def refresh_calendar():
            for w in days_frame.winfo_children():
                w.destroy()
            month_title.config(text=f"{calendar.month_name[shown_month['month']]} {shown_month['year']}")
            for col, name in enumerate(("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")):
                tk.Label(days_frame, text=name, bg="white", fg="#70768A", font=("Arial", 9, "bold")).grid(row=0, column=col, sticky="nsew", padx=2, pady=3)
                days_frame.grid_columnconfigure(col, weight=1)
            cal = calendar.Calendar(firstweekday=0)
            for row, week in enumerate(cal.monthdayscalendar(shown_month["year"], shown_month["month"]), start=1):
                days_frame.grid_rowconfigure(row, weight=1)
                for col, day in enumerate(week):
                    if day:
                        is_selected = selected_date["value"] == date(shown_month["year"], shown_month["month"], day)
                        has_tasks = bool(member_tasks(date(shown_month["year"], shown_month["month"], day).isoformat()))
                        label = f"{day}{' •' if has_tasks else ''}"
                        tk.Button(days_frame, text=label, command=lambda d=day: choose_day(d),
                                  bg=ACCENT if is_selected else ("#E8EBF5" if has_tasks else "white"),
                                  fg="white" if is_selected else "#202333", relief="flat").grid(row=row, column=col, sticky="nsew", padx=2, pady=2, ipady=5)

        def shift_month(delta):
            month = shown_month["month"] + delta
            year = shown_month["year"]
            if month < 1:
                month, year = 12, year - 1
            elif month > 12:
                month, year = 1, year + 1
            shown_month.update(year=year, month=month)
            refresh_calendar()

        task_frame = tk.Frame(right, bg="white", highlightbackground="#D9DDE8", highlightthickness=1)
        task_frame.pack(fill="both", expand=True, pady=(12, 0))
        selected_label = tk.Label(task_frame, text="", bg="white", fg="#171923", font=("Arial", 14, "bold"))
        selected_label.pack(anchor="w", padx=14, pady=(12, 4))
        tk.Label(task_frame, text="Schedule", bg="white", fg="#6E7385").pack(anchor="w", padx=14)

        # Scrollable Task Container for Checkbox Checklist
        task_canvas_container = tk.Frame(task_frame, bg="white")
        task_canvas_container.pack(fill="both", expand=True, padx=12, pady=6)
        
        task_canvas = tk.Canvas(task_canvas_container, bg="white", highlightthickness=0)
        task_scrollbar = ttk.Scrollbar(task_canvas_container, orient="vertical", command=task_canvas.yview)
        task_items_frame = tk.Frame(task_canvas, bg="white")

        task_items_frame.bind(
            "<Configure>",
            lambda e: task_canvas.configure(scrollregion=task_canvas.bbox("all"))
        )

        task_canvas.create_window((0, 0), window=task_items_frame, anchor="nw")
        task_canvas.configure(yscrollcommand=task_scrollbar.set)

        task_canvas.pack(side="left", fill="both", expand=True)
        task_scrollbar.pack(side="right", fill="y")

        task_controls = tk.Frame(task_frame, bg="white")
        task_controls.pack(fill="x", padx=12, pady=(0, 10))

        def persist_schedule():
            try:
                save_json(schedule_file, schedules)
                return True
            except OSError as exc:
                messagebox.showerror("Save failed", f"Could not save schedule: {exc}", parent=dashboard)
                return False

        def add_task():
            dialog = tk.Toplevel(dashboard)
            dialog.title("Add Schedule Task")
            dialog.transient(dashboard)
            dialog.grab_set()
            body = ttk.Frame(dialog, padding=16)
            body.pack(fill="both", expand=True)
            ttk.Label(body, text="Task:").grid(row=0, column=0, sticky="w", pady=6)
            title_entry = ttk.Entry(body, width=34)
            title_entry.grid(row=0, column=1, pady=6)
            ttk.Label(body, text="Date (YYYY-MM-DD):").grid(row=1, column=0, sticky="w", pady=6)
            date_entry = ttk.Entry(body, width=34)
            date_entry.insert(0, selected_date["value"].isoformat())
            date_entry.grid(row=1, column=1, pady=6)
            def save_task():
                title = title_entry.get().strip()
                try:
                    task_date = datetime.strptime(date_entry.get().strip(), "%Y-%m-%d").date().isoformat()
                except ValueError:
                    messagebox.showerror("Invalid date", "Enter a valid date as YYYY-MM-DD.", parent=dialog)
                    return
                if not title:
                    messagebox.showerror("Missing task", "Please enter a task name.", parent=dialog)
                    return
                item = {"family_id": family_id, "member_id": member_id, "date": task_date,
                        "title": title, "completed": False}
                schedules.append(item)
                if not persist_schedule():
                    schedules.remove(item)
                    return
                selected_date["value"] = date.fromisoformat(task_date)
                shown_month.update(year=selected_date["value"].year, month=selected_date["value"].month)
                dialog.destroy()
                refresh_calendar()
                refresh_tasks()
            ttk.Button(body, text="Save Task", command=save_task).grid(row=2, column=1, sticky="e", pady=(10, 0))
            title_entry.focus_set()

        def edit_task():
            checked_items = [task for task, var in task_check_vars if var.get()]
            if len(checked_items) != 1:
                messagebox.showinfo("Select a single task", "Please check exactly one task to edit.", parent=dashboard)
                return
            item = checked_items[0]
            new_title = simpledialog.askstring("Edit Task", "Task name:", initialvalue=item.get("title", ""), parent=dashboard)
            if new_title is None or not new_title.strip():
                return
            old = item.get("title")
            item["title"] = new_title.strip()
            if not persist_schedule(): item["title"] = old
            refresh_calendar(); refresh_tasks()

        def delete_checked_tasks():
            checked_items = [task for task, var in task_check_vars if var.get()]
            if not checked_items:
                messagebox.showinfo("Select task(s)", "Please check one or more tasks to delete.", parent=dashboard)
                return
            if not messagebox.askyesno("Delete tasks", f"Delete {len(checked_items)} checked item(s)?", parent=dashboard):
                return
            for task in checked_items:
                if task in schedules:
                    schedules.remove(task)
            persist_schedule()
            refresh_calendar()
            refresh_tasks()

        ttk.Button(task_controls, text="+ Add", command=add_task).pack(side="left", padx=(0, 6))
        ttk.Button(task_controls, text="Edit", command=edit_task).pack(side="left", padx=6)
        ttk.Button(task_controls, text="Delete Checked", command=delete_checked_tasks).pack(side="right")

        med_frame = tk.Frame(left, bg="white", padx=18, pady=12)
        med_frame.pack(fill="both", expand=True)
        
        med_header = tk.Frame(med_frame, bg="white")
        med_header.pack(fill="x", pady=(0, 8))
        tk.Label(med_header, text="My Medicines", bg="white", fg="#171923",
                 font=("Arial", 15, "bold")).pack(side="left")

        med_btn_frame = tk.Frame(med_frame, bg="white")
        med_btn_frame.pack(fill="x", pady=(0, 6))

        def add_profile_medicine():
            self._medicine_editor_dialog(None, default_member_id=member_id)
            refresh_medicines()

        def edit_profile_medicine(event=None):
            selection = med_table.selection()
            if not selection:
                messagebox.showinfo("Select Medicine", "Select a medicine to edit.", parent=dashboard)
                return
            med = getattr(dashboard, "_profile_med_map", {}).get(selection[0])
            if med:
                self._medicine_editor_dialog(med)
                refresh_medicines()

        def delete_profile_medicine():
            selection = med_table.selection()
            if not selection:
                messagebox.showinfo("Select Medicine", "Select a medicine to delete.", parent=dashboard)
                return
            med = getattr(dashboard, "_profile_med_map", {}).get(selection[0])
            if med:
                if messagebox.askyesno("Delete Medicine", f"Delete '{med.get('medicine_name', 'Medicine')}'?", parent=dashboard):
                    self.medicines = [m for m in self.medicines if id(m) != id(med)]
                    try:
                        self._save_medicine_data()
                    except OSError as exc:
                        messagebox.showerror("Save failed", str(exc), parent=dashboard)
                        self.medicines = load_json("medicine.json")
                        self.members = load_json("member.json")
                    refresh_medicines()
                    self.refresh_tables()

        ttk.Button(med_btn_frame, text="+ Add", command=add_profile_medicine).pack(side="left", padx=(0, 4))
        ttk.Button(med_btn_frame, text="Edit", command=edit_profile_medicine).pack(side="left", padx=4)
        ttk.Button(med_btn_frame, text="Delete", command=delete_profile_medicine).pack(side="right")

        med_table = ttk.Treeview(med_frame, columns=("name", "left", "daily"), show="headings", height=6)
        for col, heading, width in [("name", "Medicine", 130), ("left", "Pills left", 65), ("daily", "Per day", 65)]:
            med_table.heading(col, text=heading)
            med_table.column(col, width=width, anchor="w")
        med_table.pack(fill="both", expand=True)
        med_table.bind("<Double-1>", edit_profile_medicine)

        def refresh_medicines():
            med_table.delete(*med_table.get_children())
            dashboard._profile_med_map = {}
            for med in self.medicines:
                if str(med.get("family_id")) != family_id:
                    continue
                assigned = med.get("member_ids")
                if isinstance(assigned, list):
                    matches = member_id in {str(x) for x in assigned} or not assigned
                else:
                    med_member = str(med.get("member_id", ""))
                    matches = med_member == member_id or med_member.casefold() == "all"
                if matches:
                    item_id = med_table.insert("", "end", values=(med.get("medicine_name", ""),
                        med.get("pills_left", "—"), med.get("pills_per_day", "—")))
                    dashboard._profile_med_map[item_id] = med

        refresh_calendar()
        refresh_tasks()

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
        self.last_deleted_to_buy = []
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
        header = ttk.Frame(self.medicine_tab)
        header.pack(fill="x", pady=(0, 8))
        ttk.Label(header, text="Medicine List",
                  font=("Arial", 16, "bold")).pack(side="left")
        ttk.Button(header, text="+ Add Medicine",
                   command=self.add_medicine_dialog).pack(side="right", padx=(8, 0))
        ttk.Button(header, text="Delete Selected",
                   command=self.delete_selected_medicines).pack(side="right")

        controls = ttk.Frame(self.medicine_tab)
        controls.pack(fill="x", pady=(0, 6))
        ttk.Label(controls, text="Column:").pack(side="left")
        self.med_column_var = tk.StringVar(value="Medicine")
        self.med_column_combo = ttk.Combobox(
            controls, textvariable=self.med_column_var, state="readonly", width=16,
            values=("Medicine ID", "Medicine", "Member", "Pills left", "Pills per day"))
        self.med_column_combo.pack(side="left", padx=(5, 8))
        ttk.Label(controls, text="Action:").pack(side="left")
        self.med_action_var = tk.StringVar(value="Sort A–Z")
        self.med_action_combo = ttk.Combobox(
            controls, textvariable=self.med_action_var, state="readonly", width=12,
            values=("Sort A–Z", "Sort Z–A", "Filter contains"))
        self.med_action_combo.pack(side="left", padx=(5, 8))
        self.med_filter_entry = ttk.Entry(controls, width=18)
        self.med_filter_entry.pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Apply", command=self.apply_medicine_view).pack(side="left")
        ttk.Button(controls, text="Clear", command=self.clear_medicine_view).pack(side="left", padx=(5, 0))
        ttk.Label(self.medicine_tab, text="Double-click a medicine to edit it.",
                  foreground="gray").pack(anchor="w")

        self.medicine_table = self.make_table(
            self.medicine_tab,
            ("medicine_id", "medicine", "member", "left", "per_day"),
            ("Medicine ID", "Medicine", "Member", "Pills left", "Pills per day"))
        widths = {"medicine_id": 105, "medicine": 230, "member": 200,
                  "left": 110, "per_day": 120}
        for col, width in widths.items():
            self.medicine_table.column(col, width=width, anchor="w")
        self.medicine_table.bind("<Double-1>", self.edit_selected_medicine)
        self.medicine_sort = None
        self.medicine_filter = None

    def _family_members(self):
        if not self.current_family:
            return []
        family_id = str(self.current_family.get("family_id", ""))
        return [m for m in self.members if str(m.get("family_id")) == family_id]

    def _medicine_member_label(self, med):
        members = self._family_members()
        member_ids = med.get("member_ids")
        if isinstance(member_ids, list):
            if not member_ids:
                return "All"
            if {str(x) for x in member_ids} >= {str(m.get("member_id")) for m in members}:
                return "All"
            labels = []
            for member in members:
                if str(member.get("member_id")) in {str(x) for x in member_ids}:
                    labels.append(f"{member.get('avatar', '👤')} {member.get('member_name', 'Member')}")
            return ", ".join(labels) if labels else "Unknown member"

        member_id = str(med.get("member_id", ""))
        if member_id.casefold() == "all":
            return "All"
        member = next((m for m in members if str(m.get("member_id")) == member_id), None)
        if member:
            return f"{member.get('avatar', '👤')} {member.get('member_name', 'Member')}"
        return "Unknown member"

    def _next_medicine_id(self, exclude=None):
        used = {
            str(m.get("medicine_id", ""))
            for m in self.medicines
            if m is not exclude and str(m.get("medicine_id", "")).isdigit()
        }
        for number in range(100, 1000):
            code = f"{number:03d}"
            if code not in used:
                return code
        return None

    def _sync_member_medicine_ids(self, family_id):
        for member in self.members:
            if str(member.get("family_id")) == str(family_id):
                member["medicine_ids"] = []
        family_members = [
            m for m in self.members if str(m.get("family_id")) == str(family_id)
        ]
        for med in self.medicines:
            if str(med.get("family_id")) != str(family_id):
                continue
            ids = med.get("member_ids")
            if isinstance(ids, list):
                assigned = {str(x) for x in ids}
            else:
                legacy_id = str(med.get("member_id", ""))
                if legacy_id.casefold() == "all":
                    assigned = {str(m.get("member_id")) for m in family_members}
                else:
                    assigned = {legacy_id}
            for member in family_members:
                if str(member.get("member_id")) in assigned:
                    member.setdefault("medicine_ids", []).append(str(med.get("medicine_id", "")))

    def _save_medicine_data(self):
        family_id = str(self.current_family.get("family_id", ""))
        self._sync_member_medicine_ids(family_id)
        save_json("medicine.json", self.medicines)
        save_json("member.json", self.members)

    def add_medicine_dialog(self):
        self._medicine_editor_dialog(None)

    def edit_selected_medicine(self, event=None):
        selection = self.medicine_table.selection()
        if not selection:
            return
        med = getattr(self, "_medicine_rows", {}).get(selection[0])
        if med:
            self._medicine_editor_dialog(med)

    def _medicine_editor_dialog(self, med=None, default_member_id=None):
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Medicine" if med else "Add Medicine")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        body = ttk.Frame(dialog, padding=18)
        body.pack(fill="both", expand=True)

        ttk.Label(body, text="Medicine ID:").grid(row=0, column=0, sticky="w", padx=(0, 12), pady=5)
        med_id = str(med.get("medicine_id", "")) if med else (self._next_medicine_id() or "")
        ttk.Label(body, text=med_id or "No IDs available").grid(row=0, column=1, sticky="w", pady=5)

        ttk.Label(body, text="Medicine name *:").grid(row=1, column=0, sticky="w", padx=(0, 12), pady=5)
        name_var = tk.StringVar(value=med.get("medicine_name", "") if med else "")
        name_entry = ttk.Entry(body, textvariable=name_var, width=32)
        name_entry.grid(row=1, column=1, sticky="ew", pady=5)

        ttk.Label(body, text="Member:").grid(row=2, column=0, sticky="w", padx=(0, 12), pady=5)
        members = self._family_members()
        member_options = ["All"] + [
            f"{m.get('avatar', '👤')} {m.get('member_name', 'Member')}" for m in members
        ]
        member_lookup = {
            f"{m.get('avatar', '👤')} {m.get('member_name', 'Member')}": m for m in members
        }
        selected_label = "All"
        if med:
            existing_ids = med.get("member_ids")
            if isinstance(existing_ids, list):
                if len(existing_ids) == 1:
                    match = next((m for m in members if str(m.get("member_id")) == str(existing_ids[0])), None)
                    if match:
                        selected_label = f"{match.get('avatar', '👤')} {match.get('member_name', 'Member')}"
            elif str(med.get("member_id", "")).casefold() != "all":
                match = next((m for m in members if str(m.get("member_id")) == str(med.get("member_id"))), None)
                if match:
                    selected_label = f"{match.get('avatar', '👤')} {match.get('member_name', 'Member')}"
        elif default_member_id:
            match = next((m for m in members if str(m.get("member_id")) == str(default_member_id)), None)
            if match:
                selected_label = f"{match.get('avatar', '👤')} {match.get('member_name', 'Member')}"

        member_var = tk.StringVar(value=selected_label if selected_label in member_options else "All")
        member_combo = ttk.Combobox(body, textvariable=member_var, values=member_options,
                                    state="readonly", width=29)
        member_combo.grid(row=2, column=1, sticky="ew", pady=5)

        ttk.Label(body, text="Pills left:").grid(row=3, column=0, sticky="w", padx=(0, 12), pady=5)
        left_var = tk.StringVar(value=str(med.get("pills_left", "")) if med else "")
        ttk.Entry(body, textvariable=left_var, width=32).grid(row=3, column=1, sticky="ew", pady=5)

        ttk.Label(body, text="Pills per day:").grid(row=4, column=0, sticky="w", padx=(0, 12), pady=5)
        per_day_var = tk.StringVar(value=str(med.get("pills_per_day", "")) if med else "")
        ttk.Entry(body, textvariable=per_day_var, width=32).grid(row=4, column=1, sticky="ew", pady=5)

        def optional_number(value, label):
            value = value.strip()
            if not value:
                return ""
            try:
                number = int(value)
                if number < 0:
                    raise ValueError
                return number
            except ValueError:
                raise ValueError(f"{label} must be a non-negative whole number, or left blank.")

        def save_medicine():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Missing medicine name", "Enter a medicine name before saving.", parent=dialog)
                name_entry.focus_set()
                return
            if not med_id or len(med_id) != 3 or not med_id.isdigit():
                messagebox.showerror("ID unavailable", "A unique three-digit medicine ID could not be assigned.", parent=dialog)
                return
            try:
                pills_left = optional_number(left_var.get(), "Pills left")
                pills_per_day = optional_number(per_day_var.get(), "Pills per day")
            except ValueError as exc:
                messagebox.showerror("Invalid number", str(exc), parent=dialog)
                return

            family_id = str(self.current_family.get("family_id", ""))
            if member_var.get() == "All":
                assigned_members = [str(m.get("member_id")) for m in members]
                member_id = "all"
            else:
                selected_member = member_lookup.get(member_var.get())
                if selected_member is None:
                    assigned_members = []
                    member_id = "all"
                else:
                    member_id = selected_member.get("member_id")
                    assigned_members = [str(member_id)]

            record = {
                "family_id": family_id,
                "medicine_id": med_id,
                "medicine_name": name,
                "member_id": member_id,
                "member_ids": assigned_members,
                "pills_left": pills_left,
                "pills_per_day": pills_per_day
            }
            if med is None:
                self.medicines.insert(0, record)
            else:
                med.clear()
                med.update(record)
                self.medicines.remove(med)
                self.medicines.insert(0, med)
            try:
                self._save_medicine_data()
            except OSError as exc:
                messagebox.showerror("Save failed", f"Could not save medicine data:\n{exc}", parent=dialog)
                return
            self.medicine_sort = None
            self.medicine_filter = None
            if hasattr(self, "med_filter_entry"):
                self.med_filter_entry.delete(0, "end")
            dialog.destroy()
            self.refresh_tables()

        buttons = ttk.Frame(body)
        buttons.grid(row=5, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(buttons, text="Cancel", command=dialog.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(buttons, text="Save Medicine", command=save_medicine).pack(side="right")
        name_entry.focus_set()

    def delete_selected_medicines(self):
        selected = self.medicine_table.selection()
        if not selected:
            messagebox.showinfo("No selection", "Select one or more medicines to delete.")
            return
        rows = getattr(self, "_medicine_rows", {})
        selected_meds = [rows[item] for item in selected if item in rows]
        if not selected_meds:
            return
        names = ", ".join(str(m.get("medicine_name", "Medicine")) for m in selected_meds)
        if not messagebox.askyesno("Delete medicine", f"Delete selected medicine(s)?\n{names}"):
            return
        selected_objects = {id(m) for m in selected_meds}
        self.medicines = [m for m in self.medicines if id(m) not in selected_objects]
        try:
            self._save_medicine_data()
        except OSError as exc:
            messagebox.showerror("Save failed", f"Could not save medicine data:\n{exc}")
            self.medicines = load_json("medicine.json")
            self.members = load_json("member.json")
        self.refresh_tables()

    def apply_medicine_view(self):
        column_map = {
            "Medicine ID": "medicine_id", "Medicine": "medicine_name",
            "Member": "member", "Pills left": "pills_left",
            "Pills per day": "pills_per_day"
        }
        column = column_map.get(self.med_column_var.get(), "medicine_name")
        action = self.med_action_var.get()
        query = self.med_filter_entry.get().strip().casefold()
        if action == "Filter contains":
            self.medicine_filter = (column, query)
            self.medicine_sort = None
        else:
            self.medicine_sort = (column, action == "Sort Z–A")
            self.medicine_filter = None
        self.refresh_tables()

    def clear_medicine_view(self):
        self.medicine_sort = None
        self.medicine_filter = None
        self.med_filter_entry.delete(0, "end")
        self.refresh_tables()

    def _medicine_sort_value(self, med, column):
        if column == "member":
            return self._medicine_member_label(med).casefold()
        value = med.get(column, "")
        try:
            return (0, float(value)) if value != "" else (1, 0)
        except (TypeError, ValueError):
            return (0, str(value).casefold())

    def build_groceries(self):
        todo_frame = ttk.LabelFrame(self.groceries_tab, text=" Groceries To-Buy (To-Do List) ", padding=10)
        todo_frame.pack(fill="x", pady=(0, 15))

        # Direct To-Buy list entry & button
        add_todo_frame = ttk.Frame(todo_frame)
        add_todo_frame.pack(fill="x", pady=(0, 10))

        self.todo_entry = ttk.Entry(add_todo_frame, width=35)
        self.todo_entry.pack(side="left", padx=(0, 8))
        self.todo_entry.bind("<Return>", lambda e: self.add_to_buy_item())

        ttk.Button(add_todo_frame, text="Add Item", command=self.add_to_buy_item).pack(side="left")

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

        stock_frame = ttk.LabelFrame(self.groceries_tab, text=" Stock & Out of Stock Management ", padding=10)
        stock_frame.pack(fill="both", expand=True)

        # Entry box and add-stock / add-out-of-stock buttons
        add_frame = ttk.Frame(stock_frame)
        add_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(add_frame, text="Item:").pack(side="left", padx=(0, 6))
        self.grocery_entry = ttk.Entry(add_frame, width=28)
        self.grocery_entry.pack(side="left", padx=(0, 8))
        self.grocery_entry.bind("<Return>", lambda e: self.add_manual_grocery("stock"))

        ttk.Button(add_frame, text="add-stock", command=lambda: self.add_manual_grocery("stock")).pack(side="left", padx=(0, 6))
        ttk.Button(add_frame, text="add-out-of-stock", command=lambda: self.add_manual_grocery("out_of_stock")).pack(side="left")

        ttk.Label(stock_frame, text="Drag items between In Stock and Out of Stock to update location:",
                  foreground="gray").pack(anchor="w", pady=(0, 8))

        tables_container = ttk.Frame(stock_frame)
        tables_container.pack(fill="both", expand=True)

        # In Stock Listbox & Delete button
        stock_subframe = ttk.LabelFrame(tables_container, text="In Stock")
        stock_subframe.pack(side="left", fill="both", expand=True, padx=(0, 5))
        self.stock_listbox = tk.Listbox(stock_subframe, selectmode="single", font=("Arial", 11), bg="#222", fg="white")
        self.stock_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        ttk.Button(stock_subframe, text="Delete Selected", command=lambda: self.delete_listbox_item(self.stock_listbox, "stock")).pack(anchor="e", padx=5, pady=(0, 5))

        # Out of Stock Listbox & Delete button
        out_subframe = ttk.LabelFrame(tables_container, text="Out of Stock")
        out_subframe.pack(side="right", fill="both", expand=True, padx=(5, 0))
        self.out_listbox = tk.Listbox(out_subframe, selectmode="single", font=("Arial", 11), bg="#222", fg="white")
        self.out_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        ttk.Button(out_subframe, text="Delete Selected", command=lambda: self.delete_listbox_item(self.out_listbox, "out_of_stock")).pack(anchor="e", padx=5, pady=(0, 5))

        for lb, src in [(self.stock_listbox, "stock"), (self.out_listbox, "out_of_stock")]:
            lb.bind("<ButtonPress-1>", lambda e, s=src, widget=lb: self.start_stock_drag(e, s, widget))
            lb.bind("<B1-Motion>", self.motion_stock_drag)
            lb.bind("<ButtonRelease-1>", self.finish_stock_drag)

    def add_to_buy_item(self):
        text = self.todo_entry.get().strip()
        if not text:
            return
        grocery = self.get_current_family_grocery()
        if grocery is not None:
            grocery.setdefault("to_buy", [])
            grocery.setdefault("out_of_stock", [])
            grocery.setdefault("stock", [])

            if text not in grocery["to_buy"]:
                grocery["to_buy"].append(text)

            if text not in grocery["stock"] and text not in grocery["out_of_stock"]:
                grocery["out_of_stock"].append(text)

            save_json("groceries.json", self.groceries)
            self.todo_entry.delete(0, "end")
            self.refresh_tables()

    def add_manual_grocery(self, target_type):
        text = self.grocery_entry.get().strip()
        if not text:
            return
        grocery = self.get_current_family_grocery()
        if grocery is not None:
            grocery.setdefault("stock", [])
            grocery.setdefault("out_of_stock", [])

            other_type = "out_of_stock" if target_type == "stock" else "stock"
            if text in grocery[other_type]:
                grocery[other_type].remove(text)

            if text not in grocery[target_type]:
                grocery[target_type].append(text)

            save_json("groceries.json", self.groceries)
            self.grocery_entry.delete(0, "end")
            self.refresh_tables()

    def delete_listbox_item(self, listbox, source_type):
        selection = listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select an item to delete.")
            return
        index = selection[0]
        item = listbox.get(index)
        grocery = self.get_current_family_grocery()
        if grocery is not None:
            if item in grocery.get(source_type, []):
                grocery[source_type].remove(item)
            if item in grocery.get("to_buy", []):
                grocery["to_buy"].remove(item)
            save_json("groceries.json", self.groceries)
            self.refresh_tables()

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

    def delete_selected_todo(self):
        grocery = self.get_current_family_grocery()
        if not grocery:
            return

        selected_items = [item for item, var in getattr(self, "todo_check_vars", []) if var.get()]

        if not selected_items:
            messagebox.showinfo("No Selection", "Please check items to delete from the To-Buy list.")
            return

        self.last_deleted_to_buy = selected_items
        grocery["to_buy"] = [item for item in grocery.get("to_buy", []) if item not in selected_items]

        save_json("groceries.json", self.groceries)
        self.refresh_tables()

        self.start_undo_timer(10)

    def start_undo_timer(self, seconds_left):
        if self.undo_timer:
            self.root.after_cancel(self.undo_timer)

        if seconds_left > 0:
            self.undo_btn.config(state="normal", text=f"Undo Delete ({seconds_left}s)")
            self.undo_timer = self.root.after(1000, self.start_undo_timer, seconds_left - 1)
        else:
            self.undo_btn.config(state="disabled", text="Undo Delete")
            self.last_deleted_to_buy = []
            self.undo_timer = None

    def undo_delete(self):
        if not self.last_deleted_to_buy:
            return

        grocery = self.get_current_family_grocery()
        if grocery is not None:
            grocery.setdefault("to_buy", []).extend(self.last_deleted_to_buy)
            save_json("groceries.json", self.groceries)
            self.last_deleted_to_buy = []
            if self.undo_timer:
                self.root.after_cancel(self.undo_timer)
                self.undo_timer = None
            self.undo_btn.config(state="disabled", text="Undo Delete")
            self.refresh_tables()

    def refresh_todo_list(self):
        for widget in self.todo_items_frame.winfo_children():
            widget.destroy()

        self.todo_check_vars = []
        if not self.current_family:
            return

        grocery = self.get_current_family_grocery()
        out_items = grocery.get("out_of_stock", [])
        stock_items = grocery.get("stock", [])
        to_buy_items = grocery.get("to_buy", [])

        for item in out_items:
            if item not in to_buy_items:
                to_buy_items.append(item)

        combined_items = list(dict.fromkeys(to_buy_items))

        for item in combined_items:
            is_checked = item in stock_items
            var = tk.BooleanVar(value=is_checked)

            def on_toggle(it=item, v=var):
                g = self.get_current_family_grocery()
                if g:
                    g.setdefault("stock", [])
                    g.setdefault("out_of_stock", [])
                    if v.get():
                        if it in g["out_of_stock"]:
                            g["out_of_stock"].remove(it)
                        if it not in g["stock"]:
                            g["stock"].append(it)
                    else:
                        if it in g["stock"]:
                            g["stock"].remove(it)
                        if it not in g["out_of_stock"]:
                            g["out_of_stock"].append(it)
                    save_json("groceries.json", self.groceries)
                    self.refresh_tables()

            chk = ttk.Checkbutton(self.todo_items_frame, text=item, variable=var, command=on_toggle)
            chk.pack(anchor="w", pady=2)
            self.todo_check_vars.append((item, var))

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

        changed_ids = False
        existing_codes = {
            str(m.get("medicine_id", "")) for m in self.medicines
            if str(m.get("medicine_id", "")).isdigit()
        }
        for med in self.medicines:
            code = str(med.get("medicine_id", ""))
            if len(code) != 3 or not code.isdigit() or sum(1 for x in self.medicines if str(x.get("medicine_id", "")) == code) > 1:
                new_code = self._next_medicine_id()
                if new_code:
                    med["medicine_id"] = new_code
                    changed_ids = True
        if changed_ids:
            try:
                self._save_medicine_data()
            except OSError:
                pass

        self.clear_table(self.medicine_table)
        self._medicine_rows = {}
        family_meds = [
            med for med in self.medicines
            if str(med.get("family_id")) == family_id
        ]
        if self.medicine_filter:
            column, query = self.medicine_filter
            def filter_value(med):
                if column == "member":
                    return self._medicine_member_label(med)
                return med.get(column, "")
            family_meds = [
                med for med in family_meds
                if query in str(filter_value(med)).casefold()
            ]
        if self.medicine_sort:
            column, reverse = self.medicine_sort
            family_meds.sort(key=lambda med: self._medicine_sort_value(med, column),
                             reverse=reverse)

        for med in family_meds:
            iid = self.medicine_table.insert("", "end", values=(
                med.get("medicine_id", ""),
                med.get("medicine_name", ""),
                self._medicine_member_label(med),
                med.get("pills_left", ""),
                med.get("pills_per_day", "")
            ))
            self._medicine_rows[iid] = med

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
