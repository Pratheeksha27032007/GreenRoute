import os
import secrets
import smtplib
import sqlite3
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from functools import wraps

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash


from scheduler import schedule_task, schedule_workflow
from gemini_analyzer import analyze_task
from offline_analyzer import analyze_task_offline

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("GREENROUTE_SECRET_KEY", "dev-only-change-this-key")
CORS(app, supports_credentials=True)

DATABASE = os.path.join(os.path.dirname(__file__), "greenroute.db")
OTP_TTL_SECONDS = 300
OTP_MAX_ATTEMPTS = 5


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_db() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS login_otps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                otp_hash TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                attempts INTEGER DEFAULT 0,
                used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )


def send_otp_email(email, otp):
    smtp_host = os.getenv("SMTP_HOST")
    if not smtp_host:
        print(f"OTP for {email}: {otp}")
        return "console"

    message = EmailMessage()
    message["Subject"] = "Your GreenRoute login code"
    message["From"] = os.getenv("SMTP_FROM", os.getenv("SMTP_USERNAME", ""))
    message["To"] = email
    message.set_content(
        f"Your GreenRoute login code is {otp}. It expires in 5 minutes.\n\n"
        "If you did not request this code, you can ignore this email."
    )

    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as smtp:
        smtp.starttls()
        if smtp_username and smtp_password:
            smtp.login(smtp_username, smtp_password)
        smtp.send_message(message)
    return "email"


def create_login_otp(user_id, email):
    otp = f"{secrets.randbelow(1_000_000):06d}"
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=OTP_TTL_SECONDS)
    with get_db() as connection:
        connection.execute(
            "UPDATE login_otps SET used = 1 WHERE user_id = ? AND used = 0",
            (user_id,),
        )
        connection.execute(
            "INSERT INTO login_otps (user_id, otp_hash, expires_at) VALUES (?, ?, ?)",
            (user_id, generate_password_hash(otp), expires_at.isoformat()),
        )
    delivery = send_otp_email(email, otp)
    session["pending_login_user_id"] = user_id
    session["pending_login_email"] = email
    return delivery


def login_required(route):
    @wraps(route)
    def wrapped_route(*args, **kwargs):
        if session.get("auth_level") != "otp" or "user_id" not in session:
            return jsonify({"message": "Authentication required"}), 401
        return route(*args, **kwargs)

    return wrapped_route


initialize_database()


@app.route("/")
def home():
    return {
        "message": "GreenRoute Scheduler API is running"
    }


@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or "@" not in email:
        return jsonify({"message": "Enter a valid email address"}), 400
    if len(password) < 8:
        return jsonify({"message": "Password must be at least 8 characters"}), 400

    try:
        with get_db() as connection:
            connection.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, generate_password_hash(password)),
            )
    except sqlite3.IntegrityError:
        return jsonify({"message": "An account with that email already exists"}), 409

    return jsonify({
        "email": email,
        "message": "Account created. Sign in to receive a verification code.",
    }), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    session.pop("user_id", None)
    session.pop("email", None)
    session.pop("auth_level", None)
    session.pop("pending_login_user_id", None)
    session.pop("pending_login_email", None)

    with get_db() as connection:
        user = connection.execute(
            "SELECT id, email, password_hash FROM users WHERE email = ?",
            (email,),
        ).fetchone()

    if user is None or not check_password_hash(user["password_hash"], password):
        return jsonify({"message": "Invalid email or password"}), 401

    try:
        delivery = create_login_otp(user["id"], user["email"])
    except (OSError, smtplib.SMTPException, ValueError) as error:
        print(f"OTP email delivery failed: {type(error).__name__}: {error}")
        return jsonify({"message": "Unable to deliver the verification code"}), 503

    return jsonify({
        "otp_required": True,
        "email": user["email"],
        "delivery": delivery,
        "expires_in": OTP_TTL_SECONDS,
    })


