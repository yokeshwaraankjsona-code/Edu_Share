"""
Backend for the OTP Login System.
Handles OTP generation, email sending, verification, and user login.
"""

# 1. Standard library imports come first
import smtplib
import random
from email.mime.text import MIMEText

# 2. Third-party imports come next
from flask import Flask, request, jsonify,  send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
# Temporary storage for OTPs
otp_store = {}

# In-memory database for Users
users_store = {}

GMAIL = "yokeshwaraank@gmail.com"
# GENERATE A NEW APP PASSWORD AND PASTE IT BELOW
APP_PASSWORD = "reuk fcyg kfri ojmu"


def send_otp_email(to_email, otp):
    """Sends the OTP code to the specified email address via SMTP."""
    msg = MIMEText(f"Your OTP is: {otp}")
    msg["Subject"] = "Email Verification OTP"
    msg["From"] = GMAIL
    msg["To"] = to_email

    # Standard Gmail SMTP configuration
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL, APP_PASSWORD)
        server.send_message(msg)


# --- ROUTES ---

@app.route("/send-otp", methods=["POST"])
def send_otp():
    email = request.json.get("email")
    if not email:
        return jsonify({"message": "Email is required"}), 400
    otp = str(random.randint(100000, 999999))
    otp_store[email] = otp

    try:
        send_otp_email(email, otp)
        print(f"OTP sent to {email}: {otp}")  # Console log for debugging
        return jsonify({"message": "OTP sent successfully!"})
    # pylint: disable=broad-exception-caught
    except Exception as error:
        print(f"Error sending email: {error}")
        return jsonify({"message": "Failed to send email"}), 500


@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    """Verifies the OTP and registers the user if valid."""
    data = request.json
    email = data.get("email")
    user_otp = data.get("otp")

    # Capture name and password to save the user
    name = data.get("name")
    password = data.get("password")

    stored_otp = otp_store.get(email)

    if stored_otp and stored_otp == user_otp:
        # OTP is correct -> Create the account
        users_store[email] = {
            "name": name,
            "password": password
        }
        # Clean up used OTP
        del otp_store[email]

        print(f"User registered: {users_store}")  # Debug log
        return jsonify({"status": "verified", "message": "Account created!"})

    return jsonify({"status": "invalid", "message": "Wrong OTP"})


@app.route("/login", methods=["POST"])
def login():
    """Authenticates the user using email and password."""
    data = request.json
    email = data.get("email")
    password = data.get("password")

    # Check if user exists and password matches
    if email in users_store and users_store[email]["password"] == password:
        user_name = users_store[email]["name"]
        return jsonify({"message": "success", "name": user_name})

    return jsonify({"error": "Invalid email or password"}), 401
@app.route("/")
def home():
     return send_from_directory("static", "index.html")
if __name__ == "__main__":
    app.run(debug=True)
