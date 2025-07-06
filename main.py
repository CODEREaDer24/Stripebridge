from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import stripe
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "changeme12345")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_YOUR_KEY_HERE")

# --- DB setup ---
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            url TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('index.html')

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

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    conn = get_db_connection()
    links = conn.execute('SELECT * FROM links WHERE email = ?', (session['user'],)).fetchall()
    conn.close()
    return render_template('dashboard.html', email=session['user'], links=links)

@app.route('/create_link', methods=['POST'])
def create_link():
    if 'user' not in session:
        return redirect('/login')

    # Create Stripe product and payment link
    product = stripe.Product.create(name="NoCodePay Custom Link")
    price = stripe.Price.create(
        product=product.id,
        unit_amount=500,  # $5.00
        currency="usd"
    )
    link = stripe.PaymentLink.create(
        line_items=[{"price": price.id, "quantity": 1}]
    )

    conn = get_db_connection()
    conn.execute('INSERT INTO links (email, url) VALUES (?, ?)', (session['user'], link.url))
    conn.commit()
    conn.close()

    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')
