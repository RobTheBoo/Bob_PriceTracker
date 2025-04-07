#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import platform
import shutil
import PyInstaller.__main__

def check_python():
    """Verifica che Python sia installato e nella versione corretta"""
    try:
        python_version = platform.python_version()
        major, minor, _ = map(int, python_version.split('.'))
        
        if major >= 3 and minor >= 6:
            print(f"✓ Python {python_version} trovato (versione compatibile)")
            return True
        else:
            print(f"✗ Python {python_version} trovato, ma è richiesto Python 3.6+")
            return False
    except Exception:
        print("✗ Python non trovato nel sistema o non è accessibile")
        return False

def install_requirements():
    """Installa i requisiti dal file requirements.txt"""
    print("\nInstallazione dei requisiti...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Requisiti installati con successo")
        return True
    except subprocess.CalledProcessError:
        print("✗ Errore durante l'installazione dei requisiti")
        return False

def create_executable():
    """Crea l'eseguibile dell'applicazione"""
    # Percorsi delle directory
    src_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(src_dir, "dist")
    data_dir = os.path.join(dist_dir, "data")
    icon_path = os.path.join(src_dir, "src", "assets", "icon.ico")
    
    # Assicurati che la directory dist esista
    os.makedirs(dist_dir, exist_ok=True)
    
    # Crea la directory data se non esiste
    os.makedirs(data_dir, exist_ok=True)
    
    # Opzioni per PyInstaller
    options = [
        "src/PriceTracker.py",  # Percorso corretto del file principale
        "--name=PriceTracker",
        "--onefile",
        "--windowed",
        "--add-data=dist/data;data",  # Usa la cartella data da dist
        "--clean"
    ]
    
    # Aggiungi l'icona solo se esiste
    if os.path.exists(icon_path):
        options.append(f"--icon={icon_path}")
    
    # Esegui PyInstaller
    PyInstaller.__main__.run(options)
    
    print("\nEseguibile creato con successo!")
    print(f"I dati verranno salvati nella cartella 'data' accanto all'eseguibile.")

def main():
    """Funzione principale"""
    print("=== Setup Price Tracker ===\n")
    
    # Verifica Python
    if not check_python():
        print("\nPer favore installa Python 3.6 o superiore da: https://www.python.org/downloads/")
        input("\nPremi INVIO per uscire...")
        return
    
    # Installa requisiti
    if not install_requirements():
        print("\nImpossibile continuare senza installare i requisiti")
        input("\nPremi INVIO per uscire...")
        return
    
    # Crea eseguibile
    create_executable()
    
    input("\nSetup completato. Premi INVIO per uscire...")

if __name__ == "__main__":
    main() 