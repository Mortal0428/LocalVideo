$ErrorActionPreference = "Stop"
$destDir = "E:\tools\redis"
if (!(Test-Path $destDir)) {
    New-Item -ItemType Directory -Path $destDir -Force | Out-Null
}

$zipPath = Join-Path $destDir "redis.zip"
$urls = @(
    "https://github.com/tporadowski/redis/releases/download/v5.0.14.1/Redis-x64-5.0.14.1.zip",
    "https://ghproxy.net/https://github.com/tporadowski/redis/releases/download/v5.0.14.1/Redis-x64-5.0.14.1.zip"
)

$downloaded = $false
foreach ($u in $urls) {
    try {
        Write-Host "Attempting download from $u..."
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $u -OutFile $zipPath -TimeoutSec 20
        $downloaded = $true
        Write-Host "Download completed successfully!"
        break
    } catch {
        Write-Host "Failed from $u : $($_.Exception.Message)"
    }
}

if ($downloaded -and (Test-Path $zipPath)) {
    Write-Host "Extracting Redis to $destDir..."
    Expand-Archive -Path $zipPath -DestinationPath $destDir -Force
    Remove-Item $zipPath -Force
    Write-Host "Extraction completed!"
} else {
    Write-Host "All downloads failed, check network or use fallback."
}
