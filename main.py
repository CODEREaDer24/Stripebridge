from flask import Flask, render_template, request, redirect, session, url_for, flash
import stripe
import os
from dotenv import load_dotenv
from functools import wraps

# Load environment variables
load_dotenv()

# Initialize app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")

# Stripe setup
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Temporary mock user DB
USERS = {}

# Decorator to protect routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user"):
            flash("Login required", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        session["user"] = email
        if email not in USERS:
            USERS[email] = []  # Initialize empty link list
        flash("Logged in successfully!", "success")
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    email = session["user"]
    links = USERS.get(email, [])
    return render_template("dashboard.html", links=links)

@app.route("/generate-link", methods=["POST"])
@login_required
def generate_link():
    email = session["user"]
    try:
        name = request.form["name"]
        price = int(float(request.form["price"]) * 100)  # dollars to cents
        description = request.form["description"]

        product = stripe.Product.create(name=name, description=description)
        price_obj = stripe.Price.create(product=product.id, unit_amount=price, currency="usd")
        link = stripe.PaymentLink.create(line_items=[{"price": price_obj.id, "quantity": 1}])

        USERS[email].append({
            "name": name,
            "price": f"${price / 100:.2f}",
            "description": description,
            "url": link.url
        })

        flash("Payment link created!", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")

    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
