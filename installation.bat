@echo off
echo Installation des dependances pour le systeme de localisation UWB
echo =============================================================

echo Verification de Python...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo Python n'est pas installe ou n'est pas dans le PATH.
    echo Veuillez installer Python 3.7 ou superieur.
    pause
    exit /b 1
)

echo Creation des dossiers necessaires...
if not exist static mkdir static
if not exist templates mkdir templates

echo Installation des dependances Python...
pip install flask qrcode[pil]

echo Verifiez que le fichier server.py et le template index.html sont presents dans les bons dossiers.
echo Pour demarrer le systeme, lancez votre script Python principal.

echo Installation terminee.
pause