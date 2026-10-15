$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
foreach ($entry in @(@('server.pid', (Join-Path $projectRoot '.runtime\php\php.exe')), @('database.pid', 'D:\xampp\mysql\bin\mysqld.exe'), @('python.pid', 'python'))) {
    $pidPath = Join-Path $projectRoot ('.runtime\' + $entry[0])
    if (Test-Path -LiteralPath $pidPath) {
        $savedPid = [int](Get-Content -LiteralPath $pidPath)
        $process = Get-Process -Id $savedPid -ErrorAction SilentlyContinue
        if ($process -and ($process.Path -eq $entry[1] -or $process.Name -match "python")) {
            $details = Get-CimInstance Win32_Process -Filter "ProcessId=$savedPid"
            $belongs = if ($entry[0] -eq 'database.pid') { $details.CommandLine -match '[\\/]database[\\/]my\.ini' } elseif ($entry[0] -eq 'python.pid') { $details.CommandLine -match 'main\.py' } else { $details.CommandLine -match '127\.0\.0\.1:8088' }
            if ($belongs) {
                if ($entry[0] -eq 'database.pid') {
                    & 'D:\xampp\mysql\bin\mysqladmin.exe' "--defaults-extra-file=$projectRoot\.runtime\root-client.cnf" shutdown
                } else { Stop-Process -Id $savedPid }
            }
        }
    }
}
Write-Output 'Project services stopped.'

