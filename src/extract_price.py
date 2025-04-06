#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import logging
from bs4 import BeautifulSoup

# Configurazione logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("price_extractor")

def extract_price(text):
    """
    Estrae il prezzo da un testo contenente cifre e simboli di valuta
    
    Args:
        text (str): Il testo contenente il prezzo (es. "€ 150.000", "150.000 €")
        
    Returns:
        int: Il prezzo estratto come intero, 0 se non trovato
    """
    if not text:
        return 0
    
    # Pattern più specifici per i prezzi
    price_patterns = [
        # Euro con punto come separatore migliaia
        r'(?:€|EUR|euro)\s*(\d{1,3}(?:\.\d{3})+(?:,\d+)?)',
        r'(\d{1,3}(?:\.\d{3})+(?:,\d+)?)\s*(?:€|EUR|euro)',
        # Euro con virgola come separatore migliaia
        r'(?:€|EUR|euro)\s*(\d{1,3}(?:,\d{3})+(?:\.\d+)?)',
        r'(\d{1,3}(?:,\d{3})+(?:\.\d+)?)\s*(?:€|EUR|euro)',
        # Prezzo senza separatore migliaia
        r'(?:€|EUR|euro)\s*(\d{4,10})',
        r'(\d{4,10})\s*(?:€|EUR|euro)',
        # In contesto "prezzo: 100.000€"
        r'prezzo\s*(?::|è|di)?\s*(?:€|EUR|euro)?\s*(\d{1,3}(?:[.,]\d{3})+|\d{4,10})\s*(?:€|EUR|euro)?',
        r'(?:vendita|affitto|richiesti)\s*(?:a|:)?\s*(?:€|EUR|euro)?\s*(\d{1,3}(?:[.,]\d{3})+|\d{4,10})\s*(?:€|EUR|euro)?'
    ]
    
    # Prova tutti i pattern
    for pattern in price_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            price_str = match.group(1)
            try:
                # Normalizza il prezzo rimuovendo separatori migliaia
                price_str = price_str.replace(".", "").replace(",", "")
                price = int(price_str)
                if is_valid_property_price(price):
                    return price
            except (ValueError, AttributeError):
                continue
    
    # Pattern generico di fallback (meno preciso, usato solo se gli altri falliscono)
    try:
        # Cerca numeri con almeno 4 cifre (presumibilmente sono prezzi)
        numbers = re.findall(r'(\d{4,10})', text)
        for num in numbers:
            price = int(num)
            if is_valid_property_price(price):
                return price
    except (ValueError, AttributeError):
        pass
        
    return 0

def is_valid_property_price(price):
    """
    Verifica se un prezzo sembra plausibile per un immobile
    
    Args:
        price (int): Il prezzo da verificare
        
    Returns:
        bool: True se il prezzo sembra valido, False altrimenti
    """
    # Prezzi tipici per immobili in Italia (da adattare al mercato locale)
    min_price = 10000  # 10.000€ - sotto questo valore è probabilmente un errore
    max_price = 10000000  # 10.000.000€ - sopra questo valore è probabilmente un errore
    
    return min_price <= price <= max_price

