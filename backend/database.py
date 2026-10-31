"""
Database Management Module for Personal Finance Management System
Uses SQLite3 for fast, reliable, zero-config local storage.
"""

import sqlite3
import os
import hashlib
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'finance_system.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = "finance_secure_salt_2026"
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def init_db():
    """Create all required tables according to the system flowchart and requirements."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            monthly_income REAL DEFAULT 35000.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Transactions Table (Income & Expenses)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
            category TEXT NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0),
            payment_mode TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # 3. Budgets Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            monthly_limit REAL NOT NULL CHECK(monthly_limit >= 0),
            month_year TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, category, month_year),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # 4. Predictions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            predicted_expense REAL NOT NULL,
            income_input REAL NOT NULL,
            prev_expense_input REAL NOT NULL,
            mae REAL,
            rmse REAL,
            r2_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()

def register_user(name: str, email: str, password: str, monthly_income: float = 0.0):
    """Register a new user starting with zero balance by default."""
    conn = get_connection()
    cursor = conn.cursor()
    pwd_hash = hash_password(password)
    try:
        cursor.execute(
            'INSERT INTO users (name, email, password_hash, monthly_income) VALUES (?, ?, ?, ?)',
            (name.strip(), email.strip().lower(), pwd_hash, float(monthly_income))
        )
        user_id = cursor.lastrowid
        conn.commit()
        return {'id': user_id, 'name': name, 'email': email.lower(), 'monthly_income': float(monthly_income)}
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def login_user(email: str, password: str):
    """Authenticate a user by email and password."""
    conn = get_connection()
    cursor = conn.cursor()
    pwd_hash = hash_password(password)
    cursor.execute(
        'SELECT id, name, email, monthly_income, created_at FROM users WHERE email = ? AND password_hash = ?',
        (email.strip().lower(), pwd_hash)
    )
    user = cursor.fetchone()
    conn.close()
    if user:
        return dict(user)
    return None

def get_user_by_id(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, email, monthly_income, created_at FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_by_email(email: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, email, monthly_income, created_at FROM users WHERE email = ?', (email.strip().lower(),))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def update_user_income(user_id: int, new_income: float):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET monthly_income = ? WHERE id = ?', (float(new_income), user_id))
    conn.commit()
    conn.close()

# ----------------- Transaction CRUD -----------------

def add_transaction(user_id: int, date: str, type_: str, category: str, amount: float, payment_mode: str, description: str = ''):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (user_id, date, type, category, amount, payment_mode, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, date, type_.lower(), category, float(amount), payment_mode, description))
    tx_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return tx_id

def get_transactions(user_id: int, start_date=None, end_date=None, category=None, type_=None, limit=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = 'SELECT * FROM transactions WHERE user_id = ?'
    params = [user_id]

    if start_date:
        query += ' AND date >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND date <= ?'
        params.append(end_date)
    if category and category.lower() != 'all':
        query += ' AND category = ?'
        params.append(category)
    if type_ and type_.lower() != 'all':
        query += ' AND type = ?'
        params.append(type_.lower())

    query += ' ORDER BY date DESC, id DESC'
    if limit:
        query += ' LIMIT ?'
        params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_transaction_by_id(tx_id: int, user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM transactions WHERE id = ? AND user_id = ?', (tx_id, user_id))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_transaction(tx_id: int, user_id: int, date: str, type_: str, category: str, amount: float, payment_mode: str, description: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE transactions
        SET date = ?, type = ?, category = ?, amount = ?, payment_mode = ?, description = ?
        WHERE id = ? AND user_id = ?
    ''', (date, type_.lower(), category, float(amount), payment_mode, description, tx_id, user_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def delete_transaction(tx_id: int, user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transactions WHERE id = ? AND user_id = ?', (tx_id, user_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

# ----------------- Budgets CRUD -----------------

def set_budget(user_id: int, category: str, monthly_limit: float, month_year: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO budgets (user_id, category, monthly_limit, month_year)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, category, month_year)
        DO UPDATE SET monthly_limit = excluded.monthly_limit
    ''', (user_id, category, float(monthly_limit), month_year))
    conn.commit()
    conn.close()
    return True

def get_budgets(user_id: int, month_year: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM budgets WHERE user_id = ? AND month_year = ?
    ''', (user_id, month_year))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_budget_status(user_id: int, month_year: str):
    """
    Returns each category's budget, amount spent in that month,
    remaining amount, and percentage used.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Get budgets
    cursor.execute('SELECT category, monthly_limit FROM budgets WHERE user_id = ? AND month_year = ?', (user_id, month_year))
    budgets = {row['category']: row['monthly_limit'] for row in cursor.fetchall()}

    # Get actual spending in this month
    cursor.execute('''
        SELECT category, SUM(amount) as total_spent
        FROM transactions
        WHERE user_id = ? AND type = 'expense' AND date LIKE ?
        GROUP BY category
    ''', (user_id, f'{month_year}%'))
    spending = {row['category']: row['total_spent'] for row in cursor.fetchall()}
    conn.close()

    # Combine categories
    all_categories = sorted(list(set(list(budgets.keys()) + list(spending.keys()))))
    status_list = []
    total_budget = 0.0
    total_spent = 0.0

    for cat in all_categories:
        limit = budgets.get(cat, 0.0)
        spent = spending.get(cat, 0.0)
        remaining = limit - spent
        percent = round((spent / limit * 100), 1) if limit > 0 else (100.0 if spent > 0 else 0.0)

        total_budget += limit
        total_spent += spent

        status_list.append({
            'category': cat,
            'limit': limit,
            'spent': spent,
            'remaining': remaining,
            'percent_used': percent,
            'is_over_budget': spent > limit if limit > 0 else (spent > 0)
        })

    return {
        'month_year': month_year,
        'categories': status_list,
        'total_budget': total_budget,
        'total_spent': total_spent,
        'total_remaining': total_budget - total_spent,
        'total_percent': round((total_spent / total_budget * 100), 1) if total_budget > 0 else 0.0
    }

