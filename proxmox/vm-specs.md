# Spécifications des VMs — Proxmox VE 8.x

## Hôte Proxmox

| Paramètre | Valeur |
|---|---|
| Type | Bare Metal |
| RAM | 20 Go |
| Stockage | 256 Go SSD |
| Stockage type | LVM-thin (pve-data) |
| IP de gestion | 192.168.137.2 |
| Bridges | vmbr0 à vmbr5 |

## VMs

| VM ID | Nom | OS | vCPU | RAM | Disque | IP |
|---|---|---|---|---|---|---|
| 100 | DC01 | Windows Server 2022 | 2 | 6 Go | 80 Go | 192.168.20.10 |
| 101 | DC02 | Windows Server 2022 | 2 | 2 Go | 40 Go | 192.168.20.11 |
| 102 | pfSense | FreeBSD (pfSense 2.7.2) | 2 | 2 Go | 32 Go | WAN + 5 interfaces |
| 105 | serveur-web | Ubuntu 24.04 | 2 | 4 Go | 32 Go | 192.168.30.18 |
| 106 | wazuh-soc | Ubuntu 24.04 | 2 | 4 Go | 50 Go | 192.168.40.12 |
| 107 | soc-platform | Ubuntu 24.04 | 2 | 4 Go | 32 Go | 192.168.40.20 |
| 108 | kali-attaques | Kali Linux | 2 | 4 Go | 32 Go | 192.168.50.10 |

## Commandes utiles Proxmox

```bash
# Liste des VMs
qm list

# Arrêt propre d'une VM (toujours utiliser shutdown, jamais stop)
qm shutdown <VMID>

# Démarrage d'une VM
qm start <VMID>

# Sauvegarde d'une VM
vzdump <VMID> --compress zstd --dumpdir /var/lib/vz/dump --mode stop

# Sauvegarde de toutes les VMs
vzdump 100 101 102 105 106 107 108 \
  --compress zstd --dumpdir /var/lib/vz/dump --mode stop

# Restauration d'une VM
qmrestore /var/lib/vz/dump/vzdump-qemu-<VMID>-*.vma.zst <VMID> \
  --storage local-lvm

# Vérifier le thin-pool LVM
lvs | grep data

# Étendre le disque d'une VM depuis Proxmox
qm rescan --vmid <VMID>
```

## Gestion du thin-pool LVM

```bash
# Vérifier l'utilisation
lvs | grep data

# Étendre si nécessaire
lvextend -l +100%FREE pve/data

# En cas de saturation : arrêter les VMs inutilisées
qm shutdown <VMID>
```
