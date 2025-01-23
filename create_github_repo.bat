@echo off
REM GitHub Repository Creation Wrapper

REM Change to project directory
cd /d C:\Users\ihelp\Knowledge_Library\iHelper.tech

REM Check if Git Bash exists
if not exist "C:\Program Files\Git\bin\bash.exe" (
    echo Error: Git Bash is not installed
    echo Please install Git for Windows from https://git-scm.com/download/win
    exit /b 1
)

REM Run bash script using Git Bash
"C:\Program Files\Git\bin\bash.exe" github_repo_create.sh

REM Check exit status
if %errorlevel% neq 0 (
    echo Repository creation failed
    exit /b %errorlevel%
)

echo Repository created successfully!