# ----------------- Predictions -----------------

def save_prediction(user_id: int, predicted_expense: float, income_input: float, prev_expense_input: float, mae: float, rmse: float, r2_score: float):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO predictions (user_id, predicted_expense, income_input, prev_expense_input, mae, rmse, r2_score)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, predicted_expense, income_input, prev_expense_input, mae, rmse, r2_score))
    pred_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return pred_id

def get_prediction_history(user_id: int, limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM predictions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
    ''', (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ----------------- Demo Data Seeding -----------------

def seed_demo_data(user_id: int):
    """Populates initial realistic demo data if user has no transactions."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as cnt FROM transactions WHERE user_id = ?', (user_id,))
    cnt = cursor.fetchone()['cnt']
    if cnt > 0:
        conn.close()
        return False # Already has data

    demo_transactions = [
        # Current month: 2026-10
        ('2026-10-01', 'income', 'Salary', 42000, 'Net Banking', 'Monthly Salary Direct Deposit'),
        ('2026-10-02', 'expense', 'Bills', 12000, 'Net Banking', 'Apartment Rent & Society Maintenance'),
        ('2026-10-03', 'expense', 'Food', 2450, 'UPI', 'Supermarket Monthly Groceries'),
        ('2026-10-05', 'expense', 'Bills', 1850, 'UPI', 'Electricity & High Speed Fiber Bill'),
        ('2026-10-07', 'expense', 'Transport', 650, 'UPI', 'Shell Station Fuel & Petrol'),
        ('2026-10-09', 'expense', 'Entertainment', 499, 'Credit Card', 'Netflix Premium Streaming'),
        ('2026-10-12', 'expense', 'Food', 1280, 'Debit Card', 'Weekend Dining at Olive Bistro'),
        ('2026-10-14', 'expense', 'Shopping', 3450, 'Credit Card', 'Festival Clothes & Footwear'),
        ('2026-10-15', 'income', 'Freelance', 8500, 'UPI', 'UI/UX Consulting Project Milestone'),
        ('2026-10-18', 'expense', 'Healthcare', 1500, 'Debit Card', 'Dental Routine Checkup & Pharmacy'),
        ('2026-10-21', 'expense', 'Education', 1999, 'Credit Card', 'Machine Learning & Python Masterclass'),
        ('2026-10-23', 'expense', 'Transport', 850, 'UPI', 'Metro Card Recharge & Cab Rides'),
        ('2026-10-25', 'expense', 'Food', 1650, 'Cash', 'Weekly Organic Fresh Produce'),
        ('2026-10-27', 'expense', 'Other', 950, 'UPI', 'Home Maintenance & Repair'),

        # Previous month: 2026-09
        ('2026-09-01', 'income', 'Salary', 42000, 'Net Banking', 'Monthly Salary Direct Deposit'),
        ('2026-09-02', 'expense', 'Bills', 12000, 'Net Banking', 'Monthly Apartment Rent'),
        ('2026-09-05', 'expense', 'Bills', 1780, 'UPI', 'Electricity & Internet Bill'),
        ('2026-09-08', 'expense', 'Food', 3200, 'UPI', 'Whole Foods Groceries'),
        ('2026-09-12', 'expense', 'Transport', 1200, 'UPI', 'Gasoline & City Commute'),
        ('2026-09-15', 'income', 'Freelance', 6000, 'Net Banking', 'Software Consulting Retainer'),
        ('2026-09-18', 'expense', 'Entertainment', 1450, 'Credit Card', 'Movie IMAX Tickets & Snacks'),
        ('2026-09-22', 'expense', 'Shopping', 4200, 'Credit Card', 'Electronics & Wireless Earbuds'),
        ('2026-09-26', 'expense', 'Healthcare', 800, 'Cash', 'Medical Vitamins & Supplements'),

        # Prior month: 2026-08
        ('2026-08-01', 'income', 'Salary', 42000, 'Net Banking', 'Monthly Salary Direct Deposit'),
        ('2026-08-02', 'expense', 'Bills', 12000, 'Net Banking', 'Monthly Apartment Rent'),
        ('2026-08-06', 'expense', 'Food', 3800, 'Debit Card', 'Monthly Groceries & Dining'),
        ('2026-08-11', 'expense', 'Transport', 1100, 'UPI', 'Fuel Refill'),
        ('2026-08-16', 'expense', 'Shopping', 2800, 'Credit Card', 'Office Desk Chair'),
        ('2026-08-20', 'expense', 'Entertainment', 999, 'Debit Card', 'Concert Pass'),
        ('2026-08-25', 'expense', 'Bills', 1650, 'UPI', 'Utility Bills')
    ]

    for tx in demo_transactions:
        cursor.execute('''
            INSERT INTO transactions (user_id, date, type, category, amount, payment_mode, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, tx[0], tx[1], tx[2], tx[3], tx[4], tx[5]))

    # Set initial monthly budgets for 2026-10
    default_budgets = [
        ('Bills', 15000),
        ('Food', 6000),
        ('Transport', 3000),
        ('Shopping', 4000),
        ('Entertainment', 2000),
        ('Healthcare', 2500),
        ('Education', 3000),
        ('Other', 1500)
    ]
    current_my = datetime.now().strftime('%Y-%m')
    for cat, limit in default_budgets:
        cursor.execute('''
            INSERT INTO budgets (user_id, category, monthly_limit, month_year)
            VALUES (?, ?, ?, ?)
        ''', (user_id, cat, limit, current_my))

    conn.commit()
    conn.close()
    return True

