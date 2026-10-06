# Architecture détaillée — SOC NextGen

## Hyperviseur — Proxmox VE 8.x

- **Type** : Bare metal (PC dédié)
- **RAM** : 20 Go
- **Stockage** : 256 Go SSD (LVM-thin)
- **Bridges réseau** : vmbr0 à vmbr5 (6 interfaces)
- **IP de gestion** : 192.168.137.2

## pfSense 2.7.2 — VM 102

| Interface | Bridge | Réseau | Rôle |
|---|---|---|---|
| vtnet0 | vmbr0 | WAN | Accès internet |
| vtnet1 | vmbr1 | 192.168.10.0/24 | LAN clients |
| vtnet2 | vmbr2 | 192.168.20.0/24 | AD |
| vtnet3 | vmbr3 | 192.168.30.0/24 | DMZ |
| vtnet4 | vmbr4 | 192.168.40.0/24 | SOC |
| vtnet5 | vmbr5 | 192.168.50.0/24 | Red Team |

### Port Forwarding configuré

| Port WAN | Destination | Service |
|---|---|---|
| :80 | 192.168.30.18:80 | HTTP Serveur web |
| :443 | 192.168.30.18:443 | HTTPS Serveur web |
| :8443 | 192.168.40.12:443 | Wazuh Dashboard |
| :9443 | 192.168.40.12:443 | Wazuh Dashboard (alt) |
| :9444 | 192.168.40.12:4443 | MISP |
| :5678 | 192.168.40.20:5678 | n8n SOAR |
| :3389 | 192.168.20.10:3389 | RDP DC01 |
| :22 | 192.168.30.18:22 | SSH Serveur web |

## Active Directory — Zone AD (192.168.20.0/24)

### DC01 — VM 100
- **IP** : 192.168.20.10
- **OS** : Windows Server 2022
- **RAM** : 6 Go / **Disque** : 80 Go
- **Rôles** : AD DS, DNS, FSMO (tous les rôles)
- **Outils** : Sysmon, Agent Wazuh

### DC02 — VM 101
- **IP** : 192.168.20.11
- **OS** : Windows Server 2022
- **RAM** : 2 Go / **Disque** : 40 Go
- **Rôles** : DC secondaire, DFS Replication
- **Outils** : Sysmon, Agent Wazuh

### Domaine
- **Nom** : corp.local *(anonymisé)*
- **OUs** : IT, RH, Direction
- **Groupes** : Grp-IT, Grp-RH, Grp-Direction

## Serveur Web — Zone DMZ (192.168.30.0/24)

- **VM** : 105
- **IP** : 192.168.30.18
- **OS** : Ubuntu 24.04
- **RAM** : 4 Go / **Disque** : 32 Go
- **Services** : Apache2, HTTPS (certificat auto-signé)
- **Monitoring** : Agent Wazuh + FIM (/var/www/html, /etc/apache2)

## Zone SOC (192.168.40.0/24)

### VM Wazuh — VM 106
- **IP** : 192.168.40.12
- **OS** : Ubuntu 24.04
- **RAM** : 4 Go / **Disque** : 50 Go
- **Services** :
  - Wazuh Manager (:1514 agents, :55000 API)
  - Wazuh Indexer (:9200)
  - Wazuh Dashboard (:443)
  - MISP (Docker, :4443)

### VM SOC Platform — VM 107
- **IP** : 192.168.40.20
- **OS** : Ubuntu 24.04
- **RAM** : 4 Go / **Disque** : 32 Go
- **Réseau Docker** : soc-network (bridge)
- **Services** :
  - Elasticsearch 7.17.9 (:9200)
  - Cassandra 4.1
  - TheHive 5.2 (:9000)
  - Cortex 3.1.7 (:9001)
  - n8n 2.x (:5678)
  - Registry local (:5000)
  - Python Flask Bridge (:5050, systemd)

## Zone Red Team (192.168.50.0/24)

- **VM** : 108
- **IP** : 192.168.50.10
- **OS** : Kali Linux
- **RAM** : 4 Go / **Disque** : 32 Go
- **Outils** : nmap, nikto, hydra, gobuster, sqlmap, hping3, sqlmap
