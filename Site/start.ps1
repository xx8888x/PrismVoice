$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$phpPath = Join-Path $projectRoot '.runtime\php\php.exe'
$databaseConfig = Join-Path $projectRoot '.runtime\database\my.ini'
$databasePidPath = Join-Path $projectRoot '.runtime\database.pid'
$serverPidPath = Join-Path $projectRoot '.runtime\server.pid'
function Test-ProjectProcess($pidPath, $expectedPath) {
    if (-not (Test-Path -LiteralPath $pidPath)) { return $false }
    $savedPid = [int](Get-Content -LiteralPath $pidPath)
    $process = Get-Process -Id $savedPid -ErrorAction SilentlyContinue
    return $process -and ($process.Path -eq $expectedPath -or $process.Name -match "python")
}
$databaseExe = 'D:\xampp\mysql\bin\mysqld.exe'
if (-not (Test-ProjectProcess $databasePidPath $databaseExe)) {
    $process = Start-Process -FilePath $databaseExe -ArgumentList "--defaults-file=$databaseConfig", "--datadir=D:\稜鏡媒體網站\Site\.runtime\database", "--log-error=D:\稜鏡媒體網站\Site\.runtime\database\error.log" -WindowStyle Hidden -PassThru
    $process.Id | Set-Content -LiteralPath $databasePidPath
}
if (-not (Test-ProjectProcess $serverPidPath $phpPath)) {
    $process = Start-Process -FilePath $phpPath -ArgumentList '-S','127.0.0.1:8088','-t','public','../server-router.php' -WorkingDirectory (Join-Path $projectRoot 'backend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectRoot '.runtime\server-out.log') -RedirectStandardError (Join-Path $projectRoot '.runtime\server-error.log') -PassThru
    $process.Id | Set-Content -LiteralPath $serverPidPath
}
$pythonPidPath = Join-Path $projectRoot '.runtime\python.pid'
if (-not (Test-ProjectProcess $pythonPidPath 'python.exe')) {
    $process = Start-Process -FilePath 'python' -ArgumentList 'main.py' -WorkingDirectory (Join-Path $projectRoot 'python_service') -WindowStyle Hidden -PassThru
    $process.Id | Set-Content -LiteralPath $pythonPidPath
}
Write-Output 'Prism: http://127.0.0.1:8088 (MariaDB on 127.0.0.1:3307 | Python Service Running)'



