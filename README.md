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
# Vulnérabilité 1 : SQL Injection
query = f"SELECT * FROM users WHERE name = '{username}'"
# Attaque : ?name=' OR '1'='1  → expose toute la base

# Vulnérabilité 2 : XSS réfléchi
html = "<h1>Hello " + name + "</h1>"
# Attaque : ?name=<script>document.cookie</script>

# Vulnérabilité 3 : Secrets hardcodés
AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
# Risque : exposition des clés si le repo devient public

# Vulnérabilité 4 : Path Traversal
open(f"/tmp/{filename}", 'r')
# Attaque : ?file=../../../../etc/passwd
```

> ⚠️ Cette application ne doit jamais être déployée en production. Elle est uniquement destinée à servir de cible pour les outils de sécurité dans un contexte éducatif.

---

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
