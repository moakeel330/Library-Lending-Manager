"""
library_manager.py

Tkinter-based Library Lending Manager
- Creates library.db with two tables (books, borrowed_books)
- Insert sample books / borrowed records if none exist
- GUI: Borrow form (Student, Book combo, Borrow Date, Return Date)
- Add/Delete/Clear buttons, live searchable Treeview of borrowed_books
- Fine calculation: R5 per day late
"""

import sqlite3
from datetime import datetime, date
import os
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry

DB_FILE = "library.db"
FINE_PER_DAY = 5.0  # R5 per day constant


def init_db():
    """Create DB and tables and seed sample data (only if tables are empty)."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Create tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        quantity INTEGER NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS borrowed_books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT NOT NULL,
        book_id INTEGER,
        borrow_date TEXT,
        return_date TEXT,
        fine REAL DEFAULT 0,
        FOREIGN KEY (book_id) REFERENCES books(id)
    )
    """)

    # sample books if none exist
    cur.execute("SELECT COUNT(*) FROM books")
    if cur.fetchone()[0] == 0:
        sample_books = [
            ("Learn Python", 3),
            ("Database Systems", 2),
            ("Intro to Algorithms", 1),
            ("Effective Java", 2),
            ("Clean Code", 1),
        ]
        cur.executemany("INSERT INTO books (title, quantity) VALUES (?, ?)", sample_books)

    # few borrowed records if none exist
    cur.execute("SELECT COUNT(*) FROM borrowed_books")
    if cur.fetchone()[0] == 0:
        # sample borrow_date and return_date formatted as MM/DD/YY
        samples = [
            ("Alice Johnson", 1, date(2025, 6, 1).strftime("%m/%d/%y"), date(2025, 6, 10).strftime("%m/%d/%y"), 0.0),
            ("Bob Smith", 2, date(2025, 6, 5).strftime("%m/%d/%y"), date(2025, 6, 12).strftime("%m/%d/%y"), 0.0),
        ]
        cur.executemany(
            "INSERT INTO borrowed_books (student_name, book_id, borrow_date, return_date, fine) VALUES (?, ?, ?, ?, ?)",
            samples
        )
        # Decrease quantities of those borrowed sample books
        cur.execute("UPDATE books SET quantity = quantity - 1 WHERE id = 1")
        cur.execute("UPDATE books SET quantity = quantity - 1 WHERE id = 2")

    conn.commit()
    conn.close()


def calc_fine_for_dates(return_date_str):
    """Given a return_date string 'MM/DD/YY', compute fine (R5/day) if return date < today."""
    try:
        ret = datetime.strptime(return_date_str, "%m/%d/%y").date()
    except Exception:
        return 0.0
    today = date.today()
    if ret < today:
        days_late = (today - ret).days
        return round(days_late * FINE_PER_DAY, 2)
    return 0.0


class LibraryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Student Book Tracker - Library Manager")
        self.geometry("1000x600")
        self.resizable(True, True)

        # DB connection object per GUI
        self.conn = sqlite3.connect(DB_FILE)
        self.cur = self.conn.cursor()

        self.create_widgets()
        self.refresh_books_combobox()
        self.refresh_table()

    def create_widgets(self):
        # Main frames
        left_frame = ttk.Frame(self, padding=(10, 10))
        left_frame.pack(side=tk.LEFT, fill=tk.Y)

        right_frame = ttk.Frame(self, padding=(10, 10))
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # LabelFrame for Borrow Book form
        form_lf = ttk.LabelFrame(left_frame, text="Borrow Book", padding=(10, 10))
        form_lf.pack(fill=tk.Y, expand=False)

        # Student name
        ttk.Label(form_lf, text="Student Name:").grid(row=0, column=0, sticky=tk.W, pady=(0, 6))
        self.student_entry = ttk.Entry(form_lf, width=30)
        self.student_entry.grid(row=0, column=1, pady=(0, 6))

        # Book combobox
        ttk.Label(form_lf, text="Book:").grid(row=1, column=0, sticky=tk.W, pady=(0, 6))
        self.book_var = tk.StringVar()
        self.book_combobox = ttk.Combobox(form_lf, textvariable=self.book_var, width=28, state="readonly")
        self.book_combobox.grid(row=1, column=1, pady=(0, 6))

        # Borrow date
        ttk.Label(form_lf, text="Borrow Date:").grid(row=2, column=0, sticky=tk.W, pady=(0, 6))
        self.borrow_date = DateEntry(form_lf, date_pattern="mm/dd/yy")
        self.borrow_date.set_date(date.today())
        self.borrow_date.grid(row=2, column=1, pady=(0, 6))

        # Return date
        ttk.Label(form_lf, text="Return Date:").grid(row=3, column=0, sticky=tk.W, pady=(0, 6))
        self.return_date = DateEntry(form_lf, date_pattern="mm/dd/yy")
        self.return_date.set_date(date.today())
        self.return_date.grid(row=3, column=1, pady=(0, 6))

        # Action buttons
        btn_frame = ttk.Frame(form_lf)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0))

        self.add_btn = tk.Button(btn_frame, text="Add", bg="#2ecc71", fg="white", width=10, command=self.add_record)
        self.add_btn.grid(row=0, column=0, padx=(0, 8))

        self.delete_btn = tk.Button(btn_frame, text="Delete", bg="#e74c3c", fg="white", width=10, command=self.delete_record)
        self.delete_btn.grid(row=0, column=1, padx=(0, 8))

        self.clear_btn = tk.Button(btn_frame, text="Clear", bg="#95a5a6", fg="white", width=10, command=self.clear_form)
        self.clear_btn.grid(row=0, column=2)

        # Right frame: Search, total count, Treeview
        search_frame = ttk.Frame(right_frame)
        search_frame.pack(fill=tk.X)

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 6))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_table())

        # Total label
        self.total_label = ttk.Label(search_frame, text="Total Borrowed Books: 0")
        self.total_label.pack(side=tk.RIGHT, padx=(6, 0))

        # Table (Treeview) with scrollbar
        table_frame = ttk.Frame(right_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        columns = ("ID", "Student", "Book", "Borrow Date", "Return Date", "Fine")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        # Column config
        self.tree.column("ID", width=50, anchor=tk.CENTER)
        self.tree.column("Student", width=200, anchor=tk.W)
        self.tree.column("Book", width=220, anchor=tk.W)
        self.tree.column("Borrow Date", width=100, anchor=tk.CENTER)
        self.tree.column("Return Date", width=100, anchor=tk.CENTER)
        self.tree.column("Fine", width=80, anchor=tk.E)

        # Headings
        for col in columns:
            self.tree.heading(col, text=col)

        # Style the header
        style = ttk.Style(self)
        style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"), foreground="white", background="#1E90FF")
        try:
            style.layout("Treeview.Heading", [('Treeheading.cell', {'sticky': 'nswe'}),
                                             ('Treeheading.border', {'sticky': 'nswe', 'children':
                                                 [('Treeheading.padding', {'sticky': 'nswe', 'children':
                                                     [('Treeheading.image', {'side': 'right', 'sticky': ''}),
                                                      ('Treeheading.text', {'sticky': 'we'})]
                                                 })]
                                             })])
        except Exception:
            pass

        # Tags for late rows
        self.tree.tag_configure("late", background="#ffcccc")  # light red for overdue
        self.tree.tag_configure("normal", background="white")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    def refresh_books_combobox(self):
        """Populate combobox with books that have quantity > 0."""
        self.cur.execute("SELECT id, title, quantity FROM books WHERE quantity > 0")
        rows = self.cur.fetchall()
        self.books_map = {}
        titles = []
        for r in rows:
            bid, title, qty = r
            display = f"{title} (Available: {qty})"
            titles.append(display)
            self.books_map[display] = bid
        self.book_combobox['values'] = titles
        if titles:
            self.book_combobox.current(0)
        else:
            self.book_combobox.set("")

    def refresh_table(self):
        """Load borrowed_books (joined with books.title) and filter by search string."""
        search = self.search_var.get().strip().lower()
        query = """
            SELECT bb.id, bb.student_name, b.title, bb.borrow_date, bb.return_date, bb.fine
            FROM borrowed_books bb
            LEFT JOIN books b ON bb.book_id = b.id
        """
        params = ()
        if search:
            query += " WHERE LOWER(bb.student_name) LIKE ? OR LOWER(b.title) LIKE ?"
            like = f"%{search}%"
            params = (like, like)
        query += " ORDER BY bb.id ASC"
        self.cur.execute(query, params)
        rows = self.cur.fetchall()

        # Clear existing
        for r in self.tree.get_children():
            self.tree.delete(r)

        for row in rows:
            rid, student, title, borrow_date, return_date, fine = row
            tag = "late" if (fine is not None and fine > 0) else "normal"
            # Format fine to two decimals
            fine_fmt = f"R{fine:.2f}" if fine is not None else "R0.00"
            self.tree.insert("", tk.END, values=(rid, student, title or "Unknown", borrow_date, return_date, fine_fmt), tags=(tag,))

        self.total_label.config(text=f"Total Borrowed Books: {len(rows)}")

    def add_record(self):
        """Add new borrow record with validation, decrease book quantity, compute fine if return date passed."""
        student = self.student_entry.get().strip()
        book_display = self.book_var.get().strip()
        borrow_d_str = self.borrow_date.get_date().strftime("%m/%d/%y")
        return_d_str = self.return_date.get_date().strftime("%m/%d/%y")

        # Validations
        if not student:
            messagebox.showerror("Validation Error", "Please enter the student's name.")
            return
        if not book_display:
            messagebox.showerror("Validation Error", "Please select a book (available books only).")
            return

        # Map display back to book id
        book_id = self.books_map.get(book_display)
        if not book_id:
            messagebox.showerror("Validation Error", "Selected book is not available.")
            self.refresh_books_combobox()
            return

        # Borrow date cannot be in the past
        borrow_date_obj = datetime.strptime(borrow_d_str, "%m/%d/%y").date()
        today = date.today()
        if borrow_date_obj < today:
            messagebox.showerror("Validation Error", "Borrow Date cannot be in the past.")
            return

        # Return date cannot be before borrow date
        return_date_obj = datetime.strptime(return_d_str, "%m/%d/%y").date()
        if return_date_obj < borrow_date_obj:
            messagebox.showerror("Validation Error", "Return Date cannot be before the Borrow Date.")
            return

        # Calculate fine (if return date already passed)
        fine = calc_fine_for_dates(return_d_str)

        # Insert into DB
        try:
            self.cur.execute(
                "INSERT INTO borrowed_books (student_name, book_id, borrow_date, return_date, fine) VALUES (?, ?, ?, ?, ?)",
                (student, book_id, borrow_d_str, return_d_str, fine)
            )
            # Decrease book quantity by 1
            self.cur.execute("UPDATE books SET quantity = quantity - 1 WHERE id = ?", (book_id,))
            self.conn.commit()
        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to add record: {e}")
            self.conn.rollback()
            return

        messagebox.showinfo("Success", "Borrow record added.")
        self.clear_form()
        self.refresh_books_combobox()
        self.refresh_table()

    def delete_record(self):
        """Delete selected borrowed_book record after confirmation; increase book quantity by 1."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Delete", "Please select a record in the table to delete.")
            return
        item = sel[0]
        values = self.tree.item(item, "values")
        record_id = values[0]

        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete record ID {record_id}?")
        if not confirm:
            return

        try:
            # Get book_id of the record to increase quantity
            self.cur.execute("SELECT book_id FROM borrowed_books WHERE id = ?", (record_id,))
            row = self.cur.fetchone()
            if row:
                book_id = row[0]
                # Delete record
                self.cur.execute("DELETE FROM borrowed_books WHERE id = ?", (record_id,))
                # Increase book quantity by 1 (only if book_id exists)
                if book_id:
                    self.cur.execute("UPDATE books SET quantity = quantity + 1 WHERE id = ?", (book_id,))
                self.conn.commit()
                messagebox.showinfo("Deleted", "Record deleted and book quantity updated.")
            else:
                messagebox.showwarning("Not Found", "Record not found in database.")
        except Exception as e:
            messagebox.showerror("DB Error", f"Could not delete record: {e}")
            self.conn.rollback()
            return

        self.refresh_books_combobox()
        self.refresh_table()

    def clear_form(self):
        """Clear text entry and reset dates to today."""
        self.student_entry.delete(0, tk.END)
        if self.book_combobox['values']:
            self.book_combobox.current(0)
        self.borrow_date.set_date(date.today())
        self.return_date.set_date(date.today())

    def on_tree_select(self, event):
        """When a row is selected, populate form fields (convenience)"""
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0], "values")
        if not values:
            return
        record_id, student, book_title, borrow_d, return_d, fine_fmt = values
        # Populate student
        self.student_entry.delete(0, tk.END)
        self.student_entry.insert(0, student)
        # Try to set the combobox to matching available string; if book isn't currently available, still show title
        # We'll attempt to set to a value in the books_map that contains the book title
        found_key = None
        for k in self.books_map.keys():
            if book_title in k:
                found_key = k
                break
        if found_key:
            self.book_combobox.set(found_key)
        else:
            # no matching available book (it might be currently 0 quantity), set raw title (readonly prevents typing)
            self.book_combobox.set(book_title)
        # Set dates
        try:
            bdt = datetime.strptime(borrow_d, "%m/%d/%y").date()
            rdt = datetime.strptime(return_d, "%m/%d/%y").date()
            self.borrow_date.set_date(bdt)
            self.return_date.set_date(rdt)
        except Exception:
            pass

    def on_close(self):
        """Cleanup DB connection when closing app."""
        self.conn.close()
        self.destroy()


if __name__ == "__main__":
    # Initialize DB and start app
    init_db()
    app = LibraryApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
