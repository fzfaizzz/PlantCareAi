FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080
WORKDIR /app
RUN groupadd --system plantcare && useradd --system --gid plantcare --home /app plantcare
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=plantcare:plantcare app ./app
COPY --chown=plantcare:plantcare models ./models
USER plantcare
EXPOSE 8080
CMD ["sh", "-c", "exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1 --timeout-keep-alive 5"]
