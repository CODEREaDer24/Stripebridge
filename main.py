from flask import Flask, render_template, redirect, url_for, session
import os

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    # Placeholder login – redirect to dashboard for now
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    # Placeholder dashboard page
    return render_template('dashboard.html')

@app.route('/request-trial')
def request_trial():
    return render_template('request_trial.html')

if __name__ == '__main__':
    app.run(debug=True)
