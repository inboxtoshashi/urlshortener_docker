FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc default-libmysqlclient-dev python3-dev build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5001
CMD ["python", "app.py"]
