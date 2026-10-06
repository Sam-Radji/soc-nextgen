# 🛡️ SOC NextGen — Infrastructure critique Afrique de l'Ouest

![Wazuh](https://img.shields.io/badge/Wazuh-4.x-orange?style=flat-square)
![TheHive](https://img.shields.io/badge/TheHive-5.2-yellow?style=flat-square)
![Cortex](https://img.shields.io/badge/Cortex-3.1.7-green?style=flat-square)
![pfSense](https://img.shields.io/badge/pfSense-2.7.2-blue?style=flat-square)
![Proxmox](https://img.shields.io/badge/Proxmox-VE%208.x-darkblue?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-standalone-blue?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square)

> Étude et mise en place d'un Centre Opérationnel de Sécurité de nouvelle génération dans un environnement entièrement virtualisé.  
> Projet réalisé dans le cadre d'un stage de 4 mois au sein d'une infrastructure critique en Afrique de l'Ouest.

---

## 📋 Table des matières

- [Architecture](#architecture)
- [Stack technique](#stack-technique)
- [Fonctionnalités](#fonctionnalités)
- [Pipeline SOAR](#pipeline-soar)
- [Résultats](#résultats)
- [Structure du dépôt](#structure-du-dépôt)
- [Installation](#installation)
- [Auteur](#auteur)

---

## 🏗️ Architecture

### Vue d'ensemble

```
INTERNET (WAN)
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│                    pfSense 2.7.2                            │
│         Firewall · NAT · Routage · Port Forwarding          │
└──┬─────┬──────┬──────┬──────┬─────────────────────────────┘
   │     │      │      │      │
   ▼     ▼      ▼      ▼      ▼
  LAN   AD     DMZ    SOC  RedTeam
```

### Segmentation réseau — 6 zones isolées

| Zone | Réseau | Bridge | Rôle |
|---|---|---|---|
| WAN | 10.30.130.0/24 | vmbr0 | Internet, NAT outbound |
| LAN | 192.168.10.0/24 | vmbr1 | Postes clients IT/RH/Direction |
| AD | 192.168.20.0/24 | vmbr2 | Contrôleurs de domaine |
| DMZ | 192.168.30.0/24 | vmbr3 | Serveur web Apache2 |
| SOC | 192.168.40.0/24 | vmbr4 | Wazuh, MISP, TheHive, Cortex, n8n |
| Red Team | 192.168.50.0/24 | vmbr5 | Kali Linux — tests d'intrusion |

### VMs déployées

| VM ID | Rôle | OS | RAM | Stockage |
|---|---|---|---|---|
| 100 | DC01 — FSMO/DNS | Windows Server 2022 | 6 Go | 80 Go |
| 101 | DC02 — secondaire/DFS | Windows Server 2022 | 2 Go | 40 Go |
| 102 | pfSense — Firewall | FreeBSD (pfSense 2.7.2) | 2 Go | 32 Go |
| 105 | Serveur web — DMZ | Ubuntu 24.04 | 4 Go | 32 Go |
| 106 | Wazuh + MISP | Ubuntu 24.04 | 4 Go | 50 Go |
| 107 | SOC Platform | Ubuntu 24.04 | 4 Go | 32 Go |
| 108 | Kali Linux — Red Team | Kali Linux | 4 Go | 32 Go |

---

## 🧰 Stack technique

### Infrastructure
- **Hyperviseur** : Proxmox VE 8.x (bare metal, 20 Go RAM / 256 Go SSD)
- **Firewall/Routeur** : pfSense 2.7.2 — 6 interfaces réseau
- **Active Directory** : Windows Server 2022 — domaine `corp.local`

### SOC Platform
- **SIEM/XDR** : Wazuh 4.x — Manager + Indexer + Dashboard
- **Threat Intelligence** : MISP (Docker, feeds CIRCL + Abuse.ch)
- **Gestion incidents** : TheHive 5.2 (Docker)
- **Analyse IoC** : Cortex 3.1.7 (Docker + image custom Python 3.11)
- **SOAR** : n8n 2.x (Docker) + Python Flask Bridge (systemd)
- **Notifications** : Telegram Bot API — boutons interactifs

### Red Team
- **Kali Linux** — nmap, nikto, hydra, gobuster, sqlmap, hping3

---

## ✨ Fonctionnalités

### Détection
- ✅ 4 agents Wazuh actifs (DC01, DC02, USERS-LOCAL, serveur-web)
- ✅ Sysmon déployé sur tous les postes Windows
- ✅ File Integrity Monitoring (FIM) sur fichiers critiques
- ✅ 31 règles de détection personnalisées (IDs 100001–100031)
- ✅ Détection : brute force, scan ports, injection SQL, création comptes, modifications SYSVOL, outils offensifs

### Réponse automatisée
- ✅ Alerte Telegram en moins de 5 secondes
- ✅ Création automatique de cases TheHive
- ✅ Analyse IoC via Cortex/VirusTotal
- ✅ Vérification MISP (feeds CIRCL, Abuse.ch URLhaus, Feodo Tracker)
- ✅ Boutons Telegram interactifs : Approuver (blocage IP pfSense) ou Décliner (faux positif)
- ✅ Blocage IP via SSH pfSense : `pfctl -t blocklist -T add <IP>`

### Active Directory
- ✅ Dual DC avec réplication + DFS
- ✅ GPO : sécurité mots de passe, audit complet, WinRM
- ✅ Déploiement automatisé des agents Wazuh via PowerShell WinRM
- ✅ Partages réseau IT (I:), RH (R:), Direction (Z:)

---

## 🔄 Pipeline SOAR

```
Wazuh (détection niveau ≥ 7)
         │
         ▼
   Webhook :5678 (n8n)
         │
         ▼
   Telegram — Alerte immédiate < 5s
         │
         ▼
   TheHive — Création case automatique
         │
         ▼
   Cortex — Analyse VirusTotal (IP source)
         │
         ▼
   MISP — Vérification IoC
         │
         ▼
   Telegram — Boutons interactifs
    ┌────┴────┐
    ▼         ▼
Approuver   Décliner
    │         │
    ▼         ▼
pfSense     TheHive
SSH pfctl   FalsePositive
blocklist
```

---

## 📊 Résultats

### Tests d'intrusion Black Box (Kali Linux → pfSense WAN)

| # | Scénario | Outil | Règle Wazuh | Résultat |
|---|---|---|---|---|
| 01 | Reconnaissance réseau | nmap -sV -A | 100012 | ✅ Détecté |
| 02 | Brute Force SSH | hydra | 100030 | ✅ Détecté |
| 03 | Brute Force RDP (AD) | hydra | Event 4625 | ✅ Détecté |
| 04 | Scan vulnérabilités web | nikto | 100012 | ✅ Détecté |
| 05 | Énumération répertoires | gobuster | 100013 | ✅ Détecté |
| 06 | Injection SQL | sqlmap | 100010 | ✅ Détecté |
| 07 | Modification fichier web | curl/bash | FIM | ✅ Détecté |

### Métriques clés

| Métrique | Valeur |
|---|---|
| VMs déployées | 7 |
| Zones réseau isolées | 6 |
| Agents Wazuh actifs | 4 |
| Règles de détection custom | 31 |
| Délai alerte Telegram | < 5 secondes |
| Scénarios d'attaques validés | 7 / 7 |

---

## 📁 Structure du dépôt

```
soc-nextgen/
│
├── README.md
├── docs/
│   ├── architecture.md          # Architecture détaillée
│   ├── network-zones.md         # Description des zones réseau
│   └── pipeline-soar.md         # Pipeline SOAR complet
│
├── proxmox/
│   └── vm-specs.md              # Specs et configs des VMs
│
├── pfsense/
│   ├── nat-rules.md             # Règles NAT/Port Forwarding
│   └── firewall-rules.md        # Règles firewall par zone
│
├── active-directory/
│   ├── gpo/
│   │   └── gpo-summary.md       # Résumé des GPO déployées
│   └── deploy-wazuh.ps1         # Script déploiement agents
│
├── wazuh/
│   ├── rules/
│   │   └── local_rules.xml      # 31 règles de détection custom
│   └── ossec.conf               # Config intégrations webhook
│
├── cortex/
│   ├── Dockerfile               # Image custom Python 3.11
│   ├── application.conf         # Config Cortex
│   └── analyzers.json           # Config analyseurs (VirusTotal...)
│
├── soar/
│   ├── wazuh_to_thehive.py      # Python Flask bridge
│   ├── requirements.txt         # Dépendances Python
│   └── wazuh-thehive.service    # Service systemd
│
├── n8n/
│   └── workflow-wazuh-alerts.json  # Export workflow n8n
│
└── red-team/
    └── scenarios.md             # 7 scénarios d'attaques
```

---

## 🚀 Installation

### Prérequis
- Proxmox VE 8.x installé sur machine bare metal
- Minimum 20 Go RAM / 256 Go SSD
- Accès internet pour télécharger les images

### Déploiement rapide

```bash
# 1. Cloner le dépôt
git clone https://github.com/Sam-Radji/soc-nextgen.git
cd soc-nextgen

# 2. Déployer la VM SOC Platform (TheHive + Cortex + n8n)
# Voir docs/architecture.md pour les détails

# 3. Lancer le bridge Python SOAR
sudo cp soar/wazuh-thehive.service /etc/systemd/system/
sudo systemctl enable --now wazuh-thehive

# 4. Construire l'image Cortex custom
cd cortex/
sudo docker build -t localhost:5000/virustotal_getreport:3 .
sudo docker push localhost:5000/virustotal_getreport:3
```

> 📖 Voir le dossier `docs/` pour la documentation complète de chaque composant.

---

## ⚠️ Disclaimer

> Les adresses IP utilisées dans ce projet sont des adresses privées RFC 1918 choisies par l'auteur dans le cadre d'un lab.  
> Les noms d'entreprise et de domaine ont été anonymisés pour des raisons de confidentialité.

---

## 👤 Auteur

**Samsidine Touré**  
Licence Pro ADSILLH — Université de Bordeaux  
Admis en Master Cybersécurité — ESGI Bordeaux (rentrée 2026)  
🔍 En recherche d'alternance en cybersécurité (SOC / BlueTeam / SecOps)

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Samsidine%20Touré-blue?style=flat-square&logo=linkedin)](https://linkedin.com/in/samsidine-touré-1b2a6a284)
[![GitHub](https://img.shields.io/badge/GitHub-Sam__Radji-black?style=flat-square&logo=github)](https://github.com/Sam-Radji)
