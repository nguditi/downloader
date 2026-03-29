@echo off
REM Quick push script for ClipNest MVP to GitHub

echo ClipNest MVP - GitHub Push Script
echo ====================================
echo.

if "%1"=="" (
    echo Usage: %0 ^<github_url^>
    echo Example: %0 https://github.com/your-username/clipnest.git
    echo Or: %0 git@github.com:your-username/clipnest.git
    exit /b 1
)

set REPO_URL=%1

echo Configuring git remote to: %REPO_URL%
git remote set-url origin %REPO_URL%

echo Pushing to GitHub on 'master' branch...
git push -u origin master

if %ERRORLEVEL% equ 0 (
    echo.
    echo Push successful!
    echo Repository URL: %REPO_URL%
    echo Branch: master
) else (
    echo.
    echo Push failed. Check credentials and repository URL.
    exit /b 1
)
