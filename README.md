# 🛡️ DevSecOps CI/CD Security Pipeline

**Auteure :** Hasna AHSSAR
**Technologies :** GitHub Actions · Semgrep · Trivy · Snyk · OWASP ZAP
**Coût :** 100% gratuit · GitHub Free Tier (2 000 min/mois)

---

## 💡 Idée centrale du projet

Dans la majorité des équipes de développement traditionnelles, la sécurité est traitée **en dernier** — juste avant ou après le déploiement en production. Un testeur de sécurité (pentester) intervient, trouve des failles, et les développeurs doivent tout reprendre depuis le début. C'est lent, coûteux, et risqué.

Ce projet applique le principe du **"Shift-Left Security"** : déplacer les contrôles de sécurité **le plus tôt possible** dans le cycle de développement, directement dans le pipeline CI/CD. Concrètement, à chaque fois qu'un développeur pousse du code sur GitHub, une série d'outils de sécurité s'exécute automatiquement et **bloque le déploiement** si une vulnérabilité critique est détectée.

```
AVANT (Security à droite)           APRÈS (Shift-Left Security)
─────────────────────────           ───────────────────────────
Code → Build → Test → Deploy        Code → [SAST] → [SCA] → [Scan]
                          ↓                   ↓          ↓       ↓
                    Pentest (tard)       Bloqué ici si vulnérable
                          ↓
                   Correction (cher)
```

---

## 🎯 Objectif du projet

Construire un **pipeline de sécurité automatisé de bout en bout** qui :

1. S'intègre à GitHub Actions sans aucun coût
2. Analyse le code source, les dépendances et l'image Docker
3. Lance une application réelle pour la tester dynamiquement
4. Prend une décision finale : autoriser ou bloquer le déploiement
5. Génère des rapports consultables directement dans GitHub

---

## 🏗️ Architecture : les 5 stages

```
Git Push / Pull Request
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                   GitHub Actions Workflow                    │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  STAGE 1    │  │  STAGE 2    │  │  STAGE 3    │         │
│  │    SAST     │  │  CONTAINER  │  │    SCA      │         │
│  │  Semgrep    │  │   Trivy     │  │   Snyk      │         │
│  │             │  │             │  │             │         │
│  │ Code source │  │ Image Docker│  │requirements │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┴────────────────┘                 │
│                          │ needs: [1, 2]                    │
│                          ▼                                  │
│                  ┌─────────────┐                            │
│                  │  STAGE 4    │                            │
│                  │    DAST     │                            │
│                  │ OWASP ZAP   │                            │
│                  │ App en live │                            │
│                  └──────┬──────┘                            │
│                         │ needs: [1, 2, 3, 4]              │
│                         ▼                                   │
│                  ┌─────────────┐                            │
│                  │  STAGE 5    │                            │
│                  │  SECURITY   │                            │
│                  │    GATE     │                            │
│                  └──────┬──────┘                            │
│                         │                                   │
│              ┌──────────┴──────────┐                        │
│              ▼                     ▼                        │
│       ❌ BLOQUÉ              ✅ AUTORISÉ                    │
│    (CRITICAL trouvée)      (Aucune CRITICAL)                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 Détail de chaque stage

### Stage 1 — SAST avec Semgrep

**SAST = Static Application Security Testing**
Analyse le code source **sans l'exécuter**. Semgrep parcourt l'arbre syntaxique du code Python à la recherche de patterns dangereux connus.

| Ce qu'il détecte | Exemple dans ce projet |
|------------------|----------------------|
| Injection SQL | `f"SELECT * FROM users WHERE name = '{username}'"` |
| XSS réfléchi | `"<h1>Hello " + name + "</h1>"` |
| Secrets hardcodés | `AWS_KEY = "AKIAIOSFODNN7EXAMPLE"` |
| Path Traversal | `open(f"/tmp/{filename}")` |
| Debug mode activé | `app.run(debug=True)` |

Avantage clé : très rapide (< 30 secondes), aucun déploiement nécessaire, détecte les failles dès l'écriture du code.

---

### Stage 2 — Container Scan avec Trivy

**Trivy** décompose l'image Docker layer par layer et cherche des **CVE (Common Vulnerabilities and Exposures)** dans :
- Les packages système de l'image de base (`python:3.10-slim`)
- Les packages Python installés via `pip`
- Les secrets éventuellement copiés dans l'image

| Dépendance vulnérable | CVE | Sévérité |
|-----------------------|-----|----------|
| Flask 2.1.0 | CVE-2023-30861 | HIGH |
| Werkzeug 2.1.0 | CVE-2023-46136 | CRITICAL |
| cryptography 3.4.8 | Multiples | HIGH/CRITICAL |

---

### Stage 3 — SCA avec Snyk

**SCA = Software Composition Analysis**
Analyse le fichier `requirements.txt` **avant même le build Docker** et vérifie chaque dépendance contre la base de données CVE de Snyk.

Différence avec Trivy :
- Trivy scanne ce qui est **dans l'image** (après build)
- Snyk scanne ce qui est **déclaré dans le code** (avant build)
→ Complémentaires, ils offrent une couverture maximale.

---

### Stage 4 — DAST avec OWASP ZAP

**DAST = Dynamic Application Security Testing**
L'application est **réellement lancée** dans un container, puis OWASP ZAP lui envoie des milliers de requêtes HTTP malveillantes pour trouver des vulnérabilités en conditions réelles.

Ce que le SAST ne peut pas voir, mais le DAST oui :
- Comportements dynamiques de l'application
- Configuration des headers HTTP de sécurité
- Vulnérabilités qui n'apparaissent qu'au runtime

Ce stage se lance uniquement si les Stages 1 et 2 réussissent (`needs: [sast, container-scan]`). Logique : inutile de tester dynamiquement une application dont le code est déjà connu vulnérable.

---

### Stage 5 — Security Gate

Le stage final agrège les résultats de tous les stages et prend la **décision finale** :

```bash
si SAST = failure OU Container = failure OU SCA = failure OU DAST = failure
  → ❌ DÉPLOIEMENT BLOQUÉ
