# Price Tracker

Un'applicazione desktop per monitorare i prezzi degli immobili su vari siti web.

## Descrizione

Price Tracker è una semplice applicazione desktop che permette di monitorare i prezzi degli immobili nel tempo. Funziona con qualsiasi sito web di annunci immobiliari e tiene traccia delle variazioni di prezzo per aiutarti a prendere decisioni di acquisto informate.

## Funzionalità

- Aggiungi immobili da monitorare tramite URL
- Visualizza lo storico dei prezzi per ogni immobile
- Aggiorna i prezzi con un solo clic
- Monitora le variazioni percentuali e assolute
- Interfaccia semplice e intuitiva

## Requisiti

- Python 3.7+
- Librerie Python elencate in `requirements.txt`

## Installazione

1. Clona il repository:
```bash
git clone https://github.com/YourName/PriceTracker.git
cd PriceTracker
```

2. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

3. Avvia l'applicazione:
```bash
python main.py
```

## Come Usare

1. **Aggiungi un immobile**
   - Copia l'URL dell'annuncio immobiliare
   - Incollalo nell'apposito campo
   - Clicca su "Aggiungi"

2. **Aggiorna i prezzi**
   - Seleziona un immobile specifico o tutti
   - Clicca su "Aggiorna Selezionato" o "Aggiorna Tutti"

3. **Rimuovi un immobile**
   - Seleziona l'immobile dalla lista
   - Clicca su "Rimuovi"

## Struttura del Progetto

- `main.py`: Punto di ingresso dell'applicazione
- `PriceTracker.py`: Contiene la logica dell'applicazione e l'interfaccia grafica
- `extract_price.py`: Funzioni per l'estrazione dei prezzi dalle pagine web
- `data/`: Directory per il salvataggio dei dati

## Limitazioni

- L'estrazione dei prezzi potrebbe non funzionare su tutti i siti web
- Alcuni siti potrebbero limitare le richieste automatiche

## Licenza

MIT 