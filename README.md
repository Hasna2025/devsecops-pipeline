Phase 1 — Static Application Security Testing (SAST)
 Analyse statique du code avec Semgrep

Cette première phase du pipeline DevSecOps consiste à réaliser une analyse statique du code source (SAST) à l’aide de l’outil Semgrep.

Semgrep analyse le code sans l’exécuter, en inspectant l’AST (Abstract Syntax Tree) afin de détecter automatiquement des vulnérabilités de sécurité.

 Objectif de cette étape
Détecter les vulnérabilités dès l’écriture du code (shift-left security)
Identifier les mauvaises pratiques de développement
Bloquer l’intégration de code dangereux avant le build ou le déploiement
 Types de vulnérabilités détectées

Dans ce projet, Semgrep permet de détecter notamment :

🔴 SQL Injection (requêtes SQL non sécurisées)
🔴 Cross-Site Scripting (XSS)
🔴 Secrets hardcodés (API keys, passwords)
🔴 Path Traversal
🔴 Mauvaises configurations Flask (debug activé, host exposé)
 Exemple de vulnérabilités détectées
❌ SQL Injection
query = f"SELECT * FROM users WHERE name = '{username}'"
❌ XSS
html = "<h1>Hello " + name + "</h1>"
❌ Debug mode activé
app.run(host="0.0.0.0", debug=True)
⚙️ Règles utilisées dans Semgrep

Le scan utilise les règles suivantes :

p/security-audit
p/owasp-top-ten
p/python
p/flask
p/secrets

Ces règles couvrent les principales vulnérabilités du OWASP Top 10.

 Résultat du scan
✔ Analyse automatique du code source
✔ Détection de plusieurs vulnérabilités critiques
❌ Le pipeline est bloqué si des vulnérabilités de type CRITICAL sont détectées
 Importance dans le pipeline DevSecOps

Cette étape est la première barrière de sécurité du pipeline :

Code → SAST (Semgrep) → Validation → Build → Deployment

Elle permet de corriger les vulnérabilités dès le développement, réduisant ainsi les risques en production.

 Conclusion

La phase SAST permet d’intégrer la sécurité dès le début du cycle de développement, conformément à l’approche Shift Left Security, essentielle dans les environnements DevSecOps modernes.