sinon
  → ✅ DÉPLOIEMENT AUTORISÉ
```

---

## 🎓 Application cible : volontairement vulnérable

Le projet inclut une application Flask qui contient **intentionnellement** 4 vulnérabilités, pour que les outils aient quelque chose à détecter :

```python
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
```

> ⚠️ Cette application ne doit jamais être déployée en production. Elle est uniquement destinée à servir de cible pour les outils de sécurité dans un contexte éducatif.

---

requiments.txt
```
# ─────────────────────────────────────────────────────────────
# DÉPENDANCES VOLONTAIREMENT OBSOLÈTES — pour démontrer Trivy/Snyk
# ─────────────────────────────────────────────────────────────

# ❌ Flask 2.1.0 (publiée en 2022)
#    CVE connues : CVE-2023-30861 (cookie sécurisé bypassable)
#    Version sûre actuelle : Flask >= 3.0.3
flask==2.1.0

# ❌ Werkzeug 2.1.0 (dépendance de Flask)
#    CVE-2023-25577 : DoS via multipart form data malformé
#    CVE-2023-46136 : RCE via le debugger Werkzeug
werkzeug==2.1.0

# ❌ Jinja2 3.0.0
#    CVE-2024-34064 : XSS via les filtres xmlattr non-échappés
jinja2==3.0.0

# ❌ requests 2.20.0
#    CVE-2023-32681 : fuite de credentials via redirect cross-origin
requests==2.20.0

# ❌ cryptography 3.4.8
#    Nombreuses CVEs dans les versions < 41.0.0
cryptography==3.4.8

# Pour la gestion des requêtes (version récente, pour ne pas tout casser)
markupsafe>=2.0.0
```

security-pipeline.yml

```
# =============================================================
#  PIPELINE DE SÉCURITÉ DEVSECOPS — Hasna AHSSAR
#  GitHub Actions Workflow
#
#  Stages :
#    1. SAST    → Semgrep  (analyse statique du code source)
#    2. Trivy   → Scan CVE de l'image Docker
#    3. SCA     → Snyk     (vulnérabilités des dépendances)
#    4. DAST    → OWASP ZAP (scan dynamique de l'app en live)
#    5. Gate    → Bloquer si CRITICAL détecté, autoriser sinon
#
#  Prérequis GitHub Secrets à configurer :
#    - SEMGREP_TOKEN  : compte gratuit sur semgrep.dev
#    - SNYK_TOKEN     : compte gratuit sur snyk.io
#    (Trivy et ZAP sont open-source, aucun token requis)
# =============================================================

