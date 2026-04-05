from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3
import jwt
from datetime import datetime, timedelta
from functools import wraps
import dotenv

dotenv.load_dotenv()

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this')

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'zip'}

# =============== DATABASE INIT ===============
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT,
            created_at TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            filename TEXT,
            original_filename TEXT,
            uploaded_at TIMESTAMP,
            FOREIGN KEY (email) REFERENCES users(email)
        )
    """)
    conn.commit()
    conn.close()

# =============== JWT TOKEN VERIFICATION ===============
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return {"error": "Token missing"}, 401
        
        try:
            token = token.split(" ")[1]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            email = data['email']
        except:
            return {"error": "Invalid token"}, 401
        
        return f(email, *args, **kwargs)
    return decorated

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# =============== ROUTES ===============
@app.route("/", methods=["GET"])
def home():
    return {"message": "Backend is running successfully 🚀"}, 200

@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return {"error": "Email and password required"}, 400
    
    if len(password) < 6:
        return {"error": "Password must be at least 6 characters"}, 400
    
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        hashed_password = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (email, password, created_at) VALUES (?, ?, ?)",
            (email, hashed_password, datetime.now())
        )
        conn.commit()
        conn.close()
        return {"message": "User created successfully"}, 201
    except sqlite3.IntegrityError:
        return {"error": "User already exists"}, 409

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return {"error": "Email and password required"}, 400
    
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE email=?", (email,))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password_hash(user[0], password):
        token = jwt.encode(
            {'email': email, 'exp': datetime.utcnow() + timedelta(hours=24)},
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        return {"message": "Login successful", "token": token, "email": email}, 200
    else:
        return {"error": "Invalid credentials"}, 401

@app.route("/upload", methods=["POST"])
@token_required
def upload_file(email):
    if "file" not in request.files:
        return {"error": "No file found"}, 400
    
    file = request.files["file"]
    
    if file.filename == "":
        return {"error": "No selected file"}, 400
    
    if not allowed_file(file.filename):
        return {"error": "File type not allowed"}, 400
    
    filename = f"{email}_{datetime.now().timestamp()}_{file.filename}"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)
    
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO files (email, filename, original_filename, uploaded_at) VALUES (?, ?, ?, ?)",
        (email, filename, file.filename, datetime.now())
    )
    conn.commit()
    conn.close()
    
    return {"message": "File uploaded successfully", "filename": filename}, 200

@app.route("/files", methods=["GET"])
@token_required
def list_files(email):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT original_filename, filename, uploaded_at FROM files WHERE email=? ORDER BY uploaded_at DESC",
        (email,)
    )
    files = cursor.fetchall()
    conn.close()
    
    return {"files": [{"name": f[0], "id": f[1], "date": f[2]} for f in files]}, 200

@app.route("/download/<filename>", methods=["GET"])
@token_required
def download_file(email, filename):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT original_filename FROM files WHERE email=? AND filename=?",
        (email, filename)
    )
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return {"error": "File not found or unauthorized"}, 404
    
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(filepath):
        return {"error": "File not found on server"}, 404
    
    from flask import send_file
    return send_file(filepath, as_attachment=True, download_name=result[0])

@app.route("/delete/<filename>", methods=["DELETE"])
@token_required
def delete_file(email, filename):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT filename FROM files WHERE email=? AND filename=?",
        (email, filename)
    )
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return {"error": "File not found or unauthorized"}, 404
    
    cursor.execute("DELETE FROM files WHERE email=? AND filename=?", (email, filename))
    conn.commit()
    conn.close()
    
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    
    return {"message": "File deleted successfully"}, 200

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
