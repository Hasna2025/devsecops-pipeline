from flask import Flask, request
from markupsafe import escape
import sqlite3
import os

app = Flask(__name__)

# ============================================================
# ✅ FIX SQL Injection
# ============================================================

@app.route('/user')
def get_user():
    username = request.args.get('name', '')

    conn = sqlite3.connect('users.db')

    # ✅ Requête paramétrée
    query = "SELECT * FROM users WHERE name = ?"

    result = conn.execute(query, (username,)).fetchall()

    conn.close()

    return str(result)

# ============================================================
# ✅ FIX XSS
# ============================================================

@app.route('/hello')
def hello():
    name = request.args.get('name', 'World')

    # ✅ escape protège contre <script>
    safe_name = escape(name)

    return f"<h1>Hello {safe_name}</h1>"

# ============================================================
# ✅ FIX Secrets Hardcodés
# ============================================================

AWS_KEY = os.environ.get("AWS_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY")

# ============================================================
# ✅ FIX Path Traversal
# ============================================================

@app.route('/read')
def read_file():

    filename = request.args.get("file", "")

    # Répertoire autorisé
    BASE_DIR = "/tmp"

    # Construction sécurisée du chemin
    safe_path = os.path.abspath(os.path.join(BASE_DIR, filename))

    # Vérification anti path traversal
    if not safe_path.startswith(os.path.abspath(BASE_DIR)):
        return "Accès refusé", 403

    # Vérification existence fichier
    if not os.path.exists(safe_path):
        return "Fichier introuvable", 404

    with open(safe_path, "r") as f:
        content = f.read()

    return content

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)