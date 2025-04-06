# Price Tracker

Un'applicazione desktop per il monitoraggio dei prezzi di immobili da diverse sorgenti online.

## Funzionalità

- Monitoraggio dei prezzi di immobili da diverse fonti web
- Visualizzazione dello storico dei prezzi per ogni immobile
- Sistema di rating personale per gli immobili (mi piace, neutro, non mi piace)
- Possibilità di aggiungere note personali per ogni immobile
- Visualizzazione dell'immagine dell'immobile
- Importazione di URL da file Excel o testo
- Possibilità di importare più URL contemporaneamente
- Esportazione dei dati in formato Excel

## Requisiti

- Python 3.6+
- Librerie richieste:
  - tkinter (incluso in Python)
  - requests
  - beautifulsoup4
  - pandas
  - pillow (PIL)
  - lxml
  - pyinstaller (solo per creare l'eseguibile)

## Installazione

1. Clona questo repository:

```bash
git clone https://github.com/tuonome/PriceTracker.git
cd PriceTracker
```

2. Installa le dipendenze:

```bash
pip install -r requirements.txt
```

## Utilizzo

Avvia l'applicazione:

```bash
cd src
python main.py
```

### Funzionalità principali

- **Aggiungi URL**: Inserisci l'URL di un annuncio immobiliare per monitorarne il prezzo
- **Importa**: Importa più URL da un file Excel o da un testo
- **Aggiorna**: Aggiorna i prezzi di tutti gli immobili monitorati
- **Rating**: Assegna un rating personale agli immobili (mi piace, neutro, non mi piace)
- **Note**: Aggiungi note personali per ogni immobile
- **Prezzo alternativo**: Registra un prezzo alternativo se quello rilevato automaticamente non è corretto

## Creazione dell'eseguibile

Per creare un file eseguibile (.exe) che può essere avviato con un doppio clic senza necessità di aprire Python:

### Metodo semplice (automatico)

1. Fai doppio clic sul file `crea_eseguibile.bat` nella cartella principale
2. Segui le istruzioni a schermo
3. Una volta completato, troverai l'eseguibile nella cartella `dist`
4. Puoi scegliere di creare un collegamento sul desktop

### Metodo manuale

1. Assicurati di aver installato i requisiti:
```bash
pip install -r requirements.txt
```

2. Esegui lo script di setup:
```bash
python setup.py
```

3. L'eseguibile sarà creato nella cartella `dist`

## Privacy

Nessun dato personale viene condiviso. Tutti i dati sono memorizzati localmente nel file `properties.json`.

## Contribuire

I contributi sono benvenuti! Se vuoi contribuire al progetto:

1. Crea un fork del repository
2. Crea un branch per la tua feature (`git checkout -b feature/NuovaFeature`)
3. Commit dei tuoi cambiamenti (`git commit -m 'Aggiunta nuova feature'`)
4. Push al branch (`git push origin feature/NuovaFeature`)
5. Apri una Pull Request

## Licenza

[MIT](LICENSE) 