#!/usr/bin/env python3
"""
wazuh_to_thehive.py — Python Flask Bridge SOAR
SOC NextGen — Pipeline Wazuh → TheHive → Cortex → MISP → Telegram

Fonctionnement :
  1. Reçoit les alertes Wazuh via webhook (:5050)
  2. Envoie une alerte Telegram immédiate
  3. Crée un case dans TheHive
  4. Ajoute l'IP source comme observable
  5. Lance une analyse Cortex (VirusTotal)
  6. Vérifie l'IoC dans MISP
"""

import json
import requests
from flask import Flask, request, jsonify
from datetime import datetime
import pytz

app = Flask(__name__)

# ============================================================
# CONFIGURATION — À adapter selon votre environnement
# ============================================================

TELEGRAM_TOKEN = "VOTRE_BOT_TOKEN"
TELEGRAM_CHAT_ID = "VOTRE_CHAT_ID"

THEHIVE_URL = "http://192.168.40.20:9000"
THEHIVE_USER = "analyst@corp.local"
THEHIVE_PASS = "VOTRE_MOT_DE_PASSE"

CORTEX_URL = "http://192.168.40.20:9001"
CORTEX_API_KEY = "VOTRE_CLE_API_CORTEX"
CORTEX_ANALYZER_ID = "VirusTotal_GetReport_3_1"

MISP_URL = "https://192.168.40.12:4443"
MISP_API_KEY = "VOTRE_CLE_API_MISP"

TIMEZONE = "Africa/Dakar"

# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================

def get_severity(level):
    """Retourne le niveau de criticité et l'emoji correspondant."""
    level = int(level)
    if level >= 13:
        return "🔴 CRITIQUE", 3
    elif level >= 10:
        return "🟠 ÉLEVÉ", 3
    elif level >= 7:
        return "🟡 MOYEN", 2
    else:
        return "🟢 BAS", 1


