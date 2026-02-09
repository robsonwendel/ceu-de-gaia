FROM python:3.11-slim
WORKDIR /app
# Instala dependências para o MySQL
RUN apt-get update && apt-get install -y gcc default-libmysqlclient-dev pkg-config && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn
COPY . .
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:5000", "app:app"]