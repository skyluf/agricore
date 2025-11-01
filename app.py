# app.py
from flask import Flask, request, make_response
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'change-me'

users = {}

# Load raw HTML files
INDEX_HTML = open("template/index.html").read()
LOGIN_HTML = open("template/login.html").read()
REGISTER_HTML = open("template/register.html").read()
STYLE_CSS = open("static/style.css").read()
DASHBOARD_HTML=open("template/dashboard.html")
DASHBOARDSTYLE_CSS=open("static/dashboardStyle.css")

# Helper: Inject message into HTML
def render_page(base_html, message="", msg_type=""):
    if message:
        msg_html = f'<p class="message {msg_type}">{message}</p>'
        return base_html.replace("<!-- MESSAGE -->", msg_html)
    return base_html.replace("<!-- MESSAGE -->", "")

@app.route('/')
def index():
    return render_page(INDEX_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.get(username)

        if user and check_password_hash(user['password'], password):
            return render_page(DASHBOARD_HTML, f"Welcome back, {username}!", "success")
        else:
            return render_page(LOGIN_HTML, "Invalid username or password.", "error")
    return render_page(LOGIN_HTML)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if username in users:
            return render_page(REGISTER_HTML, "Username already exists.", "error")
        elif len(password) < 4:
            return render_page(REGISTER_HTML, "Password too short (min 4 chars).", "error")
        else:
            users[username] = {
                'email': email,
                'password': generate_password_hash(password)
            }
            return render_page(LOGIN_HTML, "Registered! Please log in.", "success")
    return render_page(REGISTER_HTML)

@app.route('/static/style.css')
def serve_css():
    response = make_response(STYLE_CSS)
    response.headers['Content-Type'] = 'text/css'
    return response

if __name__ == '__main__':
    app.run(debug=True)
