FROM python:3.9-slim

WORKDIR /app

# Dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code source
COPY . .

# CMD définie dans docker-compose.yaml
