FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt faker
COPY db/ db/
COPY backend/retrieval/ backend/retrieval/
COPY docker/init-entrypoint.sh init-entrypoint.sh
RUN chmod +x init-entrypoint.sh
ENTRYPOINT ["./init-entrypoint.sh"]
