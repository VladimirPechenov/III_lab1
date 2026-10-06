# Запуск двух локальных сервисов из любой папки. Окна процессов скрыты, вывод записывается в logs.
$projectRoot = Split-Path $PSScriptRoot -Parent
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Сначала создайте .venv и установите requirements.txt по инструкции README.'
}
$logsPath = Join-Path $projectRoot '.venv\logs'
New-Item -ItemType Directory -Force -Path $logsPath | Out-Null
foreach ($service in @(
    @{ Name='server'; Port=8000; Args='-m uvicorn server.app:app --host 127.0.0.1 --port 8000' },
    @{ Name='dashboard'; Port=8501; Args='-m streamlit run dashboard/app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true --browser.gatherUsageStats false' }
)) {
    if (Get-NetTCPConnection -State Listen -LocalPort $service.Port -ErrorAction SilentlyContinue) {
        Write-Host "Порт $($service.Port) уже занят; проверьте запущенный сервис."
        continue
    }
    $process = Start-Process -FilePath $pythonPath -ArgumentList $service.Args -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $logsPath "$($service.Name).out.log") `
        -RedirectStandardError (Join-Path $logsPath "$($service.Name).err.log")
    Write-Host "$($service.Name): PID $($process.Id)"
}
Write-Host 'Сервер: http://127.0.0.1:8000/docs'
Write-Host 'Дашборд: http://127.0.0.1:8501'
# Остановка по указанному PID: Stop-Process -Id <PID>.