name: "🛡️ DevSecOps Security Pipeline"

# ─────────────────────────────────────────────────────────────
# DÉCLENCHEURS
# Le pipeline se lance automatiquement sur :
#   - push sur main ou develop (intégration continue)
#   - pull_request vers main (review sécurité avant merge)
#   - workflow_dispatch : lancement manuel depuis l'UI GitHub
# ─────────────────────────────────────────────────────────────
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  workflow_dispatch:  # Permet de lancer le pipeline manuellement

# ─────────────────────────────────────────────────────────────
# PERMISSIONS
# Principe de moindre privilège : on accorde seulement ce dont
# chaque étape a besoin. security-events:write est nécessaire
# pour uploader les résultats SARIF vers GitHub Security Tab.
# ─────────────────────────────────────────────────────────────
permissions:
  contents: read          # Lire le code source
  security-events: write  # Uploader les rapports SARIF
  actions: read           # Lire les informations du workflow

jobs:

  # ══════════════════════════════════════════════════════════
  # STAGE 1 — SAST (Static Application Security Testing)
  #
  # Outil : Semgrep (open-source, concurrent de SonarQube)
  # Ce qu'il fait : analyse le CODE SOURCE (AST - Abstract Syntax Tree)
  # sans l'exécuter. Il cherche des patterns de code dangereux.
  #
  # Règles utilisées :
  #   p/security-audit  → audit général de sécurité
  #   p/owasp-top-ten   → les 10 vulnérabilités OWASP les plus critiques
  #   p/python          → règles spécifiques Python
  #   p/flask           → règles spécifiques au framework Flask
  #   p/secrets         → secrets hardcodés (AWS keys, passwords, tokens)
  #
  # Avantages SAST :
  #   ✅ Très rapide (pas besoin de déployer l'app)
  #   ✅ Détecte les vulnérabilités dès l'écriture du code
  #   ✅ Pas de faux positifs liés à la configuration réseau
  # Limites :
  #   ⚠️  Peut générer des faux positifs
  #   ⚠️  Ne voit pas les vulnérabilités de configuration runtime
  # ══════════════════════════════════════════════════════════
  sast:
    
    name: "🔍 Stage 1 — SAST (Semgrep)"
    runs-on: ubuntu-latest
    steps:
      - name: "📥 Checkout du code source"
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Récupérer tout l'historique pour une analyse complète

      - name: "🔍 Analyse Semgrep SAST"
        uses: returntocorp/semgrep-action@v1
        with:
          config: >-
            p/security-audit
            p/owasp-top-ten
            p/python
            p/flask
            p/secrets
        env:
          # Token optionnel : permet de sauvegarder les résultats
          # sur le dashboard Semgrep Cloud (semgrep.dev)
          # Sans token, le scan fonctionne quand même en mode local.
          SEMGREP_APP_TOKEN: ${{ secrets.SEMGREP_TOKEN }}

      # Upload des résultats au format SARIF vers GitHub Security Tab
      # → visible dans Onglet "Security" > "Code scanning alerts"
      - name: "📊 Upload résultats SARIF vers GitHub Security"
        uses: github/codeql-action/upload-sarif@v3
        if: always()  # Même si le scan a trouvé des vulnérabilités
        with:
          sarif_file: semgrep.sarif
          category: "SAST-Semgrep"


  # ══════════════════════════════════════════════════════════
  # STAGE 2 — Container Vulnerability Scan
  #
  # Outil : Trivy (par Aqua Security, leader du marché)
  # Ce qu'il fait : scanne l'image Docker layer par layer et
  # cherche des CVEs dans :
  #   - Les packages OS (Debian, Alpine, etc.)
  #   - Les packages de langages (pip, npm, go modules, etc.)
  #   - Les fichiers de config (mauvaises permissions, etc.)
  #   - Les secrets potentiellement embarqués dans l'image
  #
  # Format de sortie : SARIF (uploadé vers GitHub) + table console
  #
  # exit-code: '1' → le job ÉCHOUE si une CVE CRITICAL est trouvée
  #   C'est le "Security Gate" au niveau container.
  # ══════════════════════════════════════════════════════════
  container-scan:
    name: "🐳 Stage 2 — Container Scan (Trivy)"
    runs-on: ubuntu-latest
    steps:
      - name: "📥 Checkout du code source"
        uses: actions/checkout@v4

      - name: "🏗️ Build de l'image Docker"
        # On tague avec le SHA du commit pour la traçabilité
        run: docker build -t devsecops-app:${{ github.sha }} .

      - name: "🐳 Scan Trivy — Image Docker"
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: "devsecops-app:${{ github.sha }}"
          format: sarif
          output: trivy-results.sarif
          # On se concentre sur CRITICAL et HIGH uniquement
          # (LOW et MEDIUM génèrent trop de bruit)
          severity: CRITICAL,HIGH
          # exit-code 1 = le pipeline BLOQUE si CVE CRITICAL trouvée
          exit-code: '1'
          # Ignorer les CVEs sans fix disponible (reduce noise)
          ignore-unfixed: false
          # Scanner aussi les secrets dans l'image
          scanners: vuln,secret

      - name: "📊 Upload résultats Trivy vers GitHub Security"
        uses: github/codeql-action/upload-sarif@v3
        # if: always() → uploader même si des CVEs ont été trouvées
        if: always()
        with:
          sarif_file: trivy-results.sarif
          category: "Container-Trivy"

      # Sauvegarde du rapport en artefact téléchargeable
      - name: "💾 Sauvegarde du rapport Trivy"
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: trivy-scan-report
          path: trivy-results.sarif
          retention-days: 30  # Garder 30 jours


  # ══════════════════════════════════════════════════════════
  # STAGE 3 — SCA (Software Composition Analysis)
  #
  # Outil : Snyk (alternative : OWASP Dependency-Check)
  # Ce qu'il fait : analyse le fichier requirements.txt (ou
  # package.json, pom.xml, go.sum, etc.) et vérifie chaque
  # dépendance contre la base de données CVE de Snyk.
  #
  # Différence avec Trivy :
  #   - Trivy scanne l'IMAGE Docker (packages OS + pip installés)
  #   - Snyk scanne le FICHIER de dépendances (avant même le build)
  #   → Complémentaires ! Les deux ensemble = couverture maximale
  #
  # --severity-threshold=high → bloque sur HIGH et CRITICAL
  #   (peut être ajusté à "critical" pour moins de bruit)
  # ══════════════════════════════════════════════════════════
  sca:
    name: "📦 Stage 3 — SCA (Snyk Dependencies)"
    runs-on: ubuntu-latest
    steps:
      - name: "📥 Checkout du code source"
        uses: actions/checkout@v4

      - name: "🐍 Setup Python 3.10"
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: "📦 Installation des dépendances"
        run: pip install -r app/requirements.txt

      - name: "🔎 Analyse Snyk des dépendances"
        uses: snyk/actions/python@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: >-
            --severity-threshold=high
            --file=app/requirements.txt
            --sarif-file-output=snyk-results.sarif

      - name: "📊 Upload résultats Snyk vers GitHub Security"
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: snyk-results.sarif
          category: "SCA-Snyk"


  # ══════════════════════════════════════════════════════════
  # STAGE 4 — DAST (Dynamic Application Security Testing)
  #
  # Outil : OWASP ZAP (Zed Attack Proxy) — le standard industrie
  # Ce qu'il fait : lance l'application RÉELLE dans un container,
  # puis envoie des milliers de requêtes HTTP malformées pour
  # trouver des vulnérabilités en RUNTIME (ce que SAST ne peut pas voir).
  #
  # Types de tests effectués par ZAP :
  #   - SQL Injection (via fuzzing des paramètres)
  #   - XSS réfléchi et persistant
  #   - CSRF (Cross-Site Request Forgery)
  #   - Path Traversal
  #   - Headers de sécurité manquants (CSP, X-Frame-Options, etc.)
  #   - Informations sensibles exposées
  #
  # needs: [sast, container-scan] → Ce stage attend que les stages
  # 1 et 2 réussissent avant de démarrer.
  # Logique : pas besoin de scanner dynamiquement si le code a
  # déjà des vulnérabilités critiques identifiées.
  #
  # Limite du Baseline Scan : scan passif + actif limité.
  # Pour un scan complet : utiliser zaproxy/action-full-scan@v0.10.0
  # ══════════════════════════════════════════════════════════
  dast:
    name: "🌐 Stage 4 — DAST (OWASP ZAP)"
    runs-on: ubuntu-latest
    # Ce stage se lance SEULEMENT si SAST + Container Scan réussissent
    needs: [sast, container-scan]
    steps:
      - name: "📥 Checkout du code source"
        uses: actions/checkout@v4

      - name: "🏗️ Build et démarrage de l'application cible"
        run: |
          # Build de l'image
          docker build -t devsecops-app:dast .
          
          # Démarrage du container en background
          # --network host : ZAP pourra atteindre localhost:5000
          docker run -d \
            --name target-app \
            -p 5000:5000 \
            devsecops-app:dast
          
          # Attendre que Flask soit prêt
          echo "⏳ Attente du démarrage de l'application..."
          sleep 20
          
          # Vérification que l'app répond bien
          curl -f http://localhost:5000/ || (echo "❌ L'app ne répond pas" && exit 1)
          echo "✅ Application prête pour le scan DAST"

      - name: "🌐 Scan OWASP ZAP Baseline"
        uses: zaproxy/action-baseline@v0.12.0
        with:
          target: "http://localhost:5000"
          rules_file_name: ".zap/rules.tsv"
          # -I : ne pas échouer sur les alertes de niveau WARN
          # (seulement sur FAIL défini dans rules.tsv)
          cmd_options: "-I"
          # Générer un rapport HTML lisible
          allow_issue_writing: true

      - name: "💾 Sauvegarde du rapport ZAP HTML"
        uses: actions/upload-artifact@v4
        if: always()  # Toujours sauvegarder, même en cas d'échec
        with:
          name: zap-security-report
          path: report_html.html
          retention-days: 30

      - name: "💾 Sauvegarde du rapport ZAP JSON"
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: zap-json-report
          path: report_json.json
          retention-days: 30

      - name: "🛑 Arrêt du container cible"
        if: always()
        run: docker stop target-app && docker rm target-app


  # ══════════════════════════════════════════════════════════
  # STAGE 5 — SECURITY GATE (Rapport final)
  #
  # Ce job final agrège les résultats de tous les stages et
  # prend la décision finale : déployer ou bloquer.
  #
  # needs: [sast, container-scan, sca, dast]
  # → Attend que TOUS les stages soient terminés
  # → Si l'un d'eux a échoué (exit code 1), ce job ne bloquera
  #   pas le déploiement (c'est déjà bloqué en amont).
  #   Son rôle : afficher un rapport récapitulatif clair.
  # ══════════════════════════════════════════════════════════
  security-gate:
    name: "🚦 Stage 5 — Security Gate"
    runs-on: ubuntu-latest
    needs: [sast, container-scan, sca, dast]
    # Tourner même si certains jobs précédents ont échoué
    if: always()
    steps:
      - name: "📋 Rapport final de sécurité"
        run: |
          echo "╔══════════════════════════════════════════════╗"
          echo "║        RAPPORT SÉCURITÉ DEVSECOPS             ║"
          echo "║        Commit : ${{ github.sha }}             ║"
          echo "║        Branch : ${{ github.ref_name }}        ║"
          echo "╚══════════════════════════════════════════════╝"
          echo ""
          echo "📊 RÉSULTATS PAR STAGE :"
          echo "  Stage 1 SAST (Semgrep)   : ${{ needs.sast.result }}"
          echo "  Stage 2 Container (Trivy): ${{ needs.container-scan.result }}"
          echo "  Stage 3 SCA (Snyk)       : ${{ needs.sca.result }}"
          echo "  Stage 4 DAST (ZAP)       : ${{ needs.dast.result }}"
          echo ""

          # Logique de décision finale
          if [[ "${{ needs.sast.result }}" == "failure" || \
                "${{ needs.container-scan.result }}" == "failure" || \
                "${{ needs.sca.result }}" == "failure" || \
                "${{ needs.dast.result }}" == "failure" ]]; then
            echo "🔴 SECURITY GATE : ❌ DÉPLOIEMENT BLOQUÉ"
            echo "   Des vulnérabilités CRITIQUES ont été détectées."
            echo "   → Consulter l'onglet Security de GitHub"
            echo "   → Télécharger les rapports dans Actions > Artifacts"
            exit 1
          else
            echo "🟢 SECURITY GATE : ✅ DÉPLOIEMENT AUTORISÉ"
            echo "   Aucune vulnérabilité critique détectée."
            echo "   → Le code peut être déployé en production."
          fi