@app.route("/api/auth/verify-otp", methods=["POST"])
def verify_otp():
    pending_user_id = session.get("pending_login_user_id")
    pending_email = session.get("pending_login_email")
    data = request.get_json(silent=True) or {}
    otp = str(data.get("otp", "")).strip()

    if not pending_user_id or not pending_email:
        return jsonify({"message": "Start login again to request a verification code"}), 401
    if len(otp) != 6 or not otp.isdigit():
        return jsonify({"message": "Enter the 6-digit verification code"}), 400

    with get_db() as connection:
        challenge = connection.execute(
            """
            SELECT id, otp_hash, expires_at, attempts
            FROM login_otps
            WHERE user_id = ? AND used = 0
            ORDER BY id DESC LIMIT 1
            """,
            (pending_user_id,),
        ).fetchone()

        if challenge is None:
            return jsonify({"message": "Verification code expired. Request a new one"}), 401
        if challenge["attempts"] >= OTP_MAX_ATTEMPTS:
            return jsonify({"message": "Too many attempts. Request a new code"}), 429
        if datetime.fromisoformat(challenge["expires_at"]) < datetime.now(timezone.utc):
            connection.execute("UPDATE login_otps SET used = 1 WHERE id = ?", (challenge["id"],))
            return jsonify({"message": "Verification code expired. Request a new one"}), 401

        if not check_password_hash(challenge["otp_hash"], otp):
            connection.execute(
                "UPDATE login_otps SET attempts = attempts + 1 WHERE id = ?",
                (challenge["id"],),
            )
            return jsonify({"message": "Incorrect verification code"}), 401

        connection.execute("UPDATE login_otps SET used = 1 WHERE id = ?", (challenge["id"],))

    session.pop("pending_login_user_id", None)
    session.pop("pending_login_email", None)
    session["user_id"] = pending_user_id
    session["email"] = pending_email
    session["auth_level"] = "otp"
    return jsonify({"email": pending_email})


@app.route("/api/auth/resend-otp", methods=["POST"])
def resend_otp():
    pending_user_id = session.get("pending_login_user_id")
    pending_email = session.get("pending_login_email")
    if not pending_user_id or not pending_email:
        return jsonify({"message": "Start login again to request a verification code"}), 401

    try:
        delivery = create_login_otp(pending_user_id, pending_email)
    except (OSError, smtplib.SMTPException, ValueError) as error:
        print(f"OTP email delivery failed: {type(error).__name__}: {error}")
        return jsonify({"message": "Unable to deliver the verification code"}), 503
    return jsonify({"message": "A new verification code was sent", "delivery": delivery})


@app.route("/api/auth/me")
def current_user():
    if session.get("auth_level") != "otp" or "user_id" not in session:
        return jsonify({"authenticated": False})
    return jsonify({"authenticated": True, "email": session["email"]})


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})


@app.route("/api/analyze-and-schedule", methods=["POST"])
@login_required
def analyze_and_schedule():

    data = request.get_json()

    task = data.get("task")
    optimization_mode = data.get("optimization_mode", "balanced")
    if not task:
        return jsonify({
            "status": "error",
            "message": "Task is required"
        }), 400
    MODES = {
        "balanced": {
            "carbon": 3,
            "cost": 3,
            "energy": 3
        },
        "carbon": {
            "carbon": 8,
            "cost": 2,
            "energy": 5
        },
        "latency": {
            "carbon": 1,
            "cost": 1,
            "energy": 1
        },
        "cost": {
            "carbon": 2,
            "cost": 8,
            "energy": 3
        },
        "energy": {
            "carbon": 5,
            "cost": 2,
            "energy": 8
        }
    }

    weights = MODES.get(
        optimization_mode,
        MODES["balanced"]
    )
    # Step 1: Gemini understands the task
    try:
        requirements = analyze_task(task)
        analysis_source = "Gemini"
        offline = False

    except Exception as e:
        print(f"Gemini unavailable. Using offline fallback: {e}")

        requirements = analyze_task_offline(task)
        analysis_source = "Local Offline Fallback"
        offline = True

    # Step 2: Local scheduler optimizes execution
    required_accuracy = min(requirements.recommended_accuracy, 96)

    result = schedule_task(
        required_accuracy=required_accuracy,
        max_latency=20,
        priority=requirements.urgency,
        carbon_weight=weights["carbon"],
        cost_weight=weights["cost"],
        energy_weight=weights["energy"]
    )
    # Compare selected configuration with the highest-resource
    # feasible configuration.
    impact = None

    if result.get("status") == "success":
        selected = result["selected"]
        alternatives = result["alternatives"]

        baseline = max(
            alternatives,
            key=lambda x: (
                x["carbon"],
                x["energy"],
                x["cost"]
            )
        )

        impact = {
            "baseline": baseline,
            "carbon_reduction": round(
                max(
                    0,
                    (baseline["carbon"] - selected["carbon"])
                    / baseline["carbon"] * 100
                ),
                1
            ),
            "cost_reduction": round(
                max(
                    0,
                    (baseline["cost"] - selected["cost"])
                    / baseline["cost"] * 100
                ),
                1
            ),
            "energy_reduction": round(
                max(
                    0,
                    (baseline["energy"] - selected["energy"])
                    / baseline["energy"] * 100
                ),
                1
            )
        }
    workflow = schedule_workflow(
        urgency=requirements.urgency,
        can_be_delayed=requirements.can_be_delayed
    )
   
    return jsonify({
        "task": task,
        "requirements": requirements.model_dump(),
        "schedule": result,
        "impact": impact,
        "workflow": workflow,
        "analysis_source": analysis_source,
        "offline": offline
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)