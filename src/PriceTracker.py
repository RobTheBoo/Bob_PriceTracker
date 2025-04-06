#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
import threading
import os
import re
import json
import logging
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageTk, ImageDraw
from io import BytesIO
import pandas as pd  # Aggiungi pandas per il supporto Excel

# Importa il modulo di estrazione prezzi
from extract_price import extract_price, extract_price_from_html

# Configurazione logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("price_tracker")

# Directory per i dati
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# File di configurazione
PROPERTIES_FILE = os.path.join(DATA_DIR, "properties.json")

class Property:
    def __init__(self, url="", title="", price=0, last_checked=None):
        self.url = url
        self.title = title
        self.price = price
        self.price_history = []
        self.rating = 0  # 0=non valutato, 1=non mi piace, 2=neutro, 3=mi piace
        self.alternate_price = 0  # Prezzo alternativo/erroneo
        self.notes = ""  # Note libere
        self.image_url = ""  # URL dell'immagine dell'immobile
        
        if price > 0:
            self.add_price_point(price, last_checked)
    
    def add_price_point(self, price, timestamp=None):
        if not timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.price = price
        self.price_history.append({
            "price": price,
            "date": timestamp
        })
    
    def to_dict(self):
        return {
            "url": self.url,
            "title": self.title,
            "price": self.price,
            "price_history": self.price_history,
            "rating": self.rating,
            "alternate_price": self.alternate_price,
            "notes": self.notes,
            "image_url": self.image_url
        }
    
    @classmethod
    def from_dict(cls, data):
        prop = cls(data.get("url", ""), data.get("title", ""), data.get("price", 0))
        prop.price_history = data.get("price_history", [])
        prop.rating = data.get("rating", 0)
        prop.alternate_price = data.get("alternate_price", 0)
        prop.notes = data.get("notes", "")
        prop.image_url = data.get("image_url", "")
        return prop
    
    def get_price_change(self):
        """Calcola la variazione di prezzo dall'inizio del monitoraggio"""
        if len(self.price_history) <= 1:
            return 0, 0  # Nessuna variazione
        
        first_price = self.price_history[0]["price"]
        last_price = self.price_history[-1]["price"]
        
        diff = last_price - first_price
        percent = (diff / first_price) * 100 if first_price > 0 else 0
        
        return diff, percent

