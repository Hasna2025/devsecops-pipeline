# ✅ Fix SQL Injection → requête paramétrée
query = "SELECT * FROM users WHERE name = ?"
conn.execute(query, (username,))
# ✅ Fix XSS → render_template ou escape
from markupsafe import escape
return f"<h1>Hello {escape(name)}</h1>"
# ✅ Fix Secrets → variables d'environnement
import os
AWS_KEY = os.environ.get("AWS_KEY")
# ✅ Fix Path Traversal → validation du chemin
import os
safe_path = os.path.abspath(f"/tmp/{filename}")
if not safe_path.startswith("/tmp/"):
return "Accès refusé", 403
