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