def send_telegram(message):
    """Envoie un message Telegram formaté en HTML."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            print("[Telegram] ✅ Alerte envoyée")
        else:
            print(f"[Telegram] ❌ Erreur : {resp.text}")
    except Exception as e:
        print(f"[Telegram] ❌ Exception : {e}")


def create_thehive_case(title, description, severity, tags):
    """Crée un case dans TheHive et retourne son ID."""
    try:
        url = f"{THEHIVE_URL}/api/v1/case"
        payload = {
            "title": title,
            "description": description,
            "severity": severity,
            "tags": tags,
            "tlp": 2,
            "pap": 2,
            "status": "New"
        }
        resp = requests.post(
            url, json=payload,
            auth=(THEHIVE_USER, THEHIVE_PASS),
            timeout=15
        )
        if resp.status_code in [200, 201]:
            case_id = resp.json().get("_id")
            print(f"[TheHive] ✅ Case créé : {case_id}")
            return case_id
        else:
            print(f"[TheHive] ❌ Erreur création case : {resp.text}")
            return None
    except Exception as e:
        print(f"[TheHive] ❌ Exception : {e}")
        return None


def add_thehive_observable(case_id, ip):
    """Ajoute une IP comme observable dans un case TheHive."""
    try:
        url = f"{THEHIVE_URL}/api/v1/case/{case_id}/observable"
        payload = {
            "dataType": "ip",
            "data": ip,
            "message": "IP source de l'attaque détectée par Wazuh",
            "tlp": 2,
            "pap": 2,
            "ioc": True
        }
        resp = requests.post(
            url, json=payload,
            auth=(THEHIVE_USER, THEHIVE_PASS),
            timeout=15
        )
        if resp.status_code in [200, 201]:
            print(f"[TheHive] ✅ Observable IP ajouté : {ip}")
        else:
            print(f"[TheHive] ❌ Erreur observable : {resp.text}")
    except Exception as e:
        print(f"[TheHive] ❌ Exception observable : {e}")


def run_cortex_analysis(ip):
    """Lance une analyse VirusTotal via Cortex sur une IP."""
    try:
        url = f"{CORTEX_URL}/api/analyzer/{CORTEX_ANALYZER_ID}/run"
        payload = {
            "data": ip,
            "dataType": "ip",
            "tlp": 2,
            "pap": 2,
            "parameters": {}
        }
        resp = requests.post(
            url, json=payload,
            headers={"Authorization": f"Bearer {CORTEX_API_KEY}"},
            timeout=30
        )
        if resp.status_code in [200, 201]:
            job_id = resp.json().get("id")
            print(f"[Cortex] ✅ Analyse lancée : {job_id}")
            return job_id
        else:
            print(f"[Cortex] ❌ Erreur analyse : {resp.text}")
            return None
    except Exception as e:
        print(f"[Cortex] ❌ Exception : {e}")
        return None


def check_misp_ioc(ip):
    """Vérifie si une IP est un IoC connu dans MISP."""
    try:
        url = f"{MISP_URL}/attributes/restSearch"
        payload = {"value": ip, "type": "ip-dst", "returnFormat": "json"}
        resp = requests.post(
            url, json=payload,
            headers={
                "Authorization": MISP_API_KEY,
                "Accept": "application/json"
            },
            verify=False,
            timeout=15
        )
        if resp.status_code == 200:
            attrs = resp.json().get("response", {}).get("Attribute", [])
            if attrs:
                print(f"[MISP] ⚠️  IP connue comme IoC : {ip}")
                return True
            print(f"[MISP] ✅ IP non référencée : {ip}")
            return False
        return False
    except Exception as e:
        print(f"[MISP] ❌ Exception : {e}")
        return False


# ============================================================
# WEBHOOK PRINCIPAL
# ============================================================

@app.route("/webhook", methods=["POST"])
def webhook():
    """Point d'entrée principal — reçoit les alertes Wazuh."""
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "No data"}), 400

        # Extraction des champs
        rule = data.get("rule", {})
        agent = data.get("agent", {})
        event_data = data.get("data", {})

        rule_id = rule.get("id", "N/A")
        level = rule.get("level", 0)
        description = rule.get("description", "Alerte Wazuh")
        agent_name = agent.get("name", "N/A")
        agent_ip = agent.get("ip", "N/A")
        src_ip = event_data.get("srcip", "N/A")
        src_user = event_data.get("srcuser", "N/A")

        # Filtre niveau minimum
        if int(level) < 7:
            return jsonify({"status": "ignored", "reason": "level too low"}), 200

        # Date et heure WAT
        now = datetime.now(pytz.timezone(TIMEZONE))
        date_str = now.strftime("%d/%m/%Y")
        time_str = now.strftime("%H:%M:%S")

        emoji_level, severity = get_severity(level)

        # 1. Alerte Telegram immédiate
        tg_message = f"""
╔══════════════════════════════════╗
🛡️ <b>ALERTE SOC</b>
╚══════════════════════════════════╝

{emoji_level}

📋 <b>Règle :</b> {rule_id} — {description}
🖥️ <b>Machine :</b> {agent_name} ({agent_ip})
🌐 <b>IP Source :</b> {src_ip}
👤 <b>Utilisateur :</b> {src_user}
⚡ <b>Niveau :</b> {level}/15

📅 <b>Date :</b> {date_str}
🕐 <b>Heure :</b> {time_str} (WAT)

<i>⏳ Traitement SOC en cours...</i>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        send_telegram(tg_message.strip())

        # 2. Création case TheHive
        case_title = f"[Wazuh] {description}"
        case_desc = (
            f"**Règle Wazuh** : {rule_id} — {description}\n\n"
            f"**Machine** : {agent_name} ({agent_ip})\n"
            f"**IP Source** : {src_ip}\n"
            f"**Utilisateur** : {src_user}\n"
            f"**Niveau** : {level}/15\n"
            f"**Date** : {date_str} {time_str} WAT"
        )
        case_id = create_thehive_case(
            title=case_title,
            description=case_desc,
            severity=severity,
            tags=["wazuh", f"rule-{rule_id}", agent_name]
        )

        # 3. Observable IP + Cortex + MISP
        if case_id and src_ip != "N/A":
            add_thehive_observable(case_id, src_ip)
            run_cortex_analysis(src_ip)
            is_ioc = check_misp_ioc(src_ip)

            # 4. Telegram — résumé pipeline
            summary = f"""
✅ <b>Pipeline SOC terminé</b>

📋 Règle : {rule_id}
🌐 IP analysée : {src_ip}
🔬 Cortex VirusTotal : Analyse lancée
🔍 MISP : {"⚠️ IoC connu !" if is_ioc else "Vérification effectuée"}

🚨 <b>Alerte traitée complètement</b>
"""
            send_telegram(summary.strip())

        return jsonify({"status": "ok", "case_id": case_id}), 200

    except Exception as e:
        print(f"[Webhook] ❌ Exception : {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    """Endpoint de santé."""
    return jsonify({"status": "ok", "service": "wazuh-thehive-bridge"}), 200


if __name__ == "__main__":
    print("[SOC Bridge] Démarrage sur :5050...")
    app.run(host="0.0.0.0", port=5050, debug=False)
