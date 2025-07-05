from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure key

# --- SQLite DB setup ---
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- Create user table if not exists ---
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- SIGNUP route ---
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        hashed_pw = generate_password_hash(password)

        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, hashed_pw))
            conn.commit()
            conn.close()
            session['user'] = email
            return redirect('/dashboard')
        except sqlite3.IntegrityError:
            flash('Email already registered.')
            return redirect('/signup')
    return render_template('signup.html')

# --- LOGIN route ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user'] = user['email']
            return redirect('/dashboard')
        else:
            flash('Invalid login credentials.')
            return redirect('/login')
    return render_template('login.html')

# --- DASHBOARD route (basic auth check) ---
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    return f"<h2>Welcome, {session['user']}!<br><a href='/logout'>Logout</a></h2>"

# --- LOGOUT route ---
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')
