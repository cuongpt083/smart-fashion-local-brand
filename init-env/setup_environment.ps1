# Setup Script for Smart Fashion Local Brand Dashboard & Synthetic Data Vault
# Target OS: Windows 10 / Windows 11 (PowerShell)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   SMART FASHION LOCAL BRAND - ENVIRONMENT SETUP SCRIPT     " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Check Execution Policy
Write-Host "`n[1/5] Kiểm tra Execution Policy..." -ForegroundColor Yellow
$currentPolicy = Get-ExecutionPolicy
if ($currentPolicy -eq "Restricted") {
    Write-Host "⚠️ ExecutionPolicy hiện tại là Restricted. Đang tạm thời chuyển sang RemoteSigned..." -ForegroundColor Warning
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force
}

# Helper function to check command existence
function Test-CommandExists {
    param ($Command)
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    $result = Get-Command $Command -ErrorAction SilentlyContinue
    $ErrorActionPreference = $oldPreference
    return $null -ne $result
}

# 2. Check & Install Python 3
Write-Host "`n[2/5] Kiểm tra Python 3..." -ForegroundColor Yellow
$pythonCmd = $null

if (Test-CommandExists "python") {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Đã tìm thấy Python: $pythonVersion" -ForegroundColor Green
    $pythonCmd = "python"
} elseif (Test-CommandExists "py") {
    $pythonVersion = py --version 2>&1
    Write-Host "✅ Đã tìm thấy Python Launcher (py): $pythonVersion" -ForegroundColor Green
    $pythonCmd = "py"
} else {
    Write-Host "❌ Python 3 chưa được cài đặt." -ForegroundColor Red
    if (Test-CommandExists "winget") {
        Write-Host "🚀 Đang tiến hành cài đặt Python 3.11 bằng Winget..." -ForegroundColor Cyan
        winget install -e --id Python.Python.3.11 --accept-source-agreements --accept-package-agreements
        # Refresh environment variables
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        $pythonCmd = "python"
    } else {
        Write-Host "⚠️ Vui lòng cài đặt Python 3 (3.10+) từ https://www.python.org/downloads/ sau đó chạy lại script này!" -ForegroundColor Red
        exit 1
    }
}

# 3. Check & Install NVM for Windows & Node.js LTS
Write-Host "`n[3/5] Kiểm tra NVM (Node Version Manager) & Node.js LTS..." -ForegroundColor Yellow

# Update PATH from current environment in case NVM was added recently
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

if (Test-CommandExists "nvm") {
    $nvmVer = nvm version 2>&1
    Write-Host "✅ Đã tìm thấy NVM for Windows (Version $nvmVer)" -ForegroundColor Green
} else {
    Write-Host "⚠️ Chưa tìm thấy NVM for Windows." -ForegroundColor Yellow
    if (Test-CommandExists "winget") {
        Write-Host "🚀 Đang cài đặt NVM for Windows thông qua Winget..." -ForegroundColor Cyan
        winget install -e --id CoreyButler.NVMforWindows --accept-source-agreements --accept-package-agreements
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    } else {
        Write-Host "⚠️ Vui lòng tải và cài đặt nvm-windows từ: https://github.com/coreybutler/nvm-windows/releases" -ForegroundColor Red
    }
}

if (Test-CommandExists "nvm") {
    Write-Host "🚀 Đang cài đặt & kích hoạt Node.js LTS bằng NVM..." -ForegroundColor Cyan
    try {
        nvm install lts
        nvm use lts
        $nodeVer = node --version 2>&1
        $npmVer = npm --version 2>&1
        Write-Host "✅ Node.js: $nodeVer | npm: $npmVer" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Lưu ý: Khi chạy 'nvm use lts' có thể cần mở PowerShell bằng quyền Administrator nếu gặp lỗi cấp quyền." -ForegroundColor Yellow
    }
} else {
    if (Test-CommandExists "node") {
        $nodeVer = node --version 2>&1
        Write-Host "✅ Node.js đã sẵn có (không dùng NVM): $nodeVer" -ForegroundColor Green
    }
}

# 4. Create Python Virtual Environment (.venv)
Write-Host "`n[4/5] Thiết lập Môi trường ảo Python (.venv)..." -ForegroundColor Yellow
$venvPath = Join-Path $PSScriptRoot ".venv"

if (Test-Path $venvPath) {
    Write-Host "ℹ️ Môi trường ảo .venv đã tồn tại." -ForegroundColor Cyan
} else {
    Write-Host "🚀 Đang tạo môi trường ảo Python tại .venv..." -ForegroundColor Cyan
    & $pythonCmd -m venv .venv
    Write-Host "✅ Tạo .venv thành công!" -ForegroundColor Green
}

$venvPython = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    # Fallback for unix style if running on Git Bash / WSL
    $venvPython = Join-Path $venvPath "bin/python"
}

# 5. Install Required Python Packages (SDV, Streamlit, Pandas, etc.)
Write-Host "`n[5/5] Cài đặt các thư viện Python (SDV, Streamlit, Pandas, Plotly...)..." -ForegroundColor Yellow
Write-Host "🚀 Đang nâng cấp pip..." -ForegroundColor Cyan
& $venvPython -m pip install --upgrade pip --quiet

$reqPath = Join-Path $PSScriptRoot "requirements.txt"
if (Test-Path $reqPath) {
    Write-Host "🚀 Đang cài đặt thư viện từ requirements.txt..." -ForegroundColor Cyan
    & $venvPython -m pip install -r $reqPath
    Write-Host "✅ Đã cài đặt xong tất cả thư viện cần thiết!" -ForegroundColor Green
} else {
    Write-Host "⚠️ Không tìm thấy requirements.txt, tiến hành cài đặt mặc định..." -ForegroundColor Yellow
    & $venvPython -m pip install streamlit sdv pandas numpy plotly openpyxl scikit-learn faker
}

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "   CÀI ĐẶT HOÀN TẤT! SẴN SÀNG LÀM VIỆC VỚI ANTIGRAVITY     " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "`nHướng dẫn bắt đầu:" -ForegroundColor Cyan
Write-Host " 1. Kích hoạt virtual environment trong PowerShell:" -ForegroundColor White
Write-Host "    .\.venv\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host " 2. Chạy ứng dụng Streamlit (khi có file app.py):" -ForegroundColor White
Write-Host "    streamlit run app.py" -ForegroundColor Yellow
Write-Host "============================================================`n" -ForegroundColor Green
