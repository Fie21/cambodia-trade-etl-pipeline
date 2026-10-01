FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY dashboard/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --default-timeout=1000 --retries 10 --prefer-binary -r /app/requirements.txt

COPY dashboard/ /app/
COPY src/ /app/src/

EXPOSE 8501 8502

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || curl --fail http://localhost:8502/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run"]
CMD ["app_business.py", "--server.port=8501", "--server.address=0.0.0.0"]
