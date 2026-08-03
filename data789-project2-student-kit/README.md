# Project 2 – Real-Time Fraud Detection System

## Overview

This project implements a real-time fraud detection system using Kafka, Redis, FastAPI, and Docker. Transaction events are streamed through Kafka, customer features are calculated in real time, and the API combines those features with the incoming transaction to produce a fraud prediction.

The system was containerized using Docker and includes a blue-green deployment demonstration using nginx.

---

## System Architecture

```
Transaction Simulator
        │
        ▼
      Kafka
        │
        ▼
Feature Processor
        │
        ▼
Redis Feature Store
        │
        ▼
 FastAPI Prediction API
        │
        ▼
 Fraud Prediction
```

The transaction simulator continuously publishes transactions to Kafka. The feature processor consumes those transactions and maintains rolling customer statistics in Redis. The FastAPI application retrieves the latest customer features and combines them with the incoming transaction before generating a fraud prediction.

---

## Technologies Used

- Python 3.11
- FastAPI
- Kafka
- Redis
- Docker
- Docker Compose
- nginx
- Uvicorn

---

# Setup

Clone the repository and generate the sample dataset.

```bash
cp .env.example .env

python data/generate_seed.py

python -m src.models.train
```

If no trained model exists, the API automatically falls back to the provided rule-based model.

---

# Running the System

Start the complete application stack.

```bash
docker compose up --build
```

The following services will be available.

| Service | Address |
|----------|----------|
| API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |
| Kafka | localhost:29092 |
| Redis | localhost:6379 |

---

# API

## Health Check

```
GET /health
```

Returns

```json
{
    "status": "ok"
}
```

---

## Predict Fraud

```
POST /predict
```

Example request

```json
{
    "transaction_id":"TXN-001",
    "customer_id":"CUST0001",
    "amount":1500,
    "merchant_category":"online_retail",
    "is_online":true,
    "timestamp":"2026-08-03T14:00:00Z"
}
```

Example response

```json
{
    "transaction_id":"TXN-001",
    "fraud_probability":0.8,
    "is_fraud":1,
    "model_version":"rule-based-fallback",
    "latency_ms":20.5
}
```

---

# Feature Store

Customer features are stored in Redis using the key format

```
features:{customer_id}
```

Each value contains a JSON document similar to

```json
{
    "transaction_count":119,
    "avg_amount":136.08
}
```

Each key is written with a configurable TTL so stale customer information automatically expires.

---

# Docker

The application uses a multi-stage Docker build.

Features include

- Multi-stage image
- Non-root runtime user
- Health check
- Slim runtime image
- Port 8000 exposed
- FastAPI served using Uvicorn

Build manually

```bash
docker build -t fraud-api .
```

Run

```bash
docker run --rm -p 8000:8000 fraud-api
```

---

# Running the Tests

Run all unit tests

```bash
pytest -q tests/
```

Expected result

```
7 passed
```

---

# Performance Testing

Run

```bash
python tests/test_performance.py --n 1000 --url http://localhost:8000
```

Final performance results

| Metric | Value |
|---------|------:|
| Requests | 1000 |
| Errors | 0 |
| Throughput | 193.6 requests/sec |
| p50 latency | 4.49 ms |
| p95 latency | 10.10 ms |
| p99 latency | 15.29 ms |
| Maximum latency | 24.68 ms |

The API was tested using two Uvicorn workers, which improved throughput and reduced tail latency compared to a single worker configuration.

---

# Blue-Green Deployment

Start the deployment stack

```bash
docker compose -f deployment/docker-compose.blue-green.yml up --build
```

Switch traffic

```bash
bash deployment/switch_traffic.sh
```

Stable endpoint

```
http://localhost:8080
```

Both API versions remain running throughout deployment. nginx switches traffic between the blue and green environments without dropping requests. Running the switch script a second time performs a rollback.

Further design details are documented in

```
docs/blue_green_design.md
```

---

# Repository Structure

```
src/
    api/
    models/
    streaming/

deployment/
    docker-compose.blue-green.yml
    switch_traffic.sh

docs/
    blue_green_design.md

tests/

Dockerfile

docker-compose.yml
```

---

# Project Summary

This project demonstrates a complete real-time fraud detection pipeline built with modern streaming technologies. Kafka provides event streaming, Redis serves as a low-latency feature store, FastAPI exposes prediction endpoints, Docker containerizes the application, and nginx enables blue-green deployments. The final system successfully passed all provided unit tests and supports live traffic switching without downtime.