#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import platform
import shutil

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
    """Crea l'eseguibile usando PyInstaller"""
    print("\nCreazione dell'eseguibile...")
    try:
        # Determina il separatore corretto per --add-data in base al sistema operativo
        # Su Windows è ";" mentre su Unix è ":"
        separator = ";" if platform.system() == "Windows" else ":"
        
        # Assicurati che il percorso src esista
        if not os.path.exists("src"):
            print("✗ La directory 'src' non esiste")
            return False
            
        # Opzione per l'icona, se esiste
        icon_option = []
        if os.path.exists("src/icon.ico"):
            icon_option = ["--icon=src/icon.ico"]
            
        # Comando PyInstaller
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--name=PriceTracker",
            "--onefile",
            "--windowed",  # Senza console
            f"--add-data=src{separator}src"  # Formato corretto per Windows (;) o Unix (:)
        ]
        
        # Aggiungi la cartella data se esiste
        data_dir = os.path.join("src", "data")
        if os.path.exists(data_dir):
            # Includi la directory dei dati
            cmd.append(f"--add-data={data_dir}{separator}data")
            print("✓ Directory 'data' trovata e verrà inclusa nell'eseguibile")
        else:
            print("! Directory 'data' non trovata. I dati verranno creati nella stessa cartella dell'eseguibile.")
        
        # Aggiungi l'opzione dell'icona se esiste
        if icon_option:
            cmd.extend(icon_option)
            
        # Aggiungi il file principale
        cmd.append("src/main.py")
        
        # Esegui il comando
        subprocess.check_call(cmd)
        
        # Copia la directory dei dati nella cartella dist se esiste
        if os.path.exists(data_dir):
            dist_data_dir = os.path.join("dist", "data")
            if not os.path.exists(dist_data_dir):
                os.makedirs(dist_data_dir)
            
            # Copia i files dalla directory dei dati
            for file in os.listdir(data_dir):
                src_file = os.path.join(data_dir, file)
                dst_file = os.path.join(dist_data_dir, file)
                if os.path.isfile(src_file):
                    shutil.copy2(src_file, dst_file)
                    print(f"✓ File '{file}' copiato nella directory 'dist/data'")
        
        print("✓ Eseguibile creato con successo!")
        print("\nPuoi trovare l'eseguibile nella cartella 'dist'")
        print("NOTA: I tuoi dati verranno salvati nella cartella 'data' nella stessa directory dell'eseguibile.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Errore durante la creazione dell'eseguibile: {e}")
        return False

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