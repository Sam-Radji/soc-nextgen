# ============================================================
# deploy-wazuh.ps1 — Déploiement automatisé agents Wazuh
# SOC NextGen — Active Directory corp.local
#
# Prérequis :
#   - GPO-WinRM activée sur les OUs cibles
#   - Fichier wazuh-agent.msi copié dans \\DC01\Partages\WazuhAgent\
#   - Exécuter depuis DC01 en tant qu'Administrateur du domaine
# ============================================================

param(
    [string]$WazuhManager = "192.168.40.12",
    [string]$WazuhVersion = "4.x.x",
    [string]$OU = "OU=IT,DC=corp,DC=local"
)

$ErrorActionPreference = "Continue"
$LogFile = "C:\Logs\wazuh-deploy-$(Get-Date -Format 'yyyyMMdd-HHmm').log"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] [$Level] $Message"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line
}

# Création du dossier de logs
New-Item -ItemType Directory -Force -Path "C:\Logs" | Out-Null

Write-Log "=== Déploiement Wazuh Agent démarré ==="
Write-Log "Manager : $WazuhManager"
Write-Log "OU cible : $OU"

# Récupération des ordinateurs de l'OU
$computers = Get-ADComputer -Filter * -SearchBase $OU | Select-Object -ExpandProperty Name
Write-Log "Machines trouvées : $($computers.Count)"

$success = 0
$failed = 0

foreach ($computer in $computers) {
    Write-Log "--- Traitement de $computer ---"

    try {
        # Test de connectivité WinRM
        $session = New-PSSession -ComputerName $computer `
            -Authentication Negotiate `
            -ErrorAction Stop

        # Copie du MSI en local sur la machine cible
        Invoke-Command -Session $session -ScriptBlock {
            param($src)
            [System.IO.File]::Copy($src, "C:\Windows\Temp\wazuh-agent.msi", $true)
        } -ArgumentList "\\DC01\Partages\WazuhAgent\wazuh-agent.msi" -ErrorAction Stop

        # Installation silencieuse
        Invoke-Command -Session $session -ScriptBlock {
            param($manager)
            $args = "/i C:\Windows\Temp\wazuh-agent.msi /q " +
                    "WAZUH_MANAGER=$manager " +
                    "WAZUH_AGENT_GROUP=default " +
                    "WAZUH_REGISTRATION_SERVER=$manager"
            Start-Process "msiexec.exe" -ArgumentList $args -Wait -PassThru
        } -ArgumentList $WazuhManager -ErrorAction Stop

        # Démarrage du service
        Invoke-Command -Session $session -ScriptBlock {
            Start-Service -Name "WazuhSvc" -ErrorAction SilentlyContinue
            Set-Service -Name "WazuhSvc" -StartupType Automatic
        }

        Write-Log "$computer : ✅ Agent installé et démarré" "SUCCESS"
        $success++

        Remove-PSSession $session

    } catch {
        Write-Log "$computer : ❌ Échec — $($_.Exception.Message)" "ERROR"
        $failed++
    }
}

Write-Log "=== Déploiement terminé ==="
Write-Log "✅ Succès : $success / $($computers.Count)"
Write-Log "❌ Échecs : $failed / $($computers.Count)"
Write-Log "Log complet : $LogFile"
