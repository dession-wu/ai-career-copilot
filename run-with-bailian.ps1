param([string]$Python = "E:\podnotes\podnotes-server\.venv\Scripts\python.exe", [int]$Port = 8000)
$ErrorActionPreference = 'Stop'
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell.exe -Verb RunAs -WindowStyle Hidden -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"'+$PSCommandPath+'"'),'-Python',('"'+$Python+'"'),'-Port',$Port)
    exit
}
$env:BAILIAN_API_KEY_FILE = 'E:\podnotes\podnotes-server\config\ops-secrets\bailian-secret.bin'
if (-not (Test-Path -LiteralPath $env:BAILIAN_API_KEY_FILE)) { throw '请先通过统一运营密钥输入窗口配置百炼。' }
Set-Location -LiteralPath (Join-Path $PSScriptRoot 'backend')
if (-not $env:MODEL_DATA_DIR) { $env:MODEL_DATA_DIR = Join-Path $PSScriptRoot 'private-model-data' }
& $Python -m uvicorn app.main:app --host 127.0.0.1 --port $Port
