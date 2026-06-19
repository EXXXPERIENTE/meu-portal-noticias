FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código
COPY . .

# Porta do Railway
ENV PORT=8080
EXPOSE $PORT

# Comando: usa Gunicorn (servidor de produção)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]