@echo off
set NODE_EXE=C:\Program Files\WindowsApps\OpenAI.Codex_26.415.4716.0_x64__2p2nqsd0c76g0\app\resources\node.exe

if not exist "%NODE_EXE%" (
  echo No encontre node en:
  echo %NODE_EXE%
  pause
  exit /b 1
)

echo Iniciando piloto en http://127.0.0.1:4173
"%NODE_EXE%" "%~dp0server.js"
pause
