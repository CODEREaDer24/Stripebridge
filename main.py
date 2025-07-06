from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import os
import stripe
from urllib.parse import urlparse

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "changeme123")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_...")

def get_db_connection():
    result = urlparse(os.getenv("DATABASE_URL"))
    return psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )

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
            cur = conn.cursor()
            cur.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, hashed_pw))
            conn.commit()
            cur.close()
            conn.close()
            session['user'] = email
            return redirect('/dashboard')
        except:
            flash('Email already registered.')
            return redirect('/signup')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user'] = user[1]
            return redirect('/dashboard')
        else:
            flash('Invalid login.')
            return redirect('/login')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, url FROM links WHERE email = %s ORDER BY id DESC", (session['user'],))
    links = cur.fetchall()
    cur.execute("SELECT COUNT(*), MAX(created_at) FROM links WHERE email = %s", (session['user'],))
    stats = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('dashboard.html', email=session['user'], links=links, stats=stats)

@app.route('/create_link', methods=['POST'])
def create_link():
    if 'user' not in session:
        return redirect('/login')
    amount = int(float(request.form['amount']) * 100)
    product = stripe.Product.create(name="NoCodePay Link")
    price = stripe.Price.create(product=product.id, unit_amount=amount, currency="usd")
    link = stripe.PaymentLink.create(line_items=[{"price": price.id, "quantity": 1}])
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO links (email, url) VALUES (%s, %s)", (session['user'], link.url))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/dashboard')

@app.route('/delete_link/<int:link_id>', methods=['POST'])
def delete_link(link_id):
    if 'user' not in session:
        return redirect('/login')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM links WHERE id = %s AND email = %s", (link_id, session['user']))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/dashboard')

@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect('/login')
    return render_template('profile.html', email=session['user'])
