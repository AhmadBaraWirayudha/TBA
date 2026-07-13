@echo off
setlocal
if "%~1"=="" (
  echo Usage: validate_with_freecad_python.bat "C:\Program Files\FreeCAD 0.21\bin\python.exe"
  exit /b 2
)
set "FREECAD_PY=%~1"
if not exist "%FREECAD_PY%" (
  echo ERROR: Python executable not found: %FREECAD_PY%
  exit /b 2
)
pushd "%~dp0\.."
"%FREECAD_PY%" -m compileall -q .
if errorlevel 1 (
  echo ERROR: compileall failed.
  popd
  exit /b 1
)
"%FREECAD_PY%" -m unittest discover -s tests -v
set "RESULT=%ERRORLEVEL%"
popd
if not "%RESULT%"=="0" (
  echo ERROR: tests failed with exit code %RESULT%.
  exit /b %RESULT%
)
echo Static validation passed with: %FREECAD_PY%
exit /b 0
