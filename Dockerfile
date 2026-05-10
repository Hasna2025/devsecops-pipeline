# =============================================================
# 🔒 ULTRA MINIMAL SECURE IMAGE (Trivy-friendly)
# =============================================================

FROM python:3.12-alpine

# ─────────────────────────────────────────────────────────────
# Labels
# ─────────────────────────────────────────────────────────────
LABEL maintainer="secure-app"
LABEL version="1.0-secure"

# ─────────────────────────────────────────────────────────────
# Security hardening
# ─────────────────────────────────────────────────────────────
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app

# ─────────────────────────────────────────────────────────────
# Dependencies (minimal + clean)
# ─────────────────────────────────────────────────────────────
COPY app/requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --no-cache-dir -r requirements.txt

# ─────────────────────────────────────────────────────────────
# App copy
# ─────────────────────────────────────────────────────────────
COPY app/ .

# ─────────────────────────────────────────────────────────────
# Permissions
# ─────────────────────────────────────────────────────────────
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 5000

CMD ["python", "app.py"]