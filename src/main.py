#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import tkinter as tk
from PriceTracker import PriceTrackerApp

# Configurazione logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("main")

def main():
    """Funzione principale che avvia l'applicazione"""
    root = tk.Tk()
    app = PriceTrackerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 