FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app
WORKDIR ${APP_HOME}
RUN useradd --create-home --shell /usr/sbin/nologin worker
COPY worker/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY worker/app ./app
USER worker
CMD ["python", "-m", "app.main"]