```
Dockerfile

```
# =============================================================
#  DOCKERFILE — Image de l'application Flask vulnérable
#  Scanné par : Trivy (Stage 2 du pipeline)
# =============================================================

# ─────────────────────────────────────────────────────────────
# BASE IMAGE : python:3.10-slim
#
# ⚠️  Pourquoi pas python:3.12-slim ?
#   python:3.10-slim contient plus de CVEs connues dans ses
#   packages système (openssl, libc, etc.) → meilleur pour la démo.
#
# Trivy va scanner TOUS les packages de cette image :
#   - Les packages Debian (dpkg) : openssl, libc6, etc.
#   - Les packages Python (pip) : flask, werkzeug, etc.
#   - Les secrets éventuellement copiés dans l'image
#
# ✅ FIX production : utiliser python:3.12-slim-bookworm
#   et mettre à jour régulièrement l'image de base.
# ─────────────────────────────────────────────────────────────
FROM python:3.10-slim

# Métadonnées de l'image (bonnes pratiques OCI)
LABEL maintainer="hasna.ahssar@example.com"
LABEL version="1.0.0-vulnerable"
LABEL description="App Flask volontairement vulnérable pour pipeline DevSecOps"

# Répertoire de travail dans le container
WORKDIR /app

# ─────────────────────────────────────────────────────────────
# COPY des fichiers de dépendances en PREMIER
# Principe : Docker cache chaque layer. En copiant requirements.txt
# séparément, si le code change mais pas les deps, Docker réutilise
# le cache de la layer pip install → build beaucoup plus rapide.
# ─────────────────────────────────────────────────────────────
COPY app/requirements.txt .

