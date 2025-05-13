FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH="${PYTHONPATH}:/app"

ENV API_PORT=8000
ENV MINION_DB_PATH="/app/minion/MinionCracker.db"

CMD ["python", "-m", "minion.MinionCracker"]