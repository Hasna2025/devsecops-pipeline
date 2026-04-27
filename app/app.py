"""
=============================================================
  APP FLASK VOLONTAIREMENT VULNÉRABLE — À NE PAS DÉPLOYER
  Objectif : servir de cible pour Semgrep (SAST), Trivy et ZAP (DAST)
=============================================================
"""

from flask import Flask, request, render_template_string
import sqlite3
import os

app = Flask(__name__)

# ─────────────────────────────────────────────────────────────
# ❌ VULNÉRABILITÉ 3 : Secrets hardcodés (détectés par Semgrep)
#    Règles déclenchées : generic.secrets.security.detected-generic-secret
#                        python.lang.security.audit.hardcoded-password
#
#    Impact réel : un attaquant qui accède au code source (GitHub leak,
#    dépôt public accidentel) obtient directement les clés AWS et le
#    secret Flask → compromission totale du compte cloud.
#
#    ✅ FIX : utiliser os.environ.get("SECRET_KEY") et stocker les
#    secrets dans GitHub Secrets / AWS Secrets Manager / Vault.
# ─────────────────────────────────────────────────────────────
SECRET_KEY = "my-super-secret-password-123"        # ← Semgrep ALERT
AWS_KEY    = "AKIAIOSFODNN7EXAMPLE"                # ← Semgrep ALERT
DB_PASS    = "admin:password@localhost:5432/prod"  # ← Semgrep ALERT


# ─────────────────────────────────────────────────────────────
# ❌ VULNÉRABILITÉ 1 : SQL Injection (détectée par Semgrep + ZAP)
#    Règles déclenchées : python.flask.security.injection.tainted-sql-from-http-params
#
#    Scénario d'attaque :
#      GET /user?name=' OR '1'='1   → retourne TOUTE la table users
#      GET /user?name='; DROP TABLE users; --  → supprime la base
#
#    Impact réel : exfiltration de données, contournement d'auth,
#    destruction de données — OWASP A03:2021.
#
#    ✅ FIX : utiliser des requêtes paramétrées :
#      query = "SELECT * FROM users WHERE name = ?"
#      conn.execute(query, (username,))
# ─────────────────────────────────────────────────────────────
@app.route('/user')
def get_user():
    username = request.args.get('name', '')

    # Initialisation de la base de test (en mémoire)
    conn = sqlite3.connect(':memory:')
    conn.execute("CREATE TABLE users (id INT, name TEXT, email TEXT, password TEXT)")
    conn.execute("INSERT INTO users VALUES (1, 'alice', 'alice@corp.com', 'hash1')")
    conn.execute("INSERT INTO users VALUES (2, 'bob', 'bob@corp.com', 'hash2')")

    # ❌ Concaténation directe de l'input utilisateur dans la requête SQL
    query = f"SELECT * FROM users WHERE name = '{username}'"
    print(f"[DEBUG] Requête exécutée : {query}")  # Ne jamais logguer les requêtes en prod !

    result = conn.execute(query).fetchall()
    return str(result)


# ─────────────────────────────────────────────────────────────
# ❌ VULNÉRABILITÉ 2 : Cross-Site Scripting (XSS) réfléchi
#    Règles déclenchées : python.flask.security.xss.reflective-xss-all-tags
#
#    Scénario d'attaque :
#      GET /hello?name=<script>document.cookie</script>
#      → Le script s'exécute dans le navigateur de la victime
#      → Vol de session, redirection malveillante, défacement
#
#    Impact réel : détournement de compte, phishing ciblé — OWASP A03:2021.
#
#    ✅ FIX : utiliser render_template() avec Jinja2 (auto-escaping)
#      ou markupsafe.escape(name) avant injection dans le HTML.
# ─────────────────────────────────────────────────────────────
@app.route('/hello')
def hello():
    name = request.args.get('name', 'World')

    # ❌ Injection directe dans le HTML sans échappement
    html = "<h1>Hello " + name + "</h1>"
    return html


# ─────────────────────────────────────────────────────────────
# ❌ VULNÉRABILITÉ 4 : Path Traversal (détectée par Semgrep + ZAP)
#    Règles déclenchées : python.lang.security.audit.path-traversal
#
#    Scénario d'attaque :
#      GET /read?file=../../../../etc/passwd
#      → Lecture de fichiers système sensibles
#
#    ✅ FIX : valider et normaliser le chemin avec os.path.abspath()
#    et vérifier qu'il est dans le répertoire autorisé.
# ─────────────────────────────────────────────────────────────
@app.route('/read')
def read_file():
    filename = request.args.get('file', '')
    # ❌ Lecture directe sans validation du chemin
    with open(f"/tmp/{filename}", 'r') as f:
        return f.read()


# ─────────────────────────────────────────────────────────────
# ✅ Page d'accueil saine (pour que ZAP ait un point d'entrée)
# ─────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return """
    <html>
      <body>
        <h1>🎯 Application cible DevSecOps</h1>
        <p>Routes vulnérables (à des fins éducatives) :</p>
        <ul>
          <li><a href="/user?name=alice">/user?name=alice</a> — SQLi</li>
          <li><a href="/hello?name=World">/hello?name=World</a> — XSS</li>
          <li><a href="/read?file=test.txt">/read?file=test.txt</a> — Path Traversal</li>
        </ul>
      </body>
    </html>
    """


if __name__ == "__main__":
    # ❌ debug=True expose le Werkzeug debugger en production → RCE possible
    app.run(host="0.0.0.0", port=5000, debug=True)