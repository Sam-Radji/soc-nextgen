# Pipeline SOAR — Détection à la réponse automatisée

## Vue d'ensemble

Le pipeline SOAR orchestre la chaîne complète de traitement des incidents :
de la détection par Wazuh jusqu'à la réponse automatisée (blocage IP ou marquage faux positif).

**Délai total : moins de 5 secondes.**

## Flux complet

```
┌─────────────────────────────────────────────────────────────────┐
│  SOURCES (agents Wazuh)                                         │
│  DC01 · DC02 · USERS-LOCAL · serveur-web                       │
└────────────────────┬────────────────────────────────────────────┘
                     │ logs + événements
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  WAZUH SIEM/XDR (192.168.40.12)                                │
│  Corrélation · Détection · 31 règles custom                    │
└──────┬──────────────────────┬──────────────────────────────────┘
       │ webhook (niveau ≥ 7)  │ webhook (niveau ≥ 7)
       ▼                       ▼
┌────────────┐         ┌────────────────────┐
│  Python    │         │  n8n SOAR          │
│  Flask     │         │  :5678/webhook/    │
│  Bridge    │         │  wazuh             │
│  :5050     │         └────────┬───────────┘
└────────────┘                  │
                                ▼
                    ┌───────────────────────┐
                    │  Telegram Bot         │
                    │  Alerte immédiate     │
                    │  Règle · IP · Machine │
                    │  Niveau · Date/Heure  │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  TheHive 5.2          │
                    │  Création case auto   │
                    │  Observable IP source │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Cortex 3.1.7         │
                    │  VirusTotal analyse   │
                    │  IP source            │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  MISP                 │
                    │  Vérification IoC     │
                    │  Feeds CIRCL/Abuse.ch │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Telegram Bot         │
                    │  Boutons interactifs  │
                    │  [Approuver][Décliner]│
                    └──────┬────────┬───────┘
                           │        │
                    ┌──────┘        └──────┐
                    ▼                      ▼
          ┌─────────────────┐    ┌─────────────────┐
          │  pfSense SSH    │    │  TheHive PATCH  │
          │  pfctl -t       │    │  status:        │
          │  blocklist -T   │    │  FalsePositive  │
          │  add <IP>       │    └─────────────────┘
          └─────────────────┘
```

## Composants du pipeline

### 1. Wazuh — Détection

- Niveau minimum pour déclencher le pipeline : **7**
- Intégrations configurées dans `ossec.conf` :
  - `custom-python` → Python Flask Bridge (:5050)
  - `custom-n8n` → n8n (:5678)

### 2. Python Flask Bridge (:5050)

Script `wazuh_to_thehive.py` exécuté comme service systemd.

Fonctions :
- Réception des alertes Wazuh
- Envoi alerte Telegram formatée
- Création case TheHive
- Ajout observable IP
- Lancement analyse Cortex
- Vérification MISP

### 3. n8n SOAR — Workflow `wazuh-alerts`

Nœuds du workflow :
1. **Webhook** (POST /webhook/wazuh)
2. **IF** (level > 10)
3. **Wait** (anti-déduplication)
4. **Telegram** (alerte immédiate)
5. **TheHive** (Create a case)
6. **Cortex** (Execute an analyzer)
7. **TheHive** (Create an observable)
8. **MISP** (Get filtered list of attributes)
9. **Telegram** (Send message and wait for response)
10. **Switch** (Approuver / Décliner)
    - **Approuver** → Edit Fields → SSH pfSense
    - **Décliner** → TheHive Update case (FalsePositive)

### 4. Telegram Bot — Format des alertes

```
╔══════════════════════════════════╗
🛡️ ALERTE SOC
╚══════════════════════════════════╝

🟠 ÉLEVÉ

📋 Règle : 100030 — Brute force SSH
🖥️ Machine : serveur-web (192.168.30.18)
🌐 IP Source : 192.168.137.196
👤 Utilisateur : root
⚡ Niveau : 12/15

📅 Date : 29/07/2026
🕐 Heure : 09:21:45 (WAT)
```

### 5. Blocage IP — pfSense

Commande exécutée via SSH par n8n :

```bash
pfctl -t blocklist -T add <IP_ATTAQUANTE>
```

Vérification :
```bash
pfctl -t blocklist -T show
```

## Credentials n8n configurés

| Service | Type | Notes |
|---|---|---|
| TheHive | Basic Auth | user:password |
| Cortex | API Key | clé API Cortex |
| MISP | Header Auth | Authorization: clé MISP |
| pfSense | SSH Password | admin@192.168.40.1 |
| Telegram | Bot Token | token bot Telegram |
