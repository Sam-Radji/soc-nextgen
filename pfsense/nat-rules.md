# Règles NAT — pfSense 2.7.2

## Port Forwarding (WAN → Zones internes)

| Description | Port WAN | Protocole | Destination | Port Dest |
|---|---|---|---|---|
| HTTP Serveur Web | 80 | TCP | 192.168.30.18 | 80 |
| HTTPS Serveur Web | 443 | TCP | 192.168.30.18 | 443 |
| SSH Serveur Web | 22 | TCP | 192.168.30.18 | 22 |
| RDP DC01 | 3389 | TCP | 192.168.20.10 | 3389 |
| Wazuh Dashboard | 9443 | TCP | 192.168.40.12 | 443 |
| MISP | 9444 | TCP | 192.168.40.12 | 4443 |
| n8n SOAR | 5678 | TCP | 192.168.40.20 | 5678 |

## Blocage IP dynamique

Table pfSense `blocklist` — alimentée automatiquement par n8n via SSH :

```bash
# Ajouter une IP à la liste de blocage
pfctl -t blocklist -T add <IP>

# Voir les IPs bloquées
pfctl -t blocklist -T show

# Supprimer une IP
pfctl -t blocklist -T delete <IP>

# Vider la liste
pfctl -t blocklist -T flush
```

> ⚠️ La table `blocklist` est volatile — elle disparaît au redémarrage de pfSense.  
> Pour la rendre persistante, ajouter une règle Floating dans `Firewall → Rules → Floating`.
