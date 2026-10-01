FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY server.py accounts.py documents.py exchange.py safety_workflow.py study_operations.py wsgi.py ops.py ./
COPY public ./public
RUN useradd --uid 10001 --create-home anvaya && mkdir /app/data && chown anvaya:anvaya /app/data
USER anvaya
ENV CTMS_DB=/app/data/ctms.sqlite
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
EXPOSE 8046
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8046/api/health', timeout=3).read()"
CMD ["waitress-serve", "--listen=0.0.0.0:8046", "--threads=8", "--max-request-body-size=800000", "--trusted-proxy=172.30.46.2", "--trusted-proxy-headers=x-forwarded-for x-forwarded-proto", "--call", "wsgi:create_app"]
