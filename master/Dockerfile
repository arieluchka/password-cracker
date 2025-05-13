FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH="${PYTHONPATH}:/app"

ENV DEFAULT_IP="0.0.0.0"
ENV DEFAULT_PORT=8080
ENV HEALTH_CHECK_INTERVAL=10
ENV SET_MINION_TO_UNAVAILABLE_AFTER_HEALTH_CHECK=5
ENV MAX_FAILED_HEALTH_CHECKS=0
ENV PASSWORDS_PER_JOB=100000
ENV JOB_SCAN_INTERVAL=30
ENV JOB_ASSIGNMENT_INTERVAL=30

RUN chmod +x /app/master/start.sh


CMD ["/app/master/start.sh"]

# ENTRYPOINT ["python", "master/MasterCracker.py", "&"]
# CMD ["python", "master/cli.py"]