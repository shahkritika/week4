# Multi-stage production Dockerfile for Auth Service
FROM python:3.12-slim AS builder

WORKDIR /app

COPY Day21_Testing_and_Docker/auth_service/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.12-slim AS runner

WORKDIR /app

COPY --from=builder /root/.local /root/.local
COPY Day19_Microservices_Architecture/services/auth_service/ /app/Day19_Microservices_Architecture/services/auth_service/

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

EXPOSE 8001

HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD python -c "from urllib.request import urlopen; urlopen('http://localhost:8001/health')"

CMD ["uvicorn", "Day19_Microservices_Architecture.services.auth_service.main:app", "--host", "0.0.0.0", "--port", "8001"]

