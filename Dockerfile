FROM python:3.9-slim

WORKDIR /app

# Copia solo i file necessari
COPY requirements.txt .
COPY src/ ./src/

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Crea directory per i dati persistenti
RUN mkdir -p /app/data

# Imposta variabili di ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Comando di avvio
CMD ["python", "./src/estate_feeder.py"] 