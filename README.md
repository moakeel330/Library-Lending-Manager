# 📚 Library Lending Manager

> A modern, Tkinter-based **Library Management System** that tracks book lending, calculates fines, and manages inventory with a clean graphical interface.

---

## 🖥️ Overview

**Library Lending Manager** is a Python desktop application built with **Tkinter** and **SQLite3**.  
It provides an intuitive interface for managing a small library’s borrowed books, tracking student borrowings, handling return dates, and automatically calculating late fines.

The app automatically creates and maintains a local `library.db` file with tables for **books** and **borrowed records**, seeded with sample data on first run.

---

## ✨ Features

### 🧾 Borrowing System
- Record new borrowings with student name, selected book, and borrow/return dates.
- Prevents borrowing unavailable books.
- Validates dates (no past borrow dates or invalid return dates).

### 💰 Fine Calculation
- Automatically calculates fines for late returns.
- R5 per day overdue.
- Overdue rows are highlighted in red in the table view.

### 📚 Inventory Management
- Decreases quantity when books are borrowed.
- Increases quantity when records are deleted.
- Only displays books with available stock.

### 🔍 Smart Search
- Live search bar for **student names** or **book titles**.
- Instantly filters the Treeview display.

### 🧑‍💻 User Interface
- Built using **Tkinter + ttk** for a clean native look.
- Uses **tkcalendar** for date selection.
- Add / Delete / Clear actions for easy record management.
- Displays a live total count of borrowed books.

---

## 🧰 Tech Stack

| Component | Technology |
|------------|-------------|
| **Language** | Python 3 |
| **Database** | SQLite3 |
| **GUI Framework** | Tkinter |
| **Calendar Widget** | tkcalendar |
| **Styling** | ttk (Themed Tkinter Widgets) |

---

##⚙️ Setup & Installation

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/moakeel330/Library-Lending-Manager.git
cd Library-Lending-Manager
```

### 2️⃣ Install Required Packages

Make sure you have Python 3 installed, then run:

```
pip install tkcalendar
```
### 3️⃣ Run the Application
```
python library_manager.py
```
On first launch:
- The app creates library.db
- Seeds sample books and borrowed records
- Starts the GUI automatically

## 🧱 Database Schema
Table: books
| Column | Type | Description
|------------|-------------|------------|
| id | INTEGER | Primary key |
| title | TEXT | Book title |
| quantity | INTEGER | Available copies |

Table: borrowed_books
| Column | Type | Description
|------------|-------------|------------|
| id | INTEGER | Primary key |
| student_name | TEXT | Borrower name |
| book_id | INTEGER | Linked to books(id) |
| borrow_date | TEXT | Date borrowed |
| return_date | TEXT | Date to return |
| fine | REAL | Calculated fine |


