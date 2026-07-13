@echo off
REM Launch the Coronal Aging spatial viewer (Windows).
REM Usage: run.bat [port] [--no-open]   (or just double-click)
cd /d "%~dp0"
where python >nul 2>nul && (
  python serve.py %*
) || (
  py -3 serve.py %*
)
pause
