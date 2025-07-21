@echo off
REM Clean up all __pycache__ folders in the project using Powershell 7

pwsh -Command "Get-ChildItem -Path . -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force"

echo All __pycache__ folders have been