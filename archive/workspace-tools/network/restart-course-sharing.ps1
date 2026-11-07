param([Parameter(Mandatory=$true)][string]$LogPath)

$ErrorActionPreference = 'Stop'
$labIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$labPrincipal = [Security.Principal.WindowsPrincipal]::new($labIdentity)
if (-not $labPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Administrator permission is required to restart the Windows sharing service.'
}
$labEthernetAdapter = @(Get-NetAdapter | Where-Object {
    $_.InterfaceIndex -eq 8 -and $_.InterfaceDescription -eq 'Realtek PCIe GbE Family Controller'
})
if ($labEthernetAdapter.Count -ne 1) { throw 'Expected course Ethernet adapter is missing; no service was changed.' }
$labEthernetName = $labEthernetAdapter[0].Name
Start-Transcript -LiteralPath $LogPath -Force | Out-Null
try {
    function Get-CourseSharing {
        $labManager = New-Object -ComObject HNetCfg.HNetShare.1
        $labConnections = @($labManager.EnumEveryConnection)
        $labRows = foreach ($labConnection in $labConnections) {
            $labProperties = $labManager.NetConnectionProps($labConnection)
            $labConfiguration = $labManager.INetSharingConfigurationForINetConnection($labConnection)
            [pscustomobject]@{
                Name = $labProperties.Name
                Enabled = $labConfiguration.SharingEnabled
                Type = $(if ($labConfiguration.SharingEnabled) { [int]$labConfiguration.SharingConnectionType } else { -1 })
                Configuration = $labConfiguration
            }
        }
        return @($labRows)
    }

    $labBefore = @(Get-CourseSharing)
    $labPublic = @($labBefore | Where-Object { $_.Name -eq 'WLAN' })
    $labPrivate = @($labBefore | Where-Object { $_.Name -eq $labEthernetName })
    if ($labPublic.Count -ne 1 -or $labPrivate.Count -ne 1) {
        throw 'Expected exactly one WLAN and one Ethernet interface; no service was changed.'
    }
    if (@($labBefore | Where-Object { $_.Enabled -and $_.Type -eq 0 -and $_.Name -ne 'WLAN' }).Count -gt 0) {
        throw 'Another public sharing interface is active; review it before changing sharing.'
    }
    Write-Output ('Started: ' + (Get-Date -Format o))
    Write-Output 'Before:'
    $labBefore | Select-Object Name,Enabled,Type | Format-Table | Out-String | Write-Output

    # Target only the Internet Connection Sharing service and the course's
    # WLAN-to-Ethernet sharing bindings. Leave other adapters and registry alone.
    Restart-Service -Name SharedAccess -ErrorAction Stop
    (Get-Service -Name SharedAccess).WaitForStatus('Running', [TimeSpan]::FromSeconds(20))

    $labAfterRestart = @(Get-CourseSharing)
    $labPublic = @($labAfterRestart | Where-Object { $_.Name -eq 'WLAN' })
    $labPrivate = @($labAfterRestart | Where-Object { $_.Name -eq $labEthernetName })
    if ($labPublic.Count -ne 1 -or $labPrivate.Count -ne 1) {
        throw 'Could not locate the course sharing interfaces after service restart.'
    }
    if (-not $labPublic[0].Enabled -or $labPublic[0].Type -ne 0) {
        $labPublic[0].Configuration.EnableSharing(0)
    }
    if (-not $labPrivate[0].Enabled -or $labPrivate[0].Type -ne 1) {
        $labPrivate[0].Configuration.EnableSharing(1)
    }
    Write-Output 'After:'
    Get-CourseSharing | Select-Object Name,Enabled,Type | Format-Table | Out-String | Write-Output
    Get-NetIPAddress -InterfaceAlias $labEthernetName -AddressFamily IPv4 |
        Select-Object IPAddress,PrefixLength,AddressState | Format-Table | Out-String | Write-Output
    Write-Output 'Sharing service restart completed. Board DHCP/SSH still needs verification.'
} catch {
    Write-Output ('FAILED: ' + $_.Exception.Message)
    throw
} finally {
    Stop-Transcript | Out-Null
}
