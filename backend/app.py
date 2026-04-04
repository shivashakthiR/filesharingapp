from flask import Flask, request
from flask_cors import CORS
import os
import sqlite3
sessions={}

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ---------------- DATABASE INIT ----------------
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)

    conn.commit()
    conn.close()


# ---------------- HOME ----------------
@app.route("/")
def home():
    return "Backend is running successfully 🚀"


# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return {"error": "Email and password required"}

    try:
        conn = sqlite3.connect("users.db", timeout=5)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (email, password) VALUES (?, ?)",
            (email, password)
        )

        conn.commit()
        return {"message": "User created successfully"}

    except sqlite3.IntegrityError:
        return {"error": "User already exists"}

    finally:
        conn.close()


# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return {"error": "Email and password required"}

    conn = sqlite3.connect("users.db", timeout=5)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email, password)
    )

    user = cursor.fetchone()
    conn.close()

    if user:
        sessions[email] = True
        return {"message": "Login successful", "email": email}
    else:
        return {"error": "Invalid credentials"}


# ---------------- FILE UPLOAD ----------------
@app.route("/upload", methods=["POST"])
def upload_file():
    email = request.form.get("email")

    if email not in sessions:
        return {"error": "Unauthorized. Please login first"}
    if "file" not in request.files:
        return {"error": "No file found"}

    file = request.files["file"]

    if file.filename == "":
        return {"error": "No selected file"}

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    return {"message": "File uploaded successfully"}


# ---------------- LIST FILES ----------------
@app.route("/files", methods=["GET"])
def list_files():
    email = request.args.get("email")

    if email not in sessions:
        return {"error": "Unauthorized"}

    files = os.listdir(app.config["UPLOAD_FOLDER"])
    return {"files": files}


# ---------------- RUN ----------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)