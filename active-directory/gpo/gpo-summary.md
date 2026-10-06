# GPO déployées — Active Directory corp.local

## GPO-Securite

**Liée à** : Domaine entier  
**Objectif** : Renforcement de la politique de mots de passe et de verrouillage

| Paramètre | Valeur |
|---|---|
| Longueur minimale mot de passe | 10 caractères |
| Durée de vie maximale | 90 jours |
| Historique mots de passe | 5 derniers |
| Complexité requise | Activée |
| Tentatives avant verrouillage | 5 |
| Durée de verrouillage | 30 minutes |
| Réinitialisation compteur | 30 minutes |

---

## GPO-Audit

**Liée à** : Domaine entier  
**Objectif** : Activation de l'audit de sécurité complet pour alimenter Wazuh

| Événement | ID | Audit |
|---|---|---|
| Connexion réussie | 4624 | ✅ Activé |
| Échec de connexion | 4625 | ✅ Activé |
| Création de compte | 4720 | ✅ Activé |
| Suppression de compte | 4726 | ✅ Activé |
| Ajout à un groupe | 4728 | ✅ Activé |
| Verrouillage de compte | 4740 | ✅ Activé |
| Modification objet AD | 5136 | ✅ Activé |
| Modification de GPO | 5136 | ✅ Activé |

---

## GPO-WinRM

**Liée à** : OUs IT, RH, Direction  
**Objectif** : Activation WinRM pour déploiement automatisé des agents Wazuh

| Paramètre | Valeur |
|---|---|
| Service WinRM | Automatique + Démarré |
| Authentification | Negotiate activée |
| Accès réseau | Autorisé depuis DC01 |
| Firewall | Port 5985/5986 ouvert |

---

## GPO-IT

**Liée à** : OU=IT  
**Objectif** : Mappage lecteur réseau IT

| Paramètre | Valeur |
|---|---|
| Lettre lecteur | I: |
| Chemin UNC | \\\\DC01\\Partages\\IT |
| Accès | Lecture/Écriture (Grp-IT) |
| Reconnexion | Automatique |

---

## GPO-RH

**Liée à** : OU=RH  
**Objectif** : Mappage lecteur réseau RH + restrictions sécurité

| Paramètre | Valeur |
|---|---|
| Lettre lecteur | R: |
| Chemin UNC | \\\\DC01\\Partages\\RH |
| Accès | Lecture/Écriture (Grp-RH) |
| CMD/PowerShell | Désactivés |

---

## GPO-Direction

**Liée à** : OU=Direction  
**Objectif** : Accès aux partages IT, RH et Direction

| Lecteur | Chemin UNC | Accès |
|---|---|---|
| I: | \\\\DC01\\Partages\\IT | Lecture |
| R: | \\\\DC01\\Partages\\RH | Lecture |
| Z: | \\\\DC01\\Partages\\Direction | Lecture/Écriture |
