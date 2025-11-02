from flask import Flask, request, make_response, redirect, jsonify  # Added jsonify
import sqlite3
import os
import hashlib
from flask_cors import CORS
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # ← ADD THIS LINE

# Load environment variables
load_dotenv()  # ← ADD THIS LINE

# --- GEMINI API CONFIGURATION ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    print("Warning: GEMINI_API_KEY not found in environment variables")
    client = None


# --- PATH CONFIG ---
TEMPLATE_DIR = os.path.join(os.getcwd(), "template")
STATIC_DIR = os.path.join(os.getcwd(), "static")
DB_NAME = "users.db"

# --- LOAD HTML FILES ---
def load_html(filename):
    path = os.path.join(TEMPLATE_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:  # ✅ UTF-8 decoding
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
        with open(path, 'r', encoding='utf-8') as f:  # ✅ UTF-8 decoding
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
    
# --- AI CHATBOT ENDPOINT ---
@app.route('/api/chat', methods=['POST'])
def chat():
    """
    AI-powered farming chatbot endpoint using Gemini 2.5 Flash
    Accepts user messages and returns AI-generated farming advice
    """
    try:
        # Check if Gemini client is initialized
        if not client:
            return jsonify({
                'error': 'Gemini API not configured',
                'response': 'Sorry, the AI service is not available. Please configure GEMINI_API_KEY.',
                'status': 'error'
            }), 500

        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # System prompt for farming expertise
        system_instruction = """You are AgriBot, an expert agricultural assistant with deep knowledge of farming practices, crop management, soil health, pest control, irrigation, and sustainable agriculture. 

Your role is to provide:
- Practical farming tips and advice
- Crop-specific guidance (planting, harvesting, care)
- Soil management and fertilization recommendations
- Pest and disease identification and control methods
- Weather-based farming decisions
- Organic and sustainable farming practices
- Market trends and crop selection advice
- Water management and irrigation techniques
- Season-specific farming recommendations for India

Always provide clear, actionable advice tailored for farmers. Keep responses concise (2-4 sentences) but informative. Use simple language that farmers can easily understand. Focus on practical, implementable solutions."""

        # Generate response using Gemini 2.5 Flash
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
                max_output_tokens=300,
                top_p=0.95,
                top_k=40
            )
        )
        
        # Extract the response text
        bot_response = response.text.strip()

        return jsonify({
            'response': bot_response,
            'status': 'success'
        })
    
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'error': str(e),
            'response': 'Sorry, I encountered an error. Please try again.',
            'status': 'error'
        }), 500


# --- RUN APP ---
if __name__ == '__main__':
    app.run(debug=True)