class PriceTracker:
    def __init__(self):
        self.properties = []
        self.load_properties()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"
        }
    
    def load_properties(self):
        """Carica le proprietà dal file"""
        if os.path.exists(PROPERTIES_FILE):
            try:
                with open(PROPERTIES_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.properties = [Property.from_dict(item) for item in data]
                    logger.info(f"Caricate {len(self.properties)} proprietà")
            except Exception as e:
                logger.error(f"Errore nel caricamento delle proprietà: {e}")
                self.properties = []
        else:
            self.properties = []
    
    def save_properties(self):
        """Salva le proprietà nel file"""
        try:
            with open(PROPERTIES_FILE, 'w', encoding='utf-8') as f:
                data = [prop.to_dict() for prop in self.properties]
                json.dump(data, f, indent=4)
            logger.info(f"Salvate {len(self.properties)} proprietà")
        except Exception as e:
            logger.error(f"Errore nel salvataggio delle proprietà: {e}")
    
    def add_property(self, url):
        """Aggiunge una nuova proprietà da monitorare"""
        # Verifica se l'URL è già monitorato
        for prop in self.properties:
            if prop.url == url:
                logger.warning(f"La proprietà {url} è già monitorata")
                return None
        
        # Estrai le informazioni dalla pagina
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Estrai il titolo
            title_tag = soup.select_one("h1") or soup.select_one("title")
            title = title_tag.text.strip() if title_tag else "Immobile"
            
            # Estrai il prezzo
            price = extract_price_from_html(response.text)
            if price == 0:
                # Prova con il testo visibile
                visible_text = soup.get_text()
                price = extract_price(visible_text)
            
            # Cerca l'immagine principale dell'immobile
            image_url = ""
            img_tags = soup.select("img.bigImg") or soup.select("img.mainImg") or soup.select(".gallery img") or soup.select(".carousel img")
            if img_tags:
                for img in img_tags:
                    if img.has_attr("src") and (img["src"].endswith(".jpg") or img["src"].endswith(".png")):
                        image_url = img["src"]
                        if not image_url.startswith("http"):
                            # Converti URL relativi in assoluti
                            if image_url.startswith("//"):
                                image_url = "https:" + image_url
                            else:
                                base_url = "/".join(url.split("/")[:3])
                                image_url = base_url + ("" if image_url.startswith("/") else "/") + image_url
                        break
            
            # Crea la nuova proprietà
            prop = Property(url, title, price)
            prop.image_url = image_url
            self.properties.append(prop)
            self.save_properties()
            
            logger.info(f"Aggiunta nuova proprietà: {title} - {price}€")
            return prop
            
        except Exception as e:
            logger.error(f"Errore nell'aggiunta della proprietà {url}: {e}")
            return None
    
    def remove_property(self, index):
        """Rimuove una proprietà dal monitoraggio"""
        if 0 <= index < len(self.properties):
            removed = self.properties.pop(index)
            self.save_properties()
            logger.info(f"Rimossa proprietà: {removed.title}")
            return True
        return False
    
    def update_property(self, index):
        """Aggiorna il prezzo di una proprietà specifica"""
        if 0 <= index < len(self.properties):
            prop = self.properties[index]
            
            try:
                response = requests.get(prop.url, headers=self.headers, timeout=30)
                response.raise_for_status()
                
                # Estrai il prezzo
                price = extract_price_from_html(response.text)
                if price == 0:
                    # Prova con il testo visibile
                    soup = BeautifulSoup(response.text, "html.parser")
                    visible_text = soup.get_text()
                    price = extract_price(visible_text)
                
                # Se il prezzo è cambiato, registra il nuovo punto
                if price > 0 and price != prop.price:
                    prop.add_price_point(price)
                    self.save_properties()
                    logger.info(f"Aggiornato prezzo per {prop.title}: {price}€")
                
                return price
                
            except Exception as e:
                logger.error(f"Errore nell'aggiornamento della proprietà {prop.url}: {e}")
                return 0
        
        return 0
    
    def update_all_properties(self):
        """Aggiorna i prezzi di tutte le proprietà"""
        updated_count = 0
        price_changes = 0
        
        for i in range(len(self.properties)):
            price = self.update_property(i)
            if price > 0:
                updated_count += 1
                if price != self.properties[i].price:
                    price_changes += 1
        
        logger.info(f"Aggiornate {updated_count} proprietà, {price_changes} cambi di prezzo")
        return updated_count, price_changes

class PriceTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tracker Prezzi Immobili")
        self.root.geometry("1200x800")
        self.root.minsize(1200, 800)
        
        # Impostazione dei colori (tema chiaro)
        self.bg_color = "#FFFFFF"  # Bianco
        self.text_color = "#000000"  # Nero
        self.accent_color = "#4CAF50"  # Verde
        self.secondary_color = "#E0E0E0"  # Grigio chiaro
        self.highlight_color = "#2196F3"  # Blu
        self.link_color = "#006dcc"  # Blu dei link di Idealista
        self.price_color = "#e63900"  # Arancione dei prezzi di Idealista
        
        # Applicazione del tema chiaro
        self.root.configure(bg=self.bg_color)
        
        # Crea il tracker
        self.tracker = PriceTracker()
        self.update_thread = None
        
        # Crea l'interfaccia grafica
        self.create_widgets()
        
        # Aggiornamento iniziale della lista
        self.update_property_list()
        
        # Aggiungi un gestore per l'evento di chiusura
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Riferimento al popup immagine
        self.image_popup = None
        
        # Immagine per l'icona
        self.image_icon = None
        self.load_icon()
    
    def load_icon(self):
        """Carica l'icona per la visualizzazione immagine"""
        try:
            # Crea un'icona generica con un rettangolo e una lente
            icon_size = 16
            img = Image.new('RGBA', (icon_size, icon_size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Disegna un rettangolo per rappresentare un'immagine
            draw.rectangle([(2, 2), (icon_size-3, icon_size-3)], outline="gray", width=1)
            
            # Disegna una lente d'ingrandimento stilizzata
            draw.arc([(6, 6), (12, 12)], 0, 360, fill="gray", width=1)
            draw.line([(11, 11), (14, 14)], fill="gray", width=1)
            
            # Converti in formato Tkinter
            self.image_icon = ImageTk.PhotoImage(img)
        except Exception as e:
            logger.error(f"Errore nel caricamento dell'icona: {e}")
            self.image_icon = None
    
    def create_widgets(self):
        """Crea i widget dell'interfaccia grafica"""
        # Frame principale
        self.main_frame = tk.Frame(self.root, bg=self.bg_color)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Notebook per le schede
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scheda principale
        self.main_tab = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(self.main_tab, text="Lista Immobili")
        
        # Scheda per importazione multipla
        self.import_tab = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(self.import_tab, text="Importa URL")
        
        # Crea i widget per la scheda principale
        self.create_main_tab_widgets()
        
        # Crea i widget per la scheda di importazione
        self.create_import_tab_widgets()
        
        # Barra di stato
        self.status_frame = tk.Frame(self.root, bg=self.bg_color)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
        
        self.status_label = tk.Label(self.status_frame, text="Pronto", bg=self.bg_color, fg=self.text_color)
        self.status_label.pack(side=tk.LEFT)
        
        self.count_label = tk.Label(self.status_frame, text="Immobili: 0", bg=self.bg_color, fg=self.text_color)
        self.count_label.pack(side=tk.RIGHT)
    
    def create_main_tab_widgets(self):
        """Crea i widget per la scheda principale"""
        # Frame superiore per l'inserimento URL
        self.url_frame = tk.LabelFrame(self.main_tab, text="Aggiungi Immobile", bg=self.bg_color, fg=self.text_color)
        self.url_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.url_label = tk.Label(self.url_frame, text="URL Immobile:", bg=self.bg_color, fg=self.text_color)
        self.url_label.grid(row=0, column=0, padx=5, pady=5)
        
        self.url_var = tk.StringVar()
        self.url_entry = tk.Entry(self.url_frame, textvariable=self.url_var, width=60)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5)
        
        self.add_btn = tk.Button(self.url_frame, text="Aggiungi", 
                              command=self.add_property,
                              bg=self.accent_color, fg="white",
                              activebackground=self.highlight_color)
        self.add_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Frame centrale per la lista delle proprietà
        self.properties_frame = tk.LabelFrame(self.main_tab, text="Immobili Monitorati", bg=self.bg_color, fg=self.text_color)
        self.properties_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Creare il treeview per la lista delle proprietà
        self.columns = ("title", "price", "change", "rating", "alt_price", "last_update", "image")
        self.tree = ttk.Treeview(self.properties_frame, columns=self.columns, show="headings")
        
        # Configurare le colonne
        self.tree.heading("title", text="Titolo")
        self.tree.heading("price", text="Prezzo")
        self.tree.heading("change", text="Variazione")
        self.tree.heading("rating", text="Gradimento")
        self.tree.heading("alt_price", text="Prezzo Alt.")
        self.tree.heading("last_update", text="Ultimo Aggiornamento")
        self.tree.heading("image", text="Azioni")  # Cambiato da "URL" a "Azioni"
        
        # Configurare l'aspetto delle colonne
        style = ttk.Style()
        style.configure("Treeview", font=('Helvetica', 10), rowheight=30)
        style.configure("Treeview.Heading", font=('Helvetica', 10, 'bold'))
        
        # Configurare i colori delle righe alternate
        style.map('Treeview', 
                background=[('selected', '#e8f4f8')],
                foreground=[('selected', '#000000')])
        
        # Colori personalizzati per i tag
        self.tree.tag_configure("link", foreground=self.link_color)
        self.tree.tag_configure("even_row", background="#FFFFFF")
        self.tree.tag_configure("odd_row", background="#F9F9F9")
        
        self.tree.column("title", width=350)  # Allargata per mostrare titoli più lunghi
        self.tree.column("price", width=80)
        self.tree.column("change", width=100)
        self.tree.column("rating", width=80)
        self.tree.column("alt_price", width=80)
        self.tree.column("last_update", width=150)
        self.tree.column("image", width=70, anchor="center")  # Allargata per mostrare più azioni
        
        # Aggiungere una scrollbar
        self.scrollbar = tk.Scrollbar(self.properties_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=self.scrollbar.set)
        
        # Posizionare treeview e scrollbar
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Aggiungere il binding per la selezione e doppio clic
        self.tree.bind("<<TreeviewSelect>>", self.on_property_select)
        self.tree.bind("<Double-1>", self.on_property_double_click)
        self.tree.bind("<Button-3>", self.show_context_menu)  # Click destro
        self.tree.bind("<Button-1>", self.on_tree_click)      # Click singolo
        
        # Binding per il passaggio del mouse sulla tabella
        self.tree.bind("<Motion>", self.on_tree_motion)
        self.tree.bind("<Leave>", self.on_tree_leave)
        
        # Assicurati che tutta la riga sia cliccabile
        self.tree.bind("<Button-1>", self.on_tree_click)
        
        # Frame inferiore per i bottoni di azione
        self.actions_frame = tk.Frame(self.main_tab, bg=self.bg_color)
        self.actions_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.update_btn = tk.Button(self.actions_frame, text="Aggiorna Tutti", 
                                 command=self.update_all_properties,
                                 bg=self.accent_color, fg="white",
                                 activebackground=self.highlight_color)
        self.update_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.remove_btn = tk.Button(self.actions_frame, text="Rimuovi", 
                                 command=self.remove_selected_property,
                                 bg=self.secondary_color, fg=self.text_color,
                                 activebackground="#CCCCCC")
        self.remove_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Frame per i log
        self.log_frame = tk.LabelFrame(self.main_tab, text="Log", bg=self.bg_color, fg=self.text_color)
        self.log_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=5, wrap=tk.WORD,
                                               bg="white", fg="black")
        self.log_text.pack(fill=tk.X, padx=5, pady=5)
        self.log_text.config(state=tk.DISABLED)
        
        # Configura un handler per reindirizzare i log al widget
        self.log_handler = TextHandler(self.log_text)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.log_handler.setFormatter(formatter)
        
        # Aggiungi l'handler al logger di price_tracker
        logger.addHandler(self.log_handler)
        
        # Frame per le note
        self.details_frame = tk.LabelFrame(self.main_tab, text="Dettagli Immobile", bg=self.bg_color, fg=self.text_color)
        self.details_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Frame per i campi superiori
        self.details_top_frame = tk.Frame(self.details_frame, bg=self.bg_color)
        self.details_top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Gradimento
        self.rating_label = tk.Label(self.details_top_frame, text="Gradimento:", bg=self.bg_color, fg=self.text_color)
        self.rating_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.rating_var = tk.StringVar(value="Non valutato")
        self.rating_options = ["Non valutato", "Non mi piace", "Neutro", "Mi piace"]
        self.rating_colors = ["gray", "red", "yellow", "green"]
        
        self.rating_menu = tk.OptionMenu(self.details_top_frame, self.rating_var, *self.rating_options, command=self.update_rating)
        self.rating_menu.config(bg=self.bg_color, activebackground=self.accent_color)
        self.rating_menu.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Semaforo di gradimento
        self.rating_indicator = tk.Canvas(self.details_top_frame, width=20, height=20, bg=self.bg_color, highlightthickness=0)
        self.rating_indicator.grid(row=0, column=2, padx=5, pady=5)
        self.rating_indicator.create_oval(2, 2, 18, 18, fill="gray", outline="black")
        
        # Prezzo alternativo
        self.alt_price_label = tk.Label(self.details_top_frame, text="Prezzo Erroneo:", bg=self.bg_color, fg=self.text_color)
        self.alt_price_label.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        self.alt_price_var = tk.StringVar()
        self.alt_price_entry = tk.Entry(self.details_top_frame, textvariable=self.alt_price_var, width=12)
        self.alt_price_entry.grid(row=0, column=4, padx=5, pady=5, sticky="w")
        
        self.alt_price_save = tk.Button(self.details_top_frame, text="Salva", bg=self.accent_color, fg="white",
                                     command=self.save_alternate_price)
        self.alt_price_save.grid(row=0, column=5, padx=5, pady=5)
        
        # Note
        self.notes_label = tk.Label(self.details_frame, text="Note:", bg=self.bg_color, fg=self.text_color)
        self.notes_label.pack(anchor="w", padx=5)
        
        self.notes_text = scrolledtext.ScrolledText(self.details_frame, height=3, wrap=tk.WORD, bg="white", fg="black")
        self.notes_text.pack(fill=tk.X, padx=5, pady=5)
        
        self.notes_save = tk.Button(self.details_frame, text="Salva Note", bg=self.accent_color, fg="white",
                                 command=self.save_notes)
        self.notes_save.pack(anchor="e", padx=5, pady=5)
        
        # Disabilita inizialmente i controlli dei dettagli
        self.disable_details_controls()
        
        # Disabilita inizialmente i pulsanti di aggiornamento e rimozione
        self.remove_btn.config(state=tk.DISABLED)
    
    def create_import_tab_widgets(self):
        """Crea i widget per la scheda di importazione multipla"""
        # Frame per il caricamento da Excel
        self.excel_frame = tk.LabelFrame(self.import_tab, text="Importa da File Excel", bg=self.bg_color, fg=self.text_color)
        self.excel_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.excel_info_label = tk.Label(self.excel_frame, 
                                   text="Seleziona un file Excel (.xlsx) contenente gli URL degli immobili. L'applicazione leggerà la prima colonna del foglio attivo.",
                                   bg=self.bg_color, fg=self.text_color, wraplength=600, justify=tk.LEFT)
        self.excel_info_label.pack(anchor="w", padx=5, pady=5)
        
        self.excel_file_frame = tk.Frame(self.excel_frame, bg=self.bg_color)
        self.excel_file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.excel_path_var = tk.StringVar()
        self.excel_path_entry = tk.Entry(self.excel_file_frame, textvariable=self.excel_path_var, width=60)
        self.excel_path_entry.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.browse_btn = tk.Button(self.excel_file_frame, text="Sfoglia...", 
                                 command=self.browse_excel_file,
                                 bg=self.secondary_color, fg=self.text_color)
        self.browse_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.import_excel_btn = tk.Button(self.excel_file_frame, text="Importa da Excel", 
                                     command=self.import_from_excel,
                                     bg=self.accent_color, fg="white")
        self.import_excel_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Frame per l'inserimento manuale di più URL
        self.multi_url_frame = tk.LabelFrame(self.import_tab, text="Inserimento Manuale", bg=self.bg_color, fg=self.text_color)
        self.multi_url_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.multi_url_info_label = tk.Label(self.multi_url_frame, 
                                         text="Inserisci qui gli URL degli immobili (un URL per riga)",
                                         bg=self.bg_color, fg=self.text_color, anchor="w")
        self.multi_url_info_label.pack(anchor="w", padx=5, pady=5)
        
        self.multi_url_text = scrolledtext.ScrolledText(self.multi_url_frame, height=10, wrap=tk.WORD,
                                                   bg="white", fg="black")
        self.multi_url_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.import_multi_btn = tk.Button(self.multi_url_frame, text="Importa URL", 
                                       command=self.import_from_text,
                                       bg=self.accent_color, fg="white")
        self.import_multi_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Frame per i risultati di importazione
        self.import_results_frame = tk.LabelFrame(self.import_tab, text="Risultati Importazione", bg=self.bg_color, fg=self.text_color)
        self.import_results_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.import_results_text = scrolledtext.ScrolledText(self.import_results_frame, height=5, wrap=tk.WORD,
                                                        bg="white", fg="black")
        self.import_results_text.pack(fill=tk.X, padx=5, pady=5)
        self.import_results_text.config(state=tk.DISABLED)
    
    def browse_excel_file(self):
        """Apre un dialogo per selezionare un file Excel"""
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        file_path = filedialog.askopenfilename(
            title="Seleziona file Excel",
            initialdir=desktop_path,
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if file_path:
            self.excel_path_var.set(file_path)
    
    def import_from_excel(self):
        """Importa URL da un file Excel"""
        file_path = self.excel_path_var.get().strip()
        if not file_path:
            messagebox.showerror("Errore", "Seleziona un file Excel")
            return
        
        if not os.path.exists(file_path):
            messagebox.showerror("Errore", f"Il file {file_path} non esiste")
            return
        
        try:
            # Leggi la prima colonna del foglio Excel
            df = pd.read_excel(file_path)
            if df.empty or df.shape[1] == 0:
                messagebox.showwarning("Attenzione", "Il file Excel è vuoto o non contiene colonne")
                return
            
            # Estrai gli URL dalla prima colonna
            urls = []
            first_col = df.iloc[:, 0]  # Prima colonna
            for url in first_col:
                # Converti tutto in stringhe per sicurezza
                if url is not None:
                    urls.append(str(url))
            
            if not urls:
                messagebox.showwarning("Attenzione", "Nessun URL trovato nella prima colonna del file Excel")
                return
            
            self.process_multiple_urls(urls)
        
        except Exception as e:
            messagebox.showerror("Errore", f"Errore nella lettura del file Excel: {e}")
            logger.error(f"Errore nella lettura del file Excel: {e}")
    
    def import_from_text(self):
        """Importa URL dal campo di testo multilinea"""
        text = self.multi_url_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showerror("Errore", "Inserisci almeno un URL")
            return
        
        urls = [line.strip() for line in text.split("\n") if line.strip()]
        if not urls:
            messagebox.showwarning("Attenzione", "Nessun URL valido inserito")
            return
        
        self.process_multiple_urls(urls)
    
    def process_multiple_urls(self, urls):
        """Elabora un elenco di URL da importare"""
        if not urls:
            return
        
        # Pulisci e normalizza gli URL
        processed_urls = []
        invalid_urls = []
        
        for url in urls:
            cleaned_url = self.validate_and_clean_url(url)
            if cleaned_url:
                processed_urls.append(cleaned_url)
            else:
                invalid_urls.append(url)
        
        if invalid_urls:
            # Mostra messaggi per URL non validi
            for url in invalid_urls:
                self.add_import_result(f"URL non valido (ignorato): {url}", "error")
        
        if not processed_urls:
            messagebox.showwarning("Attenzione", "Nessun URL valido da importare")
            self.import_excel_btn.config(state=tk.NORMAL)
            self.import_multi_btn.config(state=tk.NORMAL)
            self.browse_btn.config(state=tk.NORMAL)
            return
        
        total = len(processed_urls)
        self.status_label.config(text=f"Importazione di {total} URL in corso...")
        self.root.update_idletasks()
        
        # Abilita il widget dei risultati
        self.import_results_text.config(state=tk.NORMAL)
        self.import_results_text.delete("1.0", tk.END)
        self.import_results_text.insert(tk.END, f"Inizio importazione di {total} URL...\n")
        self.import_results_text.config(state=tk.DISABLED)
        self.root.update_idletasks()
        
        # Disabilita i pulsanti durante l'importazione
        self.import_excel_btn.config(state=tk.DISABLED)
        self.import_multi_btn.config(state=tk.DISABLED)
        self.browse_btn.config(state=tk.DISABLED)
        
        # Avvia l'importazione in un thread separato
        import_thread = threading.Thread(target=self.import_urls_thread, args=(processed_urls,))
        import_thread.daemon = True
        import_thread.start()
    
    def validate_and_clean_url(self, url):
        """Valida e pulisce un URL"""
        # Rimuovi spazi all'inizio e alla fine
        url = url.strip()
        
        # Controlla se è una stringa vuota
        if not url:
            return None
        
        # Lista di domini validi di siti immobiliari
        valid_domains = [
            "idealista.it",
            "immobiliare.it", 
            "casa.it",
            "subito.it",
            "tecnocasa.it",
            "trovacasa.net",
            "wikicasa.it",
            "habitissimo.it",
            "troviamo.casa",
            "remax.it"
        ]
        
        # Lista di prefissi URL completi
        valid_prefixes = [
            "https://www.idealista.it/",
            "https://www.immobiliare.it/",
            "https://www.casa.it/",
            "https://www.subito.it/",
            "https://www.tecnocasa.it/",
            "https://www.trovacasa.net/",
            "https://www.wikicasa.it/",
            "https://www.habitissimo.it/",
            "https://www.troviamo.casa/",
            "https://www.remax.it/"
        ]
        
        # Se la stringa inizia con http o https, verifica se è un URL valido
        if url.startswith(("http://", "https://")):
            # Se non contiene spazi, potrebbe essere un URL valido
            if ' ' not in url:
                return url
            
            # Altrimenti proviamo a estrarre la parte dell'URL fino al primo spazio
            clean_url = url.split(' ')[0]
            if any(domain in clean_url.lower() for domain in valid_domains):
                return clean_url
        
        # Se potrebbe essere un URL senza protocollo
        elif any(domain in url.lower() for domain in valid_domains) and len(url) < 250:
            if ' ' not in url:
                # URL semplice senza spazi, aggiungiamo https://
                if not url.lower().startswith("www."):
                    return "https://www." + url
                else:
                    return "https://" + url
            
            # Proviamo a estrarre la parte che sembra un dominio valido
            for domain in valid_domains:
                if domain in url.lower():
                    parts = url.lower().split(domain)
                    if len(parts) > 1:
                        # Estrai il dominio e il possibile percorso
                        domain_part = url[url.lower().find(domain) - (3 if url.lower().find("www.") != -1 else 0):] 
                        
                        # Pulisci eventuali caratteri non URL
                        domain_part = domain_part.split(' ')[0]  # Tronca allo spazio
                        domain_part = re.sub(r'[^\w./\-]', '', domain_part)  # Rimuovi caratteri speciali
                        
                        if "www." in domain_part.lower():
                            return "https://" + domain_part
                        else:
                            return "https://www." + domain_part
        
        # Se la stringa è lunga ma contiene menzioni di siti immobiliari, proviamo un approccio diverso
        elif len(url) > 50 and any(domain in url.lower() for domain in valid_domains):
            # Cerca direttamente URL predefiniti nel testo
            for prefix in valid_prefixes:
                if prefix.lower() in url.lower():
                    start_idx = url.lower().find(prefix.lower())
                    url_part = url[start_idx:]
                    
                    # Tronca l'URL al primo spazio o carattere speciale
                    end_chars = [' ', ',', ';', ')', ']', '}', '"', "'"]
                    for char in end_chars:
                        if char in url_part:
                            url_part = url_part.split(char)[0]
                    
                    # Sostituisci con l'URL corretto (case-sensitive)
                    correct_prefix = prefix
                    return correct_prefix + url_part[len(prefix):]
        
        # Verifica se è solo un nome di dominio
        elif '.' in url and ' ' not in url and url.count('.') == 1 and len(url) < 50:
            if any(domain == url.lower() for domain in valid_domains):
                return "https://www." + url
        
        # Fallback per URL non validi
        return None
    
    def import_urls_thread(self, urls):
        """Thread per l'importazione di più URL"""
        total = len(urls)
        success = 0
        skipped = 0
        failed = 0
        
        for i, url in enumerate(urls):
            try:
                # Aggiorna lo stato
                self.root.after(0, lambda msg=f"Importazione URL {i+1}/{total}... ({success} aggiunti, {failed} falliti)": 
                               self.status_label.config(text=msg))
                
                # Controlla se l'URL esiste già
                exists = any(prop.url == url for prop in self.tracker.properties)
                if exists:
                    self.root.after(0, lambda url=url: self.add_import_result(
                        f"URL già esistente (saltato): {url}", "warning"))
                    skipped += 1
                    continue
                
                # Aggiungi la proprietà
                prop = self.tracker.add_property(url)
                if prop:
                    success += 1
                    self.root.after(0, lambda title=prop.title, url=url: self.add_import_result(
                        f"✅ Aggiunto: {title} - {url}", "success"))
                else:
                    failed += 1
                    self.root.after(0, lambda url=url: self.add_import_result(
                        f"❌ Errore nell'aggiunta: {url}", "error"))
            
            except Exception as e:
                failed += 1
                self.root.after(0, lambda url=url, e=str(e): self.add_import_result(
                    f"❌ Eccezione: {url} - {e}", "error"))
        
        # Aggiorna l'interfaccia al termine
        self.root.after(0, lambda: self.complete_import(total, success, skipped, failed))
    
    def add_import_result(self, message, status="info"):
        """Aggiunge un messaggio al widget dei risultati dell'importazione"""
        self.import_results_text.config(state=tk.NORMAL)
        
        # Determina il colore del testo in base allo stato
        tag = f"tag_{status}"
        if not tag in self.import_results_text.tag_names():
            if status == "success":
                self.import_results_text.tag_configure(tag, foreground="green")
            elif status == "error":
                self.import_results_text.tag_configure(tag, foreground="red")
            elif status == "warning":
                self.import_results_text.tag_configure(tag, foreground="orange")
            else:
                self.import_results_text.tag_configure(tag, foreground="black")
        
        # Inserisci il messaggio con il tag appropriato
        self.import_results_text.insert(tk.END, message + "\n", tag)
        self.import_results_text.see(tk.END)  # Auto-scroll
        self.import_results_text.config(state=tk.DISABLED)
        self.root.update_idletasks()
    
    def complete_import(self, total, success, skipped, failed):
        """Completa il processo di importazione"""
        # Riabilita i pulsanti
        self.import_excel_btn.config(state=tk.NORMAL)
        self.import_multi_btn.config(state=tk.NORMAL)
        self.browse_btn.config(state=tk.NORMAL)
        
        # Aggiorna l'interfaccia
        self.update_property_list()
        
        # Mostra il riepilogo
        summary = f"\nImportazione completata: {success} aggiunti, {skipped} saltati, {failed} falliti (su {total} totali)"
        self.add_import_result(summary, "info")
        
        # Aggiorna lo stato
        self.status_label.config(text=f"Importazione completata: {success} immobili aggiunti")
        
        # Se ci sono stati successi, passa alla scheda principale
        if success > 0:
            self.notebook.select(0)  # Seleziona la prima scheda (Lista Immobili)
        
        # Pulisci il campo testo
        self.multi_url_text.delete("1.0", tk.END)
    
    def add_property(self):
        """Aggiunge una nuova proprietà dal campo URL"""
        url = self.url_var.get().strip()
        
        if not url:
            messagebox.showerror("Errore", "Inserisci un URL valido")
            return
        
        # Valida e pulisci l'URL
        cleaned_url = self.validate_and_clean_url(url)
        if not cleaned_url:
            messagebox.showerror("Errore", "L'URL inserito non sembra valido. Inserisci un URL completo di un portale immobiliare.")
            return
        
        # Verifica se l'URL esiste già
        if any(prop.url == cleaned_url for prop in self.tracker.properties):
            messagebox.showwarning("Attenzione", "Questo URL è già monitorato")
            return
        
        # Mostra messaggio di caricamento
        self.status_label.config(text="Aggiunta in corso...")
        self.root.update_idletasks()
        
        # Aggiunge la proprietà in un thread separato
        def add_thread():
            prop = self.tracker.add_property(cleaned_url)
            
            # Aggiorna l'interfaccia nel thread principale
            self.root.after(0, lambda: self.after_add_property(prop, cleaned_url))
        
        thread = threading.Thread(target=add_thread)
        thread.daemon = True
        thread.start()
    
    def after_add_property(self, prop, url):
        """Callback dopo l'aggiunta di una proprietà"""
        if prop:
            self.update_property_list()
            self.url_var.set("")
            self.status_label.config(text="Immobile aggiunto")
        else:
            messagebox.showerror("Errore", f"Impossibile aggiungere l'immobile: {url}")
            self.status_label.config(text="Errore nell'aggiunta")
    
    def update_property_list(self):
        """Aggiorna la lista delle proprietà nel treeview"""
        # Cancella tutti gli elementi
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Aggiungi tutte le proprietà
        for i, prop in enumerate(self.tracker.properties):
            # Calcola la variazione di prezzo
            diff, percent = prop.get_price_change()
            
            # Formatta la variazione
            if diff == 0:
                change_text = "Nessuna variazione"
            else:
                change_text = f"{diff:+,d}€ ({percent:.1f}%)"
            
            # Ottieni l'ultimo aggiornamento
            last_update = "Mai" if not prop.price_history else prop.price_history[-1]["date"]
            
            # Formatta il rating
            rating_text = self.rating_options[prop.rating]
            
            # Formatta il prezzo alternativo
            alt_price_text = f"{prop.alternate_price:,d}€".replace(",", ".") if prop.alternate_price > 0 else ""
            
            # Icone per le azioni: una per vedere il tooltip e una per aprire
            action_icons = "🔍 🌐"  # Lente e globo per vedere e aprire
            
            # Aggiungi alla lista
            item_id = self.tree.insert("", tk.END, values=(
                prop.title,
                f"{prop.price:,d}€".replace(",", "."),
                change_text,
                rating_text,
                alt_price_text,
                last_update,
                action_icons
            ))
            
            # Applica tag per stile titolo come link e righe alternate
            row_tag = "even_row" if i % 2 == 0 else "odd_row"
            self.tree.item(item_id, tags=(row_tag, "link"))
        
        # Aggiorna il conteggio
        self.count_label.config(text=f"Immobili: {len(self.tracker.properties)}")
    
    def on_property_select(self, event):
        """Gestisce la selezione di una proprietà dalla lista"""
        # Abilita i pulsanti per aggiornare/rimuovere
        if self.tree.selection():
            self.remove_btn.config(state=tk.NORMAL)
            
            # Aggiorna i campi dei dettagli
            self.update_details_controls()
        else:
            self.remove_btn.config(state=tk.DISABLED)
            self.disable_details_controls()
            
        # Chiudi il popup se esiste
        self.close_image_popup()
    
    def update_details_controls(self):
        """Aggiorna i controlli dei dettagli con i dati della proprietà selezionata"""
        selection = self.tree.selection()
        if not selection:
            return
        
        # Ottieni l'indice della proprietà selezionata
        index = self.tree.index(selection[0])
        prop = self.tracker.properties[index]
        
        # Imposta il rating
        self.rating_var.set(self.rating_options[prop.rating])
        self.rating_indicator.delete("all")
        self.rating_indicator.create_oval(2, 2, 18, 18, fill=self.rating_colors[prop.rating], outline="black")
        
        # Imposta il prezzo alternativo
        self.alt_price_var.set(str(prop.alternate_price) if prop.alternate_price > 0 else "")
        
        # Imposta le note
        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert("1.0", prop.notes)
        
        # Abilita i controlli
        self.rating_menu.config(state=tk.NORMAL)
        self.alt_price_entry.config(state=tk.NORMAL)
        self.alt_price_save.config(state=tk.NORMAL)
        self.notes_text.config(state=tk.NORMAL)
        self.notes_save.config(state=tk.NORMAL)
    
    def disable_details_controls(self):
        """Disabilita i controlli dei dettagli"""
        self.rating_var.set("Non valutato")
        self.rating_indicator.delete("all")
        self.rating_indicator.create_oval(2, 2, 18, 18, fill="gray", outline="black")
        self.alt_price_var.set("")
        self.notes_text.delete("1.0", tk.END)
        
        self.rating_menu.config(state=tk.DISABLED)
        self.alt_price_entry.config(state=tk.DISABLED)
        self.alt_price_save.config(state=tk.DISABLED)
        self.notes_text.config(state=tk.DISABLED)
        self.notes_save.config(state=tk.DISABLED)
    
    def update_rating(self, *args):
        """Aggiorna il rating della proprietà selezionata"""
        selection = self.tree.selection()
        if not selection:
            return
        
        # Ottieni l'indice della proprietà selezionata
        index = self.tree.index(selection[0])
        
        # Imposta il rating
        rating_index = self.rating_options.index(self.rating_var.get())
        self.tracker.properties[index].rating = rating_index
        
        # Aggiorna l'indicatore del semaforo
        self.rating_indicator.delete("all")
        self.rating_indicator.create_oval(2, 2, 18, 18, fill=self.rating_colors[rating_index], outline="black")
        
        # Salva e aggiorna la lista
        self.tracker.save_properties()
        self.update_property_list()
        
        # Riseleziona la proprietà
        self.tree.selection_set(self.tree.get_children()[index])
    
    def save_alternate_price(self):
        """Salva il prezzo alternativo della proprietà selezionata"""
        selection = self.tree.selection()
        if not selection:
            return
        
        # Ottieni l'indice della proprietà selezionata
        index = self.tree.index(selection[0])
        
        # Leggi il prezzo alternativo
        try:
            alt_price_text = self.alt_price_var.get().strip()
            alt_price = int(alt_price_text.replace(".", "").replace(",", "").replace("€", "")) if alt_price_text else 0
            
            # Imposta il prezzo alternativo
            self.tracker.properties[index].alternate_price = alt_price
            
            # Salva e aggiorna la lista
            self.tracker.save_properties()
            self.update_property_list()
            
            # Riseleziona la proprietà
            self.tree.selection_set(self.tree.get_children()[index])
            
            # Feedback
            self.status_label.config(text="Prezzo alternativo salvato")
        except ValueError:
            messagebox.showerror("Errore", "Inserisci un prezzo valido")
    
    def save_notes(self):
        """Salva le note della proprietà selezionata"""
        selection = self.tree.selection()
        if not selection:
            return
        
        # Ottieni l'indice della proprietà selezionata
        index = self.tree.index(selection[0])
        
        # Leggi le note
        notes = self.notes_text.get("1.0", tk.END).strip()
        
        # Imposta le note
        self.tracker.properties[index].notes = notes
        
        # Salva le proprietà
        self.tracker.save_properties()
        
        # Feedback
        self.status_label.config(text="Note salvate")
    
    def on_property_double_click(self, event):
        """Gestisce il doppio clic su una proprietà - apre la pagina web"""
        selection = self.tree.selection()
        if not selection:
            return
        
        # Ottieni l'indice della proprietà selezionata
        index = self.tree.index(selection[0])
        prop = self.tracker.properties[index]
        
        # Apri direttamente la pagina web
        self.open_url(prop.url)
    
    def on_tree_motion(self, event):
        """Gestisce il movimento del mouse sul treeview"""
        # Ottieni l'item e la colonna sotto il cursore
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            item = self.tree.identify_row(event.y)
            if item:
                # Ottieni l'indice della proprietà
                index = self.tree.index(item)
                if 0 <= index < len(self.tracker.properties):
                    prop = self.tracker.properties[index]
                    
                    # Posiziona il tooltip vicino al cursore
                    show_x = self.root.winfo_rootx() + event.x + 20
                    show_y = self.root.winfo_rooty() + event.y + 10
                    
                    # Mostra il tooltip semplice
                    self.show_simple_tooltip(prop, show_x, show_y)
                    return
        
        # Se il mouse non è su una cella, chiudi il tooltip
        self.close_image_popup_if_not_over_popup(event)
    
    def close_image_popup_if_not_over_popup(self, event):
        """Chiude il popup a meno che il mouse non sia direttamente sopra di esso"""
        if self.image_popup:
            # Verifica se il mouse è direttamente sopra il popup
            popup_x = self.image_popup.winfo_x()
            popup_y = self.image_popup.winfo_y()
            popup_width = self.image_popup.winfo_width()
            popup_height = self.image_popup.winfo_height()
            
            if not (popup_x <= event.x_root <= popup_x + popup_width and
                   popup_y <= event.y_root <= popup_y + popup_height):
                self.close_image_popup()
    
    def show_simple_tooltip(self, prop, x_pos, y_pos):
        """Mostra un tooltip semplice e leggero in stile browser/Excel"""
        # Se già mostriamo lo stesso tooltip, non fare nulla
        if self.image_popup and hasattr(self.image_popup, 'prop_url') and self.image_popup.prop_url == prop.url:
            return
        
        # Chiudi eventuali popup esistenti
        self.close_image_popup()
        
        try:
            # Crea il tooltip
            tooltip = tk.Toplevel(self.root)
            tooltip.withdraw()  # Nascondi finché non è pronto
            tooltip.overrideredirect(True)  # Rimuovi decorazioni finestra
            tooltip.attributes("-topmost", True)  # Sempre in primo piano
            tooltip.prop_url = prop.url  # Salva riferimento all'URL
            
            # Frame principale
            frame = tk.Frame(tooltip, bd=1, relief=tk.SOLID, bg="white")
            frame.pack(fill=tk.BOTH, expand=True)
            
            # Area contenuto
            content = tk.Frame(frame, bg="white", padx=10, pady=10)
            content.pack(fill=tk.BOTH, expand=True)
            
            # URL e titolo
            url_parts = prop.url.split("/")
            domain = url_parts[2] if len(url_parts) > 2 else prop.url
            
            # Identifica il sito
            site_name = "Idealista" if "idealista" in prop.url else \
                       "Immobiliare" if "immobiliare" in prop.url else \
                       "Casa.it" if "casa.it" in prop.url else \
                       domain
            
            # Icona e nome sito
            site_frame = tk.Frame(content, bg="white")
            site_frame.pack(fill=tk.X, pady=(0, 5))
            
            site_icon = "🟢" if "idealista" in prop.url else \
                       "🔵" if "immobiliare" in prop.url else \
                       "🟠" if "casa.it" in prop.url else "🏠"
            
            icon_label = tk.Label(site_frame, text=site_icon, font=("Helvetica", 12), bg="white")
            icon_label.pack(side=tk.LEFT, padx=(0, 5))
            
            domain_label = tk.Label(site_frame, text=site_name, font=("Helvetica", 9), 
                                  bg="white", fg="#666666")
            domain_label.pack(side=tk.LEFT)
            
            # Titolo 
            title_label = tk.Label(content, text=prop.title, font=("Helvetica", 10, "bold"), 
                                bg="white", fg=self.link_color, justify=tk.LEFT, wraplength=300)
            title_label.pack(fill=tk.X, pady=5, anchor="w")
            
            # Prezzo
            price_frame = tk.Frame(content, bg="white")
            price_frame.pack(fill=tk.X, anchor="w")
            
            price_str = f"{prop.price:,d}€".replace(",", ".")
            price_label = tk.Label(price_frame, text=price_str, font=("Helvetica", 11, "bold"), 
                               bg="white", fg=self.price_color)
            price_label.pack(side=tk.LEFT)
            
            # Miniatura se disponibile
            if prop.image_url:
                try:
                    response = requests.get(prop.image_url, stream=True, timeout=3)
                    img = Image.open(BytesIO(response.content))
                    
                    # Ridimensiona l'immagine
                    thumb_size = 80
                    if img.width > thumb_size or img.height > thumb_size:
                        ratio = min(thumb_size / img.width, thumb_size / img.height)
                        img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
                    
                    # Crea la miniatura
                    photo = ImageTk.PhotoImage(img)
                    img_label = tk.Label(content, image=photo, bd=1, relief=tk.SOLID)
                    img_label.image = photo  # Mantieni un riferimento
                    img_label.pack(side=tk.RIGHT, padx=(10, 0), anchor="ne")
                except Exception as e:
                    # Ignora errori nell'immagine
                    pass
            
            # Messaggio di click
            hint_label = tk.Label(content, text="Clicca per aprire", font=("Helvetica", 8), 
                               bg="white", fg="#999999")
            hint_label.pack(side=tk.BOTTOM, anchor="se", pady=(5,0))
            
            # Gestisci il click
            for widget in [frame, content, title_label, price_label, hint_label]:
                widget.bind("<Button-1>", lambda e, url=prop.url: self.open_url(url))
            
            # Posiziona il tooltip vicino al mouse
            tooltip.update_idletasks()  # Aggiorna le dimensioni
            
            # Assicurati che il tooltip sia visibile sullo schermo
            width = tooltip.winfo_reqwidth()
            height = tooltip.winfo_reqheight()
            
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            if x_pos + width > screen_width:
                x_pos = screen_width - width - 10
            if y_pos + height > screen_height:
                y_pos = screen_height - height - 10
            
            tooltip.geometry(f"+{x_pos}+{y_pos}")
            tooltip.deiconify()  # Rendi visibile
            
            # Salva un riferimento al popup
            self.image_popup = tooltip
            
        except Exception as e:
            logger.error(f"Errore nel mostrare il tooltip: {e}")
    
    def on_tree_leave(self, event):
        """Gestisce l'evento quando il mouse esce dal treeview"""
        # Chiudi il popup quando il mouse esce dal treeview
        self.close_image_popup()
    
    def check_image_hover(self, event):
        """Verifica su quale elemento del treeview si trova il mouse e mostra il tooltip appropriato"""
        # Ottieni l'item e la colonna sotto il cursore
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell" or region == "heading":
            item = self.tree.identify_row(event.y)
            column = self.tree.identify_column(event.x)
            
            if item:  # Se siamo su una riga
                # Ottieni l'indice della proprietà
                index = self.tree.index(item)
                if 0 <= index < len(self.tracker.properties):
                    prop = self.tracker.properties[index]
                    
                    # Se il mouse è sopra la colonna URL, mostra il tooltip dell'URL
                    if column == "#7":  # La colonna #7 corrisponde a "URL"
                        # Calcola le coordinate dell'area che contiene l'icona URL
                        bbox = self.tree.bbox(item, column)
                        if bbox:
                            x, y, width, height = bbox
                            
                            # Posiziona il popup sopra la cella
                            show_x = self.root.winfo_rootx() + self.tree.winfo_rootx() + x
                            show_y = self.root.winfo_rooty() + self.tree.winfo_rooty() + y - 120
                            
                            # Mostra l'anteprima dell'URL
                            self.show_url_preview(prop, show_x, show_y)
                            return
                    
                    # Se il mouse è sopra la colonna del titolo e l'immobile ha un'immagine, mostra l'immagine
                    elif column == "#1" and prop.image_url:
                        # Calcola le coordinate dell'area che contiene il titolo
                        bbox = self.tree.bbox(item, column)
                        if bbox:
                            x, y, width, height = bbox
                            
                            show_x = self.root.winfo_rootx() + self.tree.winfo_rootx() + x + width + 10
                            show_y = self.root.winfo_rooty() + self.tree.winfo_rooty() + y - 10
                            
                            # Mostra l'immagine come tooltip
                            self.show_image_popup(prop, show_x, show_y)
                            return
            
            elif column == "#7" and self.tree.identify_region(event.x, event.y) == "heading":
                # Se siamo sull'intestazione della colonna URL, mostra un tooltip
                tooltip = tk.Toplevel(self.root)
                tooltip.withdraw()
                tooltip.overrideredirect(True)
                
                frame = tk.Frame(tooltip, bd=1, relief=tk.SOLID, bg="lightyellow")
                frame.pack(fill=tk.BOTH, expand=True)
                
                label = tk.Label(frame, text="Passa il mouse qui per vedere\nl'anteprima dell'URL", 
                              bg="lightyellow", fg="black", 
                              font=("Helvetica", 9), justify=tk.LEFT)
                label.pack(padx=10, pady=5)
                
                x = self.root.winfo_rootx() + event.x + 20
                y = self.root.winfo_rooty() + event.y + 10
                
                tooltip.geometry(f"+{x}+{y}")
                tooltip.deiconify()
                
                # Chiudi il tooltip dopo 2 secondi
                self.root.after(2000, tooltip.destroy)
                return
            
            # Se non siamo su una colonna speciale o non c'è una proprietà, chiudi il popup
            if self.image_popup:
                # Mantieni aperto il popup solo se il mouse è sopra di esso
                popup_x = self.image_popup.winfo_x()
                popup_y = self.image_popup.winfo_y()
                popup_width = self.image_popup.winfo_width()
                popup_height = self.image_popup.winfo_height()
                
                mouse_over_popup = (popup_x <= event.x_root <= popup_x + popup_width and
                                   popup_y <= event.y_root <= popup_y + popup_height)
                
                if not mouse_over_popup:
                    self.close_image_popup()
        # Se non siamo in una regione interessante, chiudi eventuali popup
        self.close_image_popup_if_not_hovering(event)
    
    def close_image_popup_if_not_hovering(self, event):
        """Chiude il popup solo se il mouse non è sopra di esso"""
        if self.image_popup:
            popup_x = self.image_popup.winfo_x()
            popup_y = self.image_popup.winfo_y()
            popup_width = self.image_popup.winfo_width()
            popup_height = self.image_popup.winfo_height()
            
            mouse_over_popup = (popup_x <= event.x_root <= popup_x + popup_width and
                               popup_y <= event.y_root <= popup_y + popup_height)
            
            if not mouse_over_popup:
                self.close_image_popup()
    
    def show_property_image(self):
        """Metodo non più usato"""
        pass
    
    def show_image_popup(self, prop, x_pos=None, y_pos=None):
        """Mostra un popup con l'immagine dell'immobile"""
        # Se c'è già un popup e mostra la stessa immagine, non fare nulla
        if self.image_popup and hasattr(self.image_popup, 'prop_url') and self.image_popup.prop_url == prop.url:
            return
            
        try:
            # Chiudi eventuali popup esistenti
            self.close_image_popup()
            
            # Scarica l'immagine
            response = requests.get(prop.image_url, stream=True, timeout=10)
            response.raise_for_status()
            
            # Crea l'immagine
            img = Image.open(BytesIO(response.content))
            
            # Ridimensiona l'immagine se troppo grande
            max_width, max_height = 400, 300  # Dimensioni più piccole per un effetto tooltip
            if img.width > max_width or img.height > max_height:
                ratio = min(max_width / img.width, max_height / img.height)
                new_width = int(img.width * ratio)
                new_height = int(img.height * ratio)
                img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # Converti in formato Tkinter
            photo = ImageTk.PhotoImage(img)
            
            # Crea il popup
            popup = tk.Toplevel(self.root)
            popup.title("")  # Nessun titolo per un aspetto più leggero
            popup.transient(self.root)
            popup.prop_url = prop.url  # Salva l'URL della proprietà nel popup
            
            # Rimuovi la decorazione della finestra per un aspetto più leggero
            popup.overrideredirect(True)
            
            # Rendi la finestra inizialmente trasparente
            popup.attributes("-alpha", 0.0)
            
            # Posiziona il popup vicino al punto specificato o al cursore del mouse
            if x_pos is not None and y_pos is not None:
                x = x_pos
                y = y_pos
            else:
                x = self.root.winfo_pointerx() + 10
                y = self.root.winfo_pointery() + 10
            
            # Assicurati che il popup sia completamente visibile
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            if x + img.width > screen_width:
                x = screen_width - img.width - 10
            if y + img.height > screen_height:
                y = screen_height - img.height - 10
            
            popup.geometry(f"{img.width}x{img.height}+{x}+{y}")
            
            # Cornice per tutto il contenuto
            main_frame = tk.Frame(popup, bd=1, relief=tk.SOLID)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Aggiungi l'immagine a un label
            label = tk.Label(main_frame, image=photo, bd=0)
            label.image = photo  # Mantieni un riferimento
            label.pack(fill=tk.BOTH, expand=True)
            
            # Aggiungi il titolo e il prezzo in un overlay semi-trasparente
            info_frame = tk.Frame(main_frame, bg="#FFFFFF", bd=0)
            info_frame.place(relx=0, rely=1, anchor="sw", relwidth=1, y=0)
            
            # Rendi il frame semi-trasparente
            info_frame.configure(bg="#FFFFFFCC")
            
            # Titolo dell'immobile
            title_label = tk.Label(info_frame, text=prop.title, font=("Helvetica", 9, "bold"), 
                                bg="#FFFFFFCC", fg="black", anchor="w")
            title_label.pack(fill=tk.X, padx=5, pady=(5,0))
            
            # Prezzo
            price_text = f"Prezzo: {prop.price:,d}€".replace(",", ".")
            if prop.alternate_price > 0:
                price_text += f" (Alt.: {prop.alternate_price:,d}€)".replace(",", ".")
                
            price_label = tk.Label(info_frame, text=price_text, font=("Helvetica", 8), 
                                bg="#FFFFFFCC", fg="black", anchor="w")
            price_label.pack(fill=tk.X, padx=5, pady=(0,5))
            
            # Aggiungi handler per l'evento di doppio clic sull'immagine (apre l'URL)
            popup.bind("<Double-Button-1>", lambda e: self.open_url(prop.url))
            
            # Salva un riferimento al popup
            self.image_popup = popup
            
            # Avvia l'animazione di fade in
            self.animate_popup_fadein()
        
        except Exception as e:
            logger.error(f"Errore nel mostrare l'immagine: {e}")
    
    def animate_popup_fadein(self, alpha=0.0):
        """Anima l'entrata graduale del popup"""
        if self.image_popup:
            if alpha < 1.0:
                alpha += 0.1
                self.image_popup.attributes("-alpha", alpha)
                self.root.after(20, lambda: self.animate_popup_fadein(alpha))
    
    def start_popup_fadeout(self):
        """Inizia l'animazione di uscita graduale del popup"""
        if self.image_popup:
            self.animate_popup_fadeout()
    
    def animate_popup_fadeout(self, alpha=1.0):
        """Anima l'uscita graduale del popup"""
        if self.image_popup:
            if alpha > 0.1:
                alpha -= 0.1
                self.image_popup.attributes("-alpha", alpha)
                self.root.after(20, lambda: self.animate_popup_fadeout(alpha))
            else:
                self.image_popup.destroy()
                self.image_popup = None
    
    def close_image_popup(self):
        """Chiude il popup dell'immagine se aperto"""
        if self.image_popup:
            self.image_popup.destroy()
            self.image_popup = None
    
    def open_url(self, url):
        """Apre l'URL nel browser predefinito"""
        import webbrowser
        webbrowser.open(url)
    
    def show_context_menu(self, event):
        """Mostra un menu contestuale al click destro"""
        # Trova l'elemento sotto il cursore
        item = self.tree.identify_row(event.y)
        if not item:
            return
        
        # Seleziona l'elemento
        self.tree.selection_set(item)
        
        # Ottieni l'indice della proprietà selezionata
        index = self.tree.index(item)
        prop = self.tracker.properties[index]
        
        # Crea il menu contestuale
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Apri nel Browser", command=lambda: self.open_url(prop.url))
        menu.add_command(label="Visualizza Immagine", command=lambda: self.on_property_double_click(None))
        menu.add_separator()
        menu.add_command(label="Aggiorna Prezzo", command=lambda: self.update_property_by_index(index))
        menu.add_command(label="Rimuovi", command=self.remove_selected_property)
        
        # Mostra il menu
        menu.tk_popup(event.x_root, event.y_root)
    
    def update_property_by_index(self, index):
        """Aggiorna una proprietà specifica per indice"""
        if 0 <= index < len(self.tracker.properties):
            # Mostra messaggio di caricamento
            self.status_label.config(text="Aggiornamento in corso...")
            self.root.update_idletasks()
            
            # Aggiorna la proprietà in un thread separato
            def update_thread():
                price = self.tracker.update_property(index)
                
                # Aggiorna l'interfaccia nel thread principale
                self.root.after(0, lambda: self.after_update_property(price > 0))
            
            thread = threading.Thread(target=update_thread)
            thread.daemon = True
            thread.start()
    
    def after_update_property(self, success):
        """Callback dopo l'aggiornamento di una proprietà"""
        if success:
            self.update_property_list()
            self.status_label.config(text="Immobile aggiornato")
        else:
            messagebox.showerror("Errore", "Impossibile aggiornare l'immobile")
            self.status_label.config(text="Errore nell'aggiornamento")
    
    def update_all_properties(self):
        """Aggiorna tutte le proprietà"""
        if not self.tracker.properties:
            messagebox.showinfo("Info", "Nessun immobile da aggiornare")
            return
        
        # Disabilita i pulsanti durante l'aggiornamento
        self.update_btn.config(state=tk.DISABLED)
        self.remove_btn.config(state=tk.DISABLED)
        self.add_btn.config(state=tk.DISABLED)
        
        # Mostra messaggio di caricamento
        self.status_label.config(text="Aggiornamento di tutti gli immobili...")
        self.root.update_idletasks()
        
        # Aggiorna tutte le proprietà in un thread separato
        def update_all_thread():
            updated, changes = self.tracker.update_all_properties()
            
            # Aggiorna l'interfaccia nel thread principale
            self.root.after(0, lambda: self.after_update_all(updated, changes))
        
        self.update_thread = threading.Thread(target=update_all_thread)
        self.update_thread.daemon = True
        self.update_thread.start()
    
    def after_update_all(self, updated, changes):
        """Callback dopo l'aggiornamento di tutte le proprietà"""
        self.update_property_list()
        
        # Riabilita i pulsanti
        self.update_btn.config(state=tk.NORMAL)
        self.add_btn.config(state=tk.NORMAL)
        
        # Aggiorna lo stato della selezione
        self.on_property_select(None)
        
        # Aggiorna il messaggio di stato
        self.status_label.config(text=f"Aggiornati {updated} immobili, {changes} variazioni di prezzo")
    
    def remove_selected_property(self):
        """Rimuove la proprietà selezionata"""
        selection = self.tree.selection()
        if not selection:
            return
        
        # Ottieni l'indice della proprietà selezionata
        index = self.tree.index(selection[0])
        
        # Chiedi conferma
        if messagebox.askyesno("Conferma", "Vuoi davvero rimuovere questo immobile dal monitoraggio?"):
            if self.tracker.remove_property(index):
                self.update_property_list()
                self.status_label.config(text="Immobile rimosso")
            else:
                messagebox.showerror("Errore", "Impossibile rimuovere l'immobile")
    
    def on_close(self):
        """Gestisce la chiusura dell'applicazione"""
        if self.update_thread and self.update_thread.is_alive():
            if messagebox.askyesno("Conferma", "Aggiornamento in corso. Vuoi chiudere l'applicazione?"):
                self.root.destroy()
        else:
            self.root.destroy()

    def on_tree_click(self, event):
        """Gestisce il click singolo sugli elementi del treeview"""
        # Ottieni l'item e la colonna sotto il cursore
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            item = self.tree.identify_row(event.y)
            column = self.tree.identify_column(event.x)
            
            # Se il click è sulla colonna URL, mostra il tooltip URL
            if column == "#7" and item:  # Colonna delle azioni
                # Ottieni l'indice della proprietà
                index = self.tree.index(item)
                if 0 <= index < len(self.tracker.properties):
                    prop = self.tracker.properties[index]
                    
                    # Determina quale icona è stata cliccata
                    bbox = self.tree.bbox(item, column)
                    if bbox:
                        x, y, width, height = bbox
                        # La prima metà è la lente, la seconda metà è il globo
                        icon_x = event.x - x
                        if icon_x < width / 2:  # Cliccato sulla lente - mostra anteprima
                            # Posiziona il popup vicino alla cella, ma non sopra il mouse
                            show_x = self.root.winfo_rootx() + self.tree.winfo_rootx() + x + width + 5
                            show_y = self.root.winfo_rooty() + self.tree.winfo_rooty() + y - 100
                            
                            # Mostra l'anteprima dell'URL con opzione di persistenza
                            self.show_url_preview(prop, show_x, show_y, True)  # True indica che il popup è persistente
                        else:  # Cliccato sul globo - apri direttamente URL
                            self.open_url(prop.url)
                        return
            
            # Se il click è sulla colonna del titolo, seleziona l'elemento
            if column == "#1" and item:
                self.tree.selection_set(item)
                self.on_property_select(None)
                return
    
    def show_url_preview(self, prop, x_pos=None, y_pos=None, persistent=False):
        """Mostra un popup con l'anteprima dell'URL dell'immobile"""
        # Se c'è già un popup e mostra lo stesso URL, non fare nulla
        if self.image_popup and hasattr(self.image_popup, 'prop_url') and self.image_popup.prop_url == prop.url:
            return
            
        try:
            # Chiudi eventuali popup esistenti
            self.close_image_popup()
            
            # Crea il popup
            popup = tk.Toplevel(self.root)
            popup.title("")  # Nessun titolo per un aspetto più leggero
            popup.transient(self.root)
            popup.prop_url = prop.url  # Salva l'URL della proprietà nel popup
            
            # Rimuovi la decorazione della finestra per un aspetto più leggero
            popup.overrideredirect(True)
            
            # Rendi la finestra inizialmente trasparente
            popup.attributes("-alpha", 0.0)
            
            # Posiziona il popup vicino al punto specificato o al cursore del mouse
            if x_pos is not None and y_pos is not None:
                x = x_pos
                y = y_pos
            else:
                x = self.root.winfo_pointerx() + 10
                y = self.root.winfo_pointery() + 10
            
            # Dimensioni del popup più grandi per mostrare più contenuto
            width = 400
            height = 200
            
            # Assicurati che il popup sia completamente visibile
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            if x + width > screen_width:
                x = screen_width - width - 10
            if y + height > screen_height:
                y = screen_height - height - 10
            
            popup.geometry(f"{width}x{height}+{x}+{y}")
            
            # Cornice per tutto il contenuto
            main_frame = tk.Frame(popup, bd=1, relief=tk.SOLID, bg="white")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Intestazione con icona sito e titolo
            header_frame = tk.Frame(main_frame, bg="#f0f0f0", bd=0)
            header_frame.pack(fill=tk.X, padx=0, pady=0)
            
            # Area contenuto per l'anteprima
            content_frame = tk.Frame(main_frame, bg="white")
            content_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
            
            # Barra di stato in fondo
            status_frame = tk.Frame(main_frame, bg="#f0f0f0", height=20)
            status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=0, pady=0)
            
            # Identificazione del sito
            site_name = "Idealista" if "idealista" in prop.url else \
                       "Immobiliare" if "immobiliare" in prop.url else \
                       "Casa" if "casa.it" in prop.url else \
                       "Unknown"
            
            # Icona specifica per il sito
            site_icon = "🏠"  # Default
            if site_name == "Idealista":
                site_icon = "🟢"  # Verde come il logo di Idealista
            elif site_name == "Immobiliare":
                site_icon = "🔵"  # Blu come il logo di Immobiliare
            elif site_name == "Casa":
                site_icon = "🟠"  # Arancione come il logo di Casa.it
            
            # Contenuto dell'intestazione
            icon_label = tk.Label(header_frame, text=site_icon, font=("Helvetica", 16), bg="#f0f0f0")
            icon_label.pack(side=tk.LEFT, padx=10, pady=5)
            
            title_label = tk.Label(header_frame, text=prop.title, font=("Helvetica", 10, "bold"), 
                                bg="#f0f0f0", fg=self.link_color, anchor="w")
            title_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
            
            # Mostra l'URL nella barra di stato
            url_parts = prop.url.split("/")
            domain = url_parts[2] if len(url_parts) > 2 else prop.url
            url_label = tk.Label(status_frame, text=domain, bg="#f0f0f0", fg="#666666", font=("Helvetica", 8))
            url_label.pack(side=tk.LEFT, padx=5, pady=2)
            
            # Pulsanti nella barra di stato
            if persistent:
                btn_frame = tk.Frame(status_frame, bg="#f0f0f0")
                btn_frame.pack(side=tk.RIGHT, padx=5, pady=2)
                
                # Pulsante per aprire l'URL
                open_btn = tk.Button(btn_frame, text="Apri", font=("Helvetica", 9),
                                  bg=self.accent_color, fg="white", 
                                  width=8, height=1,
                                  activebackground=self.highlight_color,
                                  command=lambda: self.open_url(prop.url))
                open_btn.pack(side=tk.RIGHT, padx=2)
                
                # Pulsante per chiudere
                close_btn = tk.Button(btn_frame, text="Chiudi", font=("Helvetica", 9),
                                    bg=self.secondary_color, fg="black",
                                    width=8, height=1,
                                    command=self.close_image_popup)
                close_btn.pack(side=tk.RIGHT, padx=2)
            
            # Contenuto principale con immagine se disponibile
            if prop.image_url:
                try:
                    response = requests.get(prop.image_url, stream=True, timeout=5)
                    response.raise_for_status()
                    
                    # Crea l'immagine
                    img = Image.open(BytesIO(response.content))
                    
                    # Ridimensiona l'immagine per adattarla al layout
                    max_width, max_height = 150, 120
                    if img.width > max_width or img.height > max_height:
                        ratio = min(max_width / img.width, max_height / img.height)
                        new_width = int(img.width * ratio)
                        new_height = int(img.height * ratio)
                        img = img.resize((new_width, new_height), Image.LANCZOS)
                    
                    # Converti in formato Tkinter
                    thumb_photo = ImageTk.PhotoImage(img)
                    
                    # Mostra l'immagine
                    img_frame = tk.Frame(content_frame, bg="white", bd=1, relief=tk.SOLID)
                    img_frame.pack(side=tk.LEFT, padx=10, pady=10)
                    
                    img_label = tk.Label(img_frame, image=thumb_photo, bd=0)
                    img_label.image = thumb_photo  # Mantieni un riferimento
                    img_label.pack()
                except Exception as e:
                    logger.error(f"Errore nel caricare l'immagine anteprima: {e}")
            
            # Informazioni dell'immobile
            info_frame = tk.Frame(content_frame, bg="white")
            info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Prezzo
            price_frame = tk.Frame(info_frame, bg="white")
            price_frame.pack(fill=tk.X, pady=2, anchor="w")
            
            price_label_text = tk.Label(price_frame, text="Prezzo:", font=("Helvetica", 9), 
                                     bg="white", fg="#666666", width=10, anchor="w")
            price_label_text.pack(side=tk.LEFT)
            
            price_str = f"{prop.price:,d}€".replace(",", ".")
            price_label = tk.Label(price_frame, text=price_str, font=("Helvetica", 11, "bold"), 
                               bg="white", fg=self.price_color, anchor="w")
            price_label.pack(side=tk.LEFT)
            
            # Prezzo alternativo se presente
            if prop.alternate_price > 0:
                alt_price_frame = tk.Frame(info_frame, bg="white")
                alt_price_frame.pack(fill=tk.X, pady=2, anchor="w")
                
                alt_price_label_text = tk.Label(alt_price_frame, text="Prezzo Alt.:", font=("Helvetica", 9), 
                                            bg="white", fg="#666666", width=10, anchor="w")
                alt_price_label_text.pack(side=tk.LEFT)
                
                alt_price_str = f"{prop.alternate_price:,d}€".replace(",", ".")
                alt_price_label = tk.Label(alt_price_frame, text=alt_price_str, font=("Helvetica", 10), 
                                        bg="white", fg="#ff9900", anchor="w")
                alt_price_label.pack(side=tk.LEFT)
            
            # Valutazione se presente
            if prop.rating > 0:
                rating_frame = tk.Frame(info_frame, bg="white")
                rating_frame.pack(fill=tk.X, pady=2, anchor="w")
                
                rating_label_text = tk.Label(rating_frame, text="Valutazione:", font=("Helvetica", 9), 
                                         bg="white", fg="#666666", width=10, anchor="w")
                rating_label_text.pack(side=tk.LEFT)
                
                rating_text = self.rating_options[prop.rating]
                rating_color = self.rating_colors[prop.rating]
                
                rating_indicator = tk.Canvas(rating_frame, width=12, height=12, 
                                          bg="white", highlightthickness=0)
                rating_indicator.pack(side=tk.LEFT, padx=(0, 5))
                rating_indicator.create_oval(0, 0, 12, 12, fill=rating_color, outline="#666666")
                
                rating_label = tk.Label(rating_frame, text=rating_text, font=("Helvetica", 9), 
                                     bg="white", fg="#333333", anchor="w")
                rating_label.pack(side=tk.LEFT)
            
            # Note se presenti
            if prop.notes:
                notes_frame = tk.Frame(info_frame, bg="white")
                notes_frame.pack(fill=tk.X, pady=2, anchor="w")
                
                notes_label_text = tk.Label(notes_frame, text="Note:", font=("Helvetica", 9), 
                                         bg="white", fg="#666666", width=10, anchor="w")
                notes_label_text.pack(side=tk.LEFT, anchor="nw")
                
                # Mostra solo le prime 50 caratteri delle note
                note_text = prop.notes[:50] + ("..." if len(prop.notes) > 50 else "")
                notes_content = tk.Label(notes_frame, text=note_text, font=("Helvetica", 9), 
                                      bg="white", fg="#333333", anchor="w", wraplength=200,
                                      justify=tk.LEFT)
                notes_content.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Salva un riferimento al popup
            self.image_popup = popup
            
            # Avvia l'animazione di fade in
            self.animate_popup_fadein()
        
        except Exception as e:
            logger.error(f"Errore nel mostrare l'anteprima URL: {e}")

class TextHandler(logging.Handler):
    """Handler che reindirizza i log a un widget di testo"""
    def __init__(self, text_widget):
        logging.Handler.__init__(self)
        self.text_widget = text_widget
    
    def emit(self, record):
        msg = self.format(record)
        
        def append():
            self.text_widget.configure(state=tk.NORMAL)
            self.text_widget.insert(tk.END, msg + "\n")
            self.text_widget.configure(state=tk.DISABLED)
            self.text_widget.see(tk.END)  # Auto-scroll
        
        # Esegui l'update nel thread principale
        self.text_widget.after(0, append)

def main():
    root = tk.Tk()
    app = PriceTrackerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 