def extract_price_from_html(html_snippet):
    """
    Estrae il prezzo da un frammento HTML utilizzando vari metodi
    
    Args:
        html_snippet (str): Il codice HTML da cui estrarre il prezzo
        
    Returns:
        int: Il prezzo estratto come intero, 0 se non trovato
    """
    # Lista di candidati prezzi trovati
    price_candidates = []
    
    # 1. Cerca nei meta tag (più affidabili)
    soup = BeautifulSoup(html_snippet, "html.parser")
    meta_tags = soup.select('meta[property="product:price:amount"], meta[property="og:price:amount"], meta[itemprop="price"]')
    for tag in meta_tags:
        if tag.has_attr("content"):
            try:
                price_str = tag["content"].replace(".", "").replace(",", "")
                price = int(price_str)
                if is_valid_property_price(price):
                    price_candidates.append((price, 10)) # Alta affidabilità
            except (ValueError, AttributeError):
                pass
    
    # 2. Cerca nei markup strutturati
    price_elements = soup.select('[itemprop="price"], .price, .Price, .listing-price, .property-price, .product-price')
    for elem in price_elements:
        try:
            text = elem.text.strip()
            price = extract_price(text)
            if price > 0:
                price_candidates.append((price, 8)) # Buona affidabilità
        except:
            pass
    
    # 3. Cerca elementi con nomi di classe che contengono "price" o "prezzo"
    price_classes = soup.select('[class*="price" i], [class*="prezzo" i], [id*="price" i], [id*="prezzo" i]')
    for elem in price_classes:
        try:
            text = elem.text.strip()
            price = extract_price(text)
            if price > 0:
                price_candidates.append((price, 6)) # Media affidabilità
        except:
            pass
    
    # 4. Cerca pattern regex nel testo HTML (vari formati)
    patterns = [
        # Pattern comuni per prezzi in euro
        r'(\d{1,3}(?:\.\d{3})+|\d{4,10})(?:\s*€)',
        r'€\s*(\d{1,3}(?:\.\d{3})+|\d{4,10})',
        # Pattern specifici per JSON/data attributes
        r'"price"\s*:\s*"?(\d+(?:\.\d+)?)"?',
        r'"prezzo"\s*:\s*"?(\d+(?:\.\d+)?)"?',
        r'data-price="(\d+(?:\.\d+)?)"',
        # Pattern specifici per display di prezzo
        r'class="[^"]*price[^"]*"[^>]*>([0-9.,]+)',
        r'id="[^"]*price[^"]*"[^>]*>([0-9.,]+)'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html_snippet, re.IGNORECASE)
        if matches:
            for match in matches:
                try:
                    price_str = match.replace(".", "").replace(",", "")
                    price = int(price_str)
                    if is_valid_property_price(price):
                        price_candidates.append((price, 4)) # Bassa affidabilità
                except (ValueError, AttributeError):
                    continue
    
    # 5. Fallback: estrai da tutto il testo visibile (solo se non abbiamo trovato nulla finora)
    if not price_candidates:
        try:
            visible_text = soup.get_text()
            price = extract_price(visible_text)
            if price > 0:
                price_candidates.append((price, 2)) # Molto bassa affidabilità
        except:
            pass
    
    # Analizza i candidati e scegli il prezzo più probabile
    if price_candidates:
        # Ordina per affidabilità, poi per valore (in caso di parità di affidabilità)
        price_candidates.sort(key=lambda x: (-x[1], x[0]))
        
        # Prendi il candidato più affidabile
        return price_candidates[0][0]
    
    return 0

def extract_surface(text):
    """
    Estrae la superficie in metri quadrati da un testo
    
    Args:
        text (str): Il testo contenente l'indicazione della superficie
        
    Returns:
        float: La superficie in metri quadrati, 0 se non trovata
    """
    if not text:
        return 0
        
    # Cerca un pattern numerico seguito da m²
    match = re.search(r'(\d+[.,]?\d*)\s*m(?:q|²|2)', text.lower())
    if match:
        value = match.group(1).replace(",", ".")
        try:
            return float(value)
        except ValueError:
            pass
    
    # Cerca la parola "superficie" o "metratura" seguita da un numero
    match = re.search(r'(?:superficie|metratura|area|dimensione)[:\s]+(\d+[.,]?\d*)', text.lower())
    if match:
        value = match.group(1).replace(",", ".")
        try:
            return float(value)
        except ValueError:
            pass
    
    # Altrimenti cerca solo numeri (meno affidabile)
    match = re.search(r'(\d+[.,]?\d*)', text)
    if match:
        value = match.group(1).replace(",", ".")
        try:
            return float(value)
        except ValueError:
            pass
            
    return 0

def extract_rooms(text):
    """
    Estrae il numero di locali da un testo
    
    Args:
        text (str): Il testo contenente l'indicazione dei locali
        
    Returns:
        int: Il numero di locali, 0 se non trovato
    """
    if not text:
        return 0
        
    # Cerca parole chiave come "locali" o "vani" o "camere"
    match = re.search(r'(\d+)\s*(local[ei]|van[io]|rooms?|stanz[ae]|camer[ae])', text.lower())
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass
    
    # Altrimenti cerca solo numeri (meno affidabile)
    match = re.search(r'(\d+)', text)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass
            
    return 0

# Funzione di test
if __name__ == "__main__":
    # Test con diversi formati di prezzo
    test_strings = [
        "€ 150.000", 
        "150.000 €",
        "€150.000", 
        "150.000€",
        "150000 EUR",
        "Prezzo: 150.000 euro",
        "Prezzo € 250000",
        "Richiesti € 320.000",
        "In vendita a 180000 €",
        "Appartamento in vendita a 290.500 euro",
        "Prezzo trattabile di 450.000 euro"
    ]
    
    for test in test_strings:
        price = extract_price(test)
        print(f"Input: '{test}' -> Prezzo estratto: {price}€")
        
    # Test con snippet HTML
    html_test = '<div class="price">€ 180.000</div>'
    price = extract_price_from_html(html_test)
    print(f"\nDa HTML: {html_test} -> Prezzo estratto: {price}€") 