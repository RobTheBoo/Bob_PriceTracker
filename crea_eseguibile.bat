@echo off
echo Avvio della creazione dell'eseguibile PriceTracker...
echo.

REM Verifica se Python è installato
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python non trovato nel sistema!
    echo Per favore installa Python 3.6 o superiore da: https://www.python.org/downloads/
    echo.
    echo Assicurati di selezionare l'opzione "Aggiungi Python al PATH" durante l'installazione.
    echo.
    pause
    exit /b 1
)

REM Esegui lo script di setup
python setup.py

echo.
if exist dist\PriceTracker.exe (
    echo Creazione completata! L'eseguibile si trova nella cartella 'dist'.
    echo.
    
    REM Chiedi se vuole creare un collegamento sul desktop
    set /p create_shortcut="Vuoi creare un collegamento sul desktop? (s/n): "
    if /i "%create_shortcut%"=="s" (
        echo Creazione collegamento sul desktop...
        powershell "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\PriceTracker.lnk'); $s.TargetPath = '%CD%\dist\PriceTracker.exe'; $s.Save()"
        echo Collegamento creato con successo!
    )
) else (
    echo C'è stato un problema nella creazione dell'eseguibile.
)

echo.
pause 