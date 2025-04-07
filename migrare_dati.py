#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import json
import tkinter as tk
from tkinter import filedialog, messagebox

def migrate_data():
    """
    Migra i dati da una vecchia installazione alla nuova struttura
    """
    root = tk.Tk()
    root.withdraw()  # Nascondi la finestra principale
    
    # Chiedi all'utente di selezionare il file properties.json esistente
    messagebox.showinfo("Migrazione Dati", 
                        "Seleziona il file 'properties.json' dalla tua vecchia installazione.\n"
                        "Questo è il file che contiene i tuoi dati salvati.")
    
    src_file = filedialog.askopenfilename(
        title="Seleziona il file properties.json esistente",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )
    
    if not src_file or not os.path.exists(src_file):
        messagebox.showerror("Errore", "Nessun file selezionato o file non valido.")
        return False
    
    # Chiedi all'utente di selezionare l'eseguibile PriceTracker.exe
    messagebox.showinfo("Migrazione Dati", 
                        "Ora seleziona l'eseguibile 'PriceTracker.exe'.\n"
                        "I dati verranno migrati nella cartella corretta.")
    
    exe_file = filedialog.askopenfilename(
        title="Seleziona l'eseguibile PriceTracker.exe",
        filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
    )
    
    if not exe_file or not os.path.exists(exe_file):
        messagebox.showerror("Errore", "Nessun eseguibile selezionato o file non valido.")
        return False
    
    # Crea la cartella data nella directory dell'eseguibile
    exe_dir = os.path.dirname(exe_file)
    data_dir = os.path.join(exe_dir, "data")
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Copia il file properties.json nella cartella data
    dst_file = os.path.join(data_dir, "properties.json")
    
    try:
        # Leggi il file sorgente per verificare che sia un file JSON valido
        with open(src_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Copia il file
        shutil.copy2(src_file, dst_file)
        
        messagebox.showinfo("Successo", 
                            f"Migrazione completata con successo!\n\n"
                            f"I tuoi dati sono stati copiati in:\n"
                            f"{dst_file}\n\n"
                            f"Ora puoi avviare l'eseguibile e i tuoi dati saranno disponibili.")
        return True
        
    except json.JSONDecodeError:
        messagebox.showerror("Errore", "Il file selezionato non è un file JSON valido.")
        return False
    except Exception as e:
        messagebox.showerror("Errore", f"Si è verificato un errore durante la migrazione:\n{e}")
        return False

def main():
    """Funzione principale"""
    print("=== Migrazione Dati PriceTracker ===")
    print("\nQuesto strumento ti aiuterà a migrare i dati da una vecchia installazione")
    print("alla nuova struttura utilizzata dall'eseguibile.\n")
    
    migrate_data()
    
if __name__ == "__main__":
    main() 