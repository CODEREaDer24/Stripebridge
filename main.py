from flask import Flask, render_template, request, redirect, session, url_for, flash import stripe import os from dotenv import load_dotenv from functools import wraps

load_dotenv()

app = Flask(name) app.secret_key = os.getenv('FLASK_SECRET_KEY', 'supersecret')

Stripe config

stripe.api_key = os.getenv('STRIPE_SECRET_KEY') YOUR_DOMAIN = os.getenv('YOUR_DOMAIN', 'https://nocodepay.xyz')

Temporary mock user DB

USERS = { "test@example.com": { "password": "1234", "links": [], "plan": "free"  # mock plan tiers } } PLAN_LIMITS = { "free": 1, "pro": 5, "team": 20 }

Auth check

def login_required(f): @wraps(f) def decorated(*args, **kwargs): if 'user' not in session: flash('Please log in first.') return redirect(url_for('login')) return f(*args, **kwargs) return decorated

@app.route('/') def index(): return render_template('index.html')

@app.route('/login', methods=['GET', 'POST']) def login(): if request.method == 'POST': email = request.form['email'] password = request.form['password'] user = USERS.get(email) if user and user['password'] == password: session['user'] = email flash('Logged in successfully.') return redirect(url_for('dashboard')) flash('Invalid login.') return render_template('login.html')

@app.route('/logout') def logout(): session.pop('user', None) flash('Logged out.') return redirect(url_for('index'))

@app.route('/dashboard') @login_required def dashboard(): user = USERS[session['user']] return render_template('dashboard.html', links=user['links'])

@app.route('/generate-link', methods=['POST']) @login_required def generate_link(): user_email = session['user'] user = USERS[user_email] limit = PLAN_LIMITS.get(user.get('plan', 'free'), 1)

if len(user['links']) >= limit:
    flash(f"Link limit reached for your plan ({user['plan']}).")
    return redirect(url_for('dashboard'))

try:
    product_name = request.form['name']
    price = int(float(request.form['price']) * 100)
    description = request.form['description']

    product = stripe.Product.create(name=product_name, description=description)
    price_obj = stripe.Price.create(product=product.id, unit_amount=price, currency="usd")
    link = stripe.PaymentLink.create(line_items=[{"price": price_obj.id, "quantity": 1}])

    user['links'].append({
        'name': product_name,
        'price': f"${price/100:.2f}",
        'description': description,
        'url': link.url
    })

    flash("Payment link created!")
except Exception as e:
    flash(f"Error creating link: {str(e)}")

return redirect(url_for('dashboard'))

if name == 'main': app.run(host="0.0.0.0", port=10000)

