@echo off
REM Set variables
set "PYTHON_PATH=C:\Users\Administrator\AppData\Local\Programs\Python\Python313\python.exe"
set "SERVICE_NAME=FastApiService"
set "APP_MODULE=main:app"
set "APP_DIR=C:\Program Files\Apache24\htdocs\BIOMETRIC-DATA-SCHEDULAR"
set "NSSM_PATH=nssm"
set "LOG_FILE=%~dp0FastApiService.log"

REM Check if service already exists
sc query "%SERVICE_NAME%" >nul 2>&1
if %errorlevel% neq 0 (
    REM Service does not exist, so install it
    echo [%date% %time%] Installing %SERVICE_NAME% >> "%LOG_FILE%"
    "%NSSM_PATH%" install %SERVICE_NAME% "%PYTHON_PATH%" >> "%LOG_FILE%" 2>&1
    "%NSSM_PATH%" set %SERVICE_NAME% AppParameters "-m uvicorn %APP_MODULE% --host 0.0.0.0 --port 9000" >> "%LOG_FILE%" 2>&1
    "%NSSM_PATH%" set %SERVICE_NAME% AppDirectory "%APP_DIR%" >> "%LOG_FILE%" 2>&1
    "%NSSM_PATH%" set %SERVICE_NAME% AppStdout "%~dp0FastApiService_stdout.log" >> "%LOG_FILE%" 2>&1
    "%NSSM_PATH%" set %SERVICE_NAME% AppStderr "%~dp0FastApiService_stderr.log" >> "%LOG_FILE%" 2>&1
    "%NSSM_PATH%" set %SERVICE_NAME% AppNoConsole 1 >> "%LOG_FILE%" 2>&1
)

REM Check service status
sc query "%SERVICE_NAME%" | findstr /I "RUNNING START_PENDING" >nul
if %errorlevel%==0 (
    REM Service is running or starting, so restart it
    "%NSSM_PATH%" restart %SERVICE_NAME% >> "%LOG_FILE%" 2>&1
    if %errorlevel% neq 0 (
        echo [%date% %time%] ERROR: Failed to restart service %SERVICE_NAME%. >> "%LOG_FILE%"
        sc query "%SERVICE_NAME%" >> "%LOG_FILE%" 2>&1
    ) else (
        echo [%date% %time%] Restarted %SERVICE_NAME% successfully. >> "%LOG_FILE%"
    )
) else (
    REM Service is not running, so start it
    "%NSSM_PATH%" start %SERVICE_NAME% >> "%LOG_FILE%" 2>&1
    if %errorlevel% neq 0 (
        echo [%date% %time%] ERROR: Failed to start service %SERVICE_NAME%. >> "%LOG_FILE%"
        sc query "%SERVICE_NAME%" >> "%LOG_FILE%" 2>&1
    ) else (
        echo [%date% %time%] Started %SERVICE_NAME% successfully. >> "%LOG_FILE%"
    )
)

REM Check if service is paused
sc query "%SERVICE_NAME%" | findstr /I "PAUSED" >nul
if %errorlevel%==0 (
    echo [%date% %time%] WARNING: Service %SERVICE_NAME% is PAUSED. >> "%LOG_FILE%"
    sc query "%SERVICE_NAME%" >> "%LOG_FILE%" 2>&1
)