# Installation des dépendances Python
# --no-cache-dir : réduit la taille de l'image finale
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source de l'application
COPY app/ .

# ─────────────────────────────────────────────────────────────
# ❌ PROBLÈME DE SÉCURITÉ : l'app tourne en tant que root (uid=0)
#
#    Si un attaquant exploite une vuln dans l'app, il obtient un
#    shell root dans le container → pivot possible si le container
#    est mal configuré (--privileged, montage de /etc, etc.)
#
#    ✅ FIX :
#      RUN adduser --disabled-password --gecos '' appuser
#      USER appuser
# ─────────────────────────────────────────────────────────────

# Exposition du port Flask
EXPOSE 5000

# ─────────────────────────────────────────────────────────────
# Commande de démarrage
# Note : en production, utiliser gunicorn au lieu du serveur de dev Flask :
#   CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
# ─────────────────────────────────────────────────────────────
CMD ["python", "app.py"]
```

## 📁 Structure du projet

```
devsecops-pipeline/
├── .github/
│   └── workflows/
│       └── security-pipeline.yml   # Le pipeline complet (5 stages)
├── .zap/
│   └── rules.tsv                   # Règles OWASP ZAP : IGNORE / WARN / FAIL
├── app/
│   ├── app.py                      # Application Flask vulnérable (cible)
│   └── requirements.txt            # Dépendances intentionnellement obsolètes
├── Dockerfile                      # Image Docker de l'application
└── README.md
```

---

## 🚀 Installation et lancement

### Prérequis

- Un compte [GitHub](https://github.com) (gratuit)
- Un compte [Snyk](https://snyk.io) pour le token API (gratuit)

### Étapes

**1. Cloner le repo**
```bash
git clone https://github.com/Hasna2025/devsecops-pipeline.git
cd devsecops-pipeline
```

**2. Configurer les secrets GitHub**

Dans : `Settings → Secrets and variables → Actions → New repository secret`

| Secret | Où l'obtenir |
|--------|-------------|
| `SNYK_TOKEN` | [app.snyk.io](https://app.snyk.io) → Account Settings → API Token |
| `SEMGREP_TOKEN` | [semgrep.dev](https://semgrep.dev) → Settings → Tokens (optionnel) |

**3. Activer le Code Scanning**

`Settings → Security → Code security → Code scanning → Enable`

**4. Déclencher le pipeline**
```bash
git add .
git commit -m "test: trigger security pipeline"
git push origin main
```

Le pipeline se lance automatiquement. Observer les résultats dans l'onglet **Actions**.

---

## 📊 Résultats attendus

| Stage | Résultat attendu | Raison |
|-------|-----------------|--------|
| SAST Semgrep | ❌ Failure | 8 vulnérabilités détectées dans app.py |
| Container Trivy | ❌ Failure | CVEs CRITICAL dans Werkzeug 2.1.0 |
| SCA Snyk | ❌ Failure | Dépendances obsolètes avec CVEs HIGH |
| DAST ZAP | ⏭️ Skipped | Skippé car stages 1+2 ont échoué |
| Security Gate | ❌ Bloqué | Au moins 1 stage en failure |

C'est le comportement **normal et attendu**. Le pipeline fonctionne correctement : il détecte les failles et bloque le déploiement.

---

## 🔧 Exercice : corriger les vulnérabilités

Pour voir le pipeline passer au vert, créer une branche de fix :

```bash
git checkout -b fix/all-vulnerabilities
```

Corriger `app.py` :

```python
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
```

Corriger `requirements.txt` :
```
flask>=3.0.3
werkzeug>=3.0.3
cryptography>=42.0.0
```

```bash
git add .
git commit -m "fix: remediate all critical vulnerabilities"
git push origin fix/all-vulnerabilities
# → Créer une Pull Request → pipeline se relance → tout passe au vert ✅
```

---

<img width="854" height="214" alt="image" src="https://github.com/user-attachments/assets/560b0d24-aaa4-486b-97a7-d33cf0fb1627" />

<img width="820" height="323" alt="image" src="https://github.com/user-attachments/assets/1213e722-edcf-49e6-8ebd-76a2549bab4b" />


## 🛠️ Stack technique

| Outil | Rôle | Type | Coût |
|-------|------|------|------|
| GitHub Actions | Orchestration CI/CD | Cloud | Gratuit (2000 min/mois) |
| Semgrep | Analyse statique du code | SAST | Gratuit (open-source) |
| Trivy | Scan de l'image Docker | Container | Gratuit (open-source) |
| Snyk | Analyse des dépendances | SCA | Gratuit (compte free) |
| OWASP ZAP | Test dynamique en runtime | DAST | Gratuit (open-source) |
| Flask | Application cible vulnérable | App | Gratuit (open-source) |

---

## 📚 Concepts clés

**Shift-Left Security** : intégrer la sécurité le plus tôt possible dans le cycle de développement, plutôt qu'en fin de chaîne.

**SAST** : analyse du code source sans exécution. Rapide, détecte les patterns dangereux.

**DAST** : test de l'application en cours d'exécution. Détecte les vulnérabilités runtime.

**SCA** : analyse des dépendances tierces. Identifie les CVEs dans les librairies utilisées.

**CVE** : Common Vulnerabilities and Exposures — identifiant standardisé pour les failles de sécurité connues.

**Security Gate** : point de contrôle qui bloque automatiquement le déploiement si des critères de sécurité ne sont pas respectés.

---

*Projet DevSecOps réalisé dans le cadre d'une démarche de sécurisation du cycle de développement logiciel.*
