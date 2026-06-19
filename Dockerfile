FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema para psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do código
COPY . .

# Porta que o Railway usa
EXPOSE 8888

# Comando para rodar
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8888"]