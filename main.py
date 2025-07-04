from flask import Flask, render_template, request, redirect, session, url_for, flash
import stripe
import os
from dotenv import load_dotenv
from functools import wraps
import requests

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_CLIENT_ID = os.getenv("STRIPE_CLIENT_ID")
YOUR_DOMAIN = os.getenv("YOUR_DOMAIN") or "http://localhost:10000"

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
            USERS[email] = {"links": [], "stripe_user_id": None}
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
    user_data = USERS.get(email, {})
    links = user_data.get("links", [])
    connected = bool(user_data.get("stripe_user_id"))
    return render_template("dashboard.html", links=links, connected=connected)

@app.route("/connect")
@login_required
def connect():
    connect_url = (
        f"https://connect.stripe.com/oauth/authorize?response_type=code"
        f"&client_id={STRIPE_CLIENT_ID}"
        f"&scope=read_write"
        f"&redirect_uri={YOUR_DOMAIN}/connect/callback"
    )
    return redirect(connect_url)

@app.route("/connect/callback")
@login_required
def connect_callback():
    code = request.args.get("code")
    if not code:
        flash("Connection failed.", "danger")
        return redirect(url_for("dashboard"))

    try:
        response = requests.post(
            "https://connect.stripe.com/oauth/token",
            data={
                "client_secret": stripe.api_key,
                "code": code,
                "grant_type": "authorization_code"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response_data = response.json()
        stripe_user_id = response_data.get("stripe_user_id")

        if stripe_user_id:
            USERS[session["user"]]["stripe_user_id"] = stripe_user_id
            flash("Stripe connected successfully!", "success")
        else:
            flash("Stripe connection error.", "danger")
    except Exception as e:
        flash(f"OAuth error: {str(e)}", "danger")

    return redirect(url_for("dashboard"))

@app.route("/generate-link", methods=["POST"])
@login_required
def generate_link():
    email = session["user"]
    user_data = USERS[email]
    stripe_user_id = user_data.get("stripe_user_id")

    if not stripe_user_id:
        flash("Please connect your Stripe account first.", "warning")
        return redirect(url_for("dashboard"))

    try:
        name = request.form["name"]
        price = int(float(request.form["price"]) * 100)
        description = request.form["description"]

        product = stripe.Product.create(name=name, description=description, stripe_account=stripe_user_id)
        price_obj = stripe.Price.create(product=product.id, unit_amount=price, currency="usd", stripe_account=stripe_user_id)
        link = stripe.PaymentLink.create(line_items=[{"price": price_obj.id, "quantity": 1}], stripe_account=stripe_user_id)

        user_data["links"].append({
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
