@echo off
setlocal EnableDelayedExpansion
:: =============================================================================
:: NeuralForge Studio -- Windows Setup
:: Double-click or run from cmd: setup.bat
:: =============================================================================

set "SCRIPT_DIR=%~dp0"
:: Strip trailing backslash
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "VENV_DIR=%SCRIPT_DIR%\.venv"
set "LAUNCHER=%SCRIPT_DIR%\launch.bat"

echo.
echo   NeuralForge Studio -- Windows Setup
echo   ----------------------------------------
echo.

:: ── Python ───────────────────────────────────────────────────────────────────
echo [INFO]  Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERR]   Python not found.
    echo         Download from https://python.org
    echo         IMPORTANT: Check "Add Python to PATH" and "Install tcl/tk and IDLE"
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo [OK]    Found: %PY_VER%

:: ── tkinter ───────────────────────────────────────────────────────────────────
echo [INFO]  Checking tkinter...
python -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo [WARN]  tkinter not found.
    echo         Reinstall Python and tick "tcl/tk and IDLE" in Optional Features.
    pause
    exit /b 1
)
echo [OK]    tkinter available

:: ── Virtual environment ───────────────────────────────────────────────────────
if exist "%VENV_DIR%\" (
    echo [OK]    Virtual environment already exists
) else (
    echo [INFO]  Creating virtual environment...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERR]   Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK]    Created .venv
)

call "%VENV_DIR%\Scripts\activate.bat"

:: ── pip dependencies ──────────────────────────────────────────────────────────
echo [INFO]  Upgrading pip...
python -m pip install --quiet --upgrade pip

echo [INFO]  Installing core dependencies...
pip install --quiet requests
echo [OK]    Core dependencies installed

:: ── airllm (optional) ────────────────────────────────────────────────────────
echo.
set /p AIRLLM="Install airllm for quantized model loading? [y/N]: "
if /i "%AIRLLM%"=="y" (
    echo [INFO]  Installing airllm + PyTorch CPU...
    pip install --quiet airllm torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    if errorlevel 1 (
        echo [WARN]  airllm install failed. Ollama will still work fine.
    ) else (
        echo [OK]    airllm installed
    )
) else (
    echo [INFO]  Skipping airllm -- Ollama will be used for inference
)

:: ── Ollama ────────────────────────────────────────────────────────────────────
echo.
echo [INFO]  Checking Ollama...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo [WARN]  Ollama not found.
    set /p GET_OLLAMA="Open Ollama download page? [Y/n]: "
    if /i not "!GET_OLLAMA!"=="n" (
        start "" "https://ollama.com/download/windows"
        echo [INFO]  Install Ollama, then re-run this script.
        echo         After installing, also start the Ollama app before launching NeuralForge.
    )
) else (
    for /f "tokens=*" %%v in ('ollama --version 2^>^&1') do set OL_VER=%%v
    echo [OK]    Ollama found: !OL_VER!
)

:: ── Starter models ────────────────────────────────────────────────────────────
echo.
echo [INFO]  Recommended starter models:
echo         Agent:    ollama pull qwen2.5:7b
echo         Scripter: ollama pull qwen2.5-coder:7b
echo.
set /p PULL_MODELS="Pull these models now? [y/N]: "
if /i "%PULL_MODELS%"=="y" (
    ollama --version >nul 2>&1
    if errorlevel 1 (
        echo [WARN]  Ollama not available -- skipping model pull.
    ) else (
        echo [INFO]  Pulling qwen2.5:7b ...
        ollama pull qwen2.5:7b
        echo [INFO]  Pulling qwen2.5-coder:7b ...
        ollama pull qwen2.5-coder:7b
        echo [OK]    Models downloaded
    )
)

:: ── Create launch.bat ────────────────────────────────────────────────────────
echo.
echo [INFO]  Creating launcher...
(
    echo @echo off
    echo cd /d "%SCRIPT_DIR%"
    echo call .venv\Scripts\activate.bat
    echo python main.py %%*
) > "%LAUNCHER%"
echo [OK]    Launcher created: %LAUNCHER%

:: ── Done ─────────────────────────────────────────────────────────────────────
echo.
echo   ----------------------------------------
echo [OK]    Setup complete!
echo.
echo   To launch NeuralForge Studio:
echo     Double-click launch.bat
echo   Or from this folder in cmd:
echo     launch.bat
echo.
pause
endlocal