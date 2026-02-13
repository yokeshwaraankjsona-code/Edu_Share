"""
Backend for the OTP Login System.
Handles OTP generation, email sending, verification, and user login using MySQL.
"""

# --------------------- IMPORTS ---------------------
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

import smtplib
import random
from email.mime.text import MIMEText

# --------------------- APP CONFIG ---------------------
app = Flask(__name__)

# MySQL Database Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://edushare:1234@localhost/edushare_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '118186f0f222e5eaef2146d7ccaac7'

db = SQLAlchemy(app)
CORS(app)


# --------------------- DATABASE MODEL ---------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


# --------------------- OTP STORAGE ---------------------
otp_store = {}  # temporary storage for email → OTP


# --------------------- EMAIL CONFIG ---------------------
GMAIL = "edushare.2026@gmail.com"
APP_PASSWORD = "qsqg ytvp zluy fpke"  # your Gmail App Password


def send_otp_email(to_email, otp):
    """Send OTP using Gmail SMTP"""
    msg = MIMEText(f"Your OTP is: {otp}")
    msg["Subject"] = "Email Verification OTP"
    msg["From"] = GMAIL
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL, APP_PASSWORD)
        server.send_message(msg)


# --------------------- ROUTES ---------------------

@app.route("/send-otp", methods=["POST"])
def send_otp():
    """Generate and send OTP to email"""
    email = request.json.get("email")

    if not email:
        return jsonify({"message": "Email is required"}), 400

    otp = str(random.randint(100000, 999999))
    otp_store[email] = otp

    try:
        send_otp_email(email, otp)
        print(f"OTP sent to {email}: {otp}")
        return jsonify({"message": "OTP sent successfully!"})
    except Exception as error:
        print(f"Error sending email: {error}")
        return jsonify({"message": "Failed to send OTP"}), 500


@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    """Verify OTP and register user in MySQL"""
    data = request.json
    email = data.get("email")
    user_otp = data.get("otp")
    name = data.get("name")
    password = data.get("password")

    stored_otp = otp_store.get(email)

    if not stored_otp or stored_otp != user_otp:
        return jsonify({"status": "invalid", "message": "Wrong OTP"})

    # OTP valid → delete OTP
    del otp_store[email]

    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"status": "exists", "message": "User already registered!"})

    # Save new user in MySQL
    hashed_password = generate_password_hash(password)
    new_user = User(username=name, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"status": "verified", "message": "Account created successfully!"})


@app.route("/login", methods=["POST"])
def login():
    """Login using MySQL stored credentials"""
    data = request.json
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password):
        return jsonify({"message": "success", "name": user.username})

    return jsonify({"error": "Invalid email or password"}), 401


@app.route("/")
def home():
    return send_from_directory("static", "index.html")


# --------------------- MAIN ---------------------
if __name__ == "__main__":
    app.run(debug=True)
