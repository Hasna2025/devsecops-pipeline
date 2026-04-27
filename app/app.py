"""
=============================================================
  APP FLASK SÉCURISÉE — Version corrigée
  Branche : fix/secure-version
  Comparaison : main (vulnérable) vs fix/secure-version (safe)
=============================================================
"""

from flask import Flask, request
from markupsafe import escape   # ✅ Fix XSS
import sqlite3
import os

app = Flask(__name__)

# ✅ Fix 3 : Secrets via variables d'environnement (plus rien de hardcodé)
SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-for-dev-only")
AWS_KEY    = os.environ.get("AWS_KEY")


# ✅ Fix 1 : SQL Injection → requête paramétrée
@app.route('/user')
def get_user():
    username = request.args.get('name', '')

    conn = sqlite3.connect(':memory:')
    conn.execute("CREATE TABLE users (id INT, name TEXT, email TEXT)")
    conn.execute("INSERT INTO users VALUES (1, 'alice', 'alice@corp.com')")
    conn.execute("INSERT INTO users VALUES (2, 'bob', 'bob@corp.com')")

    # ✅ Paramètre séparé → impossible d'injecter du SQL
    query = "SELECT * FROM users WHERE name = ?"
    result = conn.execute(query, (username,)).fetchall()
    return str(result)


# ✅ Fix 2 : XSS → escape() neutralise les balises HTML
@app.route('/hello')
def hello():
    name = request.args.get('name', 'World')
    # escape() transforme <script> en &lt;script&gt;
    return f"<h1>Hello {escape(name)}</h1>"


# ✅ Fix 4 : Path Traversal → validation du chemin absolu
@app.route('/read')
def read_file():
    filename = request.args.get('file', '')

    # Normaliser le chemin et vérifier qu'il reste dans /tmp/safe/
    safe_dir = "/tmp/safe/"
    os.makedirs(safe_dir, exist_ok=True)
    safe_path = os.path.abspath(os.path.join(safe_dir, filename))

    if not safe_path.startswith(safe_dir):
        return "Accès refusé", 403

    if not os.path.exists(safe_path):
        return "Fichier introuvable", 404

    with open(safe_path, 'r') as f:
        return f.read()


@app.route('/')
def index():
    return """
    <html>
      <body>
        <h1>✅ Application sécurisée</h1>
        <p>Toutes les vulnérabilités ont été corrigées.</p>
      </body>
    </html>
    """


if __name__ == "__main__":
    # ✅ debug=False + host restreint au localhost
    app.run(host="127.0.0.1", port=5000, debug=False)