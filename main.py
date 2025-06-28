from flask import Flask, request, jsonify
import stripe
import json
import os

app = Flask(__name__)
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_yourkeyhere')

DATA_FILE = 'payments.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET', 'whsec_test')

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        email = session.get('customer_email')
        product = session.get('metadata', {}).get('product_name', 'default')
        data = load_data()
        data[email] = product
        save_data(data)
        print(f'Payment recorded: {email} -> {product}')

    return '', 200

@app.route('/has-paid')
def has_paid():
    email = request.args.get('email')
    product = request.args.get('product')
    data = load_data()
    return jsonify({"paid": data.get(email) == product})

@app.route('/create-checkout', methods=['POST'])
def create_checkout():
    req = request.get_json()
    session = stripe.checkout.Session.create(
        success_url=req['success_url'],
        cancel_url=req['cancel_url'],
        customer_email=req['email'],
        line_items=[{
            'price': req['price_id'],
            'quantity': 1,
        }],
        mode='payment',
        metadata={"product_name": req['product']}
    )
    return jsonify({"url": session.url})

if __name__ == '__main__':
    app.run(debug=True)
