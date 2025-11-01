from flask import Flask, request, make_response, redirect
import sqlite3
import os
import hashlib

# Initialize Flask app
app = Flask(__name__)

# --- PATH CONFIG ---
TEMPLATE_DIR = os.path.join(os.getcwd(), "template")
STATIC_DIR = os.path.join(os.getcwd(), "static")
DB_NAME = "users.db"

# --- LOAD HTML FILES ---
def load_html(filename):
    path = os.path.join(TEMPLATE_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r') as f:
            return f.read()
    return f"<h1>File {filename} not found</h1>"

INDEX_HTML = load_html("index.html")
LOGIN_HTML = load_html("login.html")
REGISTER_HTML = load_html("register.html")
DASHBOARD_HTML = load_html("dashboard.html")
MARKETPLACE_HTML = load_html("marketplace.html")
DRONESCAN_HTML = load_html("droneScan.html")
AICHATBOT_HTML = load_html("aiChatbot.html")

# --- LOAD CSS FILES ---
def load_css(filename):
    path = os.path.join(STATIC_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r') as f:
            return f.read()
    return ""

STYLE_CSS = load_css("style.css")
DASHBOARD_CSS = load_css("dashboard.css")
MARKETPLACE_CSS = load_css("marketplace.css")
DRONESCAN_CSS = load_css("dronescan.css")
AICHATBOT_CSS = load_css("aichatbot.css")
LOGIN_CSS = load_css("login.css")

# --- DATABASE SETUP ---
def init_db():
    if not os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE users (
                username TEXT PRIMARY KEY,
                email TEXT,
                password TEXT
            )
        ''')
        conn.commit()
        conn.close()

init_db()

# --- HELPER FUNCTIONS ---
def render(html, message="", msg_type=""):
    msg = f'<p class="message {msg_type}">{message}</p>' if message else ""
    return html.replace("<!-- MESSAGE -->", msg)

def generate_password_hash(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def check_password(stored, provided):
    return hashlib.sha256(provided.encode()).hexdigest() == stored

# --- ROUTES ---
@app.route('/')
def index():
    return render(INDEX_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username = ?", (username,))
        row = c.fetchone()
        conn.close()

        if row and check_password(row[0], password):
            return redirect('/dashboard')
        else:
            return render(LOGIN_HTML, "Invalid username or password.", "error")
    return render(LOGIN_HTML)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if len(password) < 4:
            return render(REGISTER_HTML, "Password too short (min 4 chars).", "error")

        hashed = generate_password_hash(password)

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                      (username, email, hashed))
            conn.commit()
            conn.close()
            return render(LOGIN_HTML, "Registered! Please log in.", "success")
        except sqlite3.IntegrityError:
            conn.close()
            return render(REGISTER_HTML, "Username already exists.", "error")
    return render(REGISTER_HTML)

@app.route('/dashboard')
def dashboard():
    return render(DASHBOARD_HTML)

@app.route('/marketplace')
def marketplace():
    return render(MARKETPLACE_HTML)

@app.route('/droneScan')
def droneScan():
    return render(DRONESCAN_HTML)

@app.route('/aiChatbot')
def aiChatbot():
    return render(AICHATBOT_HTML)

# --- STATIC FILE SERVING ---
@app.route('/static/<path:filename>')
def static_files(filename):
    path = os.path.join(STATIC_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r') as f:
            content = f.read()
        response = make_response(content)
        if filename.endswith('.css'):
            response.headers['Content-Type'] = 'text/css'
        return response
    return "File not found", 404

# --- RUN APP ---
if __name__ == '__main__':
    app.run(debug=True)

