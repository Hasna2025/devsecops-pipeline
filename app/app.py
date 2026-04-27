from flask import Flask, request, render_template_string
from markupsafe import escape
import sqlite3
import os

app = Flask(__name__)

# ─────────────────────────────
# ✅ Secrets externalisés
# ─────────────────────────────
SECRET_KEY = os.environ.get("SECRET_KEY", "dev")
AWS_KEY = os.environ.get("AWS_KEY", "dev")


# ─────────────────────────────
# ✅ SQL Injection FIX
# ─────────────────────────────
@app.route('/user')
def get_user():
    username = request.args.get('name', '')

    conn = sqlite3.connect(':memory:')
    conn.execute("CREATE TABLE users (id INT, name TEXT, email TEXT)")
    conn.execute("INSERT INTO users VALUES (1, 'alice', 'alice@corp.com')")
    conn.execute("INSERT INTO users VALUES (2, 'bob', 'bob@corp.com')")

    # SAFE QUERY
    query = "SELECT * FROM users WHERE name = ?"
    result = conn.execute(query, (username,)).fetchall()

    return str(result)


# ─────────────────────────────
# ✅ XSS FIX (IMPORTANT pour Semgrep)
# ─────────────────────────────
@app.route('/hello')
def hello():
    name = request.args.get('name', 'World')

    safe_name = escape(name)

    # PAS de HTML brut → OK Semgrep
    return render_template_string(
        "<h1>Hello {{ name }}</h1>",
        name=safe_name
    )


# ─────────────────────────────
# ✅ PATH TRAVERSAL FIX
# ─────────────────────────────
@app.route('/read')
def read_file():
    filename = request.args.get('file', '')

    safe_dir = "/tmp/safe/"
    os.makedirs(safe_dir, exist_ok=True)

    full_path = os.path.abspath(os.path.join(safe_dir, filename))

    if not full_path.startswith(safe_dir):
        return "Forbidden", 403

    if not os.path.exists(full_path):
        return "Not found", 404

    with open(full_path, 'r') as f:
        return f.read()


# ─────────────────────────────
# HOME
# ─────────────────────────────
@app.route('/')
def index():
    return """
    <h1>SAFE DevSecOps App</h1>
    <ul>
      <li>/user?name=alice</li>
      <li>/hello?name=test</li>
      <li>/read?file=test.txt</li>
    </ul>
    """


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)