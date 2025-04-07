@echo off
echo Avvio dello strumento di migrazione dati per PriceTracker...
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

REM Esegui lo script di migrazione
python migrare_dati.py

echo.
pause 