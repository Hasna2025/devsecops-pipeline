"""
=============================================================
  APP FLASK SÉCURISÉE — VERSION CORRIGÉE DEVSECOPS
=============================================================
"""

from flask import Flask, request
from markupsafe import escape
import sqlite3
import os

app = Flask(__name__)

# ─────────────────────────────────────────────
# ✅ Secrets externalisés (bonne pratique DevSecOps)
# ─────────────────────────────────────────────
SECRET_KEY = os.environ.get("SECRET_KEY")
AWS_KEY = os.environ.get("AWS_KEY")


# ─────────────────────────────────────────────
# ✅ SQL Injection FIX (requêtes paramétrées)
# ─────────────────────────────────────────────
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


# ─────────────────────────────────────────────
# ✅ XSS FIX (escape output)
# ─────────────────────────────────────────────
@app.route('/hello')
def hello():
    name = request.args.get('name', 'World')

    safe_name = escape(name)
    return f"<h1>Hello {safe_name}</h1>"


# ─────────────────────────────────────────────
# ✅ PATH TRAVERSAL FIX
# ─────────────────────────────────────────────
@app.route('/read')
def read_file():
    filename = request.args.get('file', '')

    safe_dir = "/tmp/safe/"
    os.makedirs(safe_dir, exist_ok=True)

    safe_path = os.path.abspath(os.path.join(safe_dir, filename))

    # Vérification sécurité
    if not safe_path.startswith(safe_dir):
        return "Accès refusé", 403

    if not os.path.exists(safe_path):
        return "Fichier introuvable", 404

    with open(safe_path, 'r') as f:
        return f.read()


# ─────────────────────────────────────────────
# ✅ HOME PAGE SAFE
# ─────────────────────────────────────────────
@app.route('/')
def index():
    return """
    <html>
      <body>
        <h1>🟢 Application sécurisée DevSecOps</h1>
        <ul>
          <li>/user?name=alice</li>
          <li>/hello?name=test</li>
          <li>/read?file=test.txt</li>
        </ul>
      </body>
    </html>
    """


# ─────────────────────────────────────────────
# ✅ PRODUCTION SAFE CONFIG
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)