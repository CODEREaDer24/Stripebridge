from flask import Flask, render_template, request, redirect, session, url_for, flash
import stripe
import os
from dotenv import load_dotenv
from functools import wraps

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Example route: Home
@app.route("/")
def index():
    return render_template("index.html")

# Example route: Dashboard (protected)
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

# Example login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        # Normally you'd validate against a database
        session["user"] = username
        flash("Logged in successfully!", "success")
        return redirect(url_for("dashboard"))
    return render_template("request_trial.html")

# Logout route
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("index"))

# Required for Render to pick up the correct port
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
