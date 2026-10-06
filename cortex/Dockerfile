# ============================================================
# Dockerfile — Analyseur VirusTotal pour Cortex 3.1.7
# Corrige l'incompatibilité Python 3.14 / cortexutils 2.2.1
#
# Problème : l'image officielle ghcr.io/thehive-project/
#             virustotal_getreport:3 utilise Python 3.14
#             incompatible avec cortexutils <= 2.2.1
#
# Solution : image custom basée sur Python 3.11-slim
#            avec copie des fichiers de l'analyseur
#            depuis l'image officielle
# ============================================================

FROM python:3.11-slim

WORKDIR /worker

# Copie des fichiers de l'analyseur depuis l'image officielle
COPY --from=ghcr.io/thehive-project/virustotal_getreport:3 /worker /worker

# Installation des dépendances compatibles Python 3.11
RUN apt-get update && apt-get install -y libmagic1 && \
    pip install cortexutils==2.2.1 requests python-magic filetype vt-py && \
    pip install -r /worker/VirusTotal/requirements.txt 2>/dev/null || true

ENTRYPOINT ["python3", "/worker/VirusTotal/virustotal.py"]
