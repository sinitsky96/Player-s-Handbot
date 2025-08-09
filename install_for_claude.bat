@echo off
setlocal

REM Check if python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python not found. Checking for winget...

    winget --version >nul 2>&1
    if NOT %ERRORLEVEL% EQU 0 (
        echo ERROR: winget is not available.
        goto manual_install
    )

    echo Installing Python 3.12 using winget...
    winget install Python.Python.3.12 --accept-source-agreements --accept-package-agreements

    if NOT %ERRORLEVEL% EQU 0 (
        echo ERROR: winget install failed.
        goto manual_install
    )

    echo Python installation completed!
    echo Waiting for environment to update...
    timeout /t 5 >nul
)

REM Run Python script to update Claude config
echo Running Python script to update Claude Desktop configuration...
python update_claude_config.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to update Claude configuration.
    pause
    exit /b 1
)

REM Restart Claude Desktop
echo Restarting Claude Desktop...

REM Kill Claude process if running
tasklist /FI "IMAGENAME eq Claude.exe" 2>NUL | find /I /N "Claude.exe" >NUL
if "%ERRORLEVEL%"=="0" (
    echo Stopping Claude Desktop...
    taskkill /IM Claude.exe /F
    timeout /t 3 >nul
) else (
    echo Claude Desktop not running.
)

REM Start Claude Desktop
set "CLAUDE_PATH=%APPDATA%\Claude\Claude.exe"
if exist "%CLAUDE_PATH%" (
    echo Starting Claude Desktop...
    start "" "%CLAUDE_PATH%"
) else (
    echo WARNING: Claude Desktop executable not found at %CLAUDE_PATH%
)

echo Setup complete!
pause
exit /b 0

:manual_install
echo.
echo Please install Python manually:
echo 1. Go to https://www.python.org/downloads/
echo 2. Download Python 3.8 or newer
echo 3. Run the installer and make sure to check "Add Python to PATH"
echo 4. Restart this script after installation
pause
exit /b 1
