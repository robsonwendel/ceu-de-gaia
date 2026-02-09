# 1. Usa uma imagem oficial do Python otimizada (slim) para ocupar menos espaço na VPS
FROM python:3.11-slim

# 2. Define o diretório de trabalho dentro do container
WORKDIR /app

# 3. Instala dependências do sistema necessárias para o conector do MySQL
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 4. Copia apenas o arquivo de requisitos primeiro (otimiza o cache do Docker)
COPY requirements.txt .

# 5. Instala as bibliotecas do Python e o Gunicorn para produção
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# 6. Copia todo o restante do código do projeto para dentro do container
COPY . .

# 7. Informa ao Easypanel que a aplicação escuta na porta 5000
EXPOSE 5000

# 8. Comando para iniciar a aplicação com Gunicorn (3 workers para melhor performance)
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:5000", "app:app"]