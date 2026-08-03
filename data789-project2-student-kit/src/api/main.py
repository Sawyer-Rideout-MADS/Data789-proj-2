"""
FastAPI serving app.

PROVIDED: app setup, model/feature-store load at startup, /health, /model/info,
and the request/response schemas (so input validation → HTTP 422 works for free).
YOU IMPLEMENT: the bodies of /predict and /predict_batch (graded: FastAPI Serving, 16 pts).
"""
from __future__ import annotations

import os
import time
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.api.fraud_detector import FraudDetector
from src.streaming.feature_store import FeatureStore

app = FastAPI(title="TrustBank Fraud Detection API")

# Loaded once at startup (do NOT load the model per-request).
detector = FraudDetector()
store = FeatureStore()


class Transaction(BaseModel):
    customer_id: str
    amount: float
    merchant_category: str
    is_online: bool
    timestamp: str
    transaction_id: Optional[str] = None


class FraudPrediction(BaseModel):
    transaction_id: Optional[str] = None
    fraud_probability: float
    is_fraud: int
    model_version: str
    latency_ms: float


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/model/info")
async def model_info():
    return {"model_version": detector.model_version}


@app.post("/predict", response_model=FraudPrediction)
async def predict_fraud(txn: Transaction):
    """Score a single transaction for fraud."""

    start_time = time.perf_counter()

    try:
        customer_features = store.get_customer_features(txn.customer_id)
    except Exception:
        # The API should still work when Redis is unavailable.
        customer_features = None

    if customer_features is None:
        customer_features = {
            "transaction_count": 0,
            "avg_amount": 0.0,
        }

    merged_features = {
        **txn.model_dump(),
        **customer_features,
    }

    prediction = detector.predict(merged_features)

    latency_ms = (time.perf_counter() - start_time) * 1000

    return FraudPrediction(
        transaction_id=txn.transaction_id,
        fraud_probability=prediction["fraud_probability"],
        is_fraud=prediction["is_fraud"],
        model_version=prediction["model_version"],
        latency_ms=round(latency_ms, 3),
    )


@app.post("/predict_batch", response_model=List[FraudPrediction])
async def predict_fraud_batch(txns: List[Transaction]):
    """Score multiple transactions using one batch feature-store lookup."""

    start_time = time.perf_counter()

    customer_ids = [txn.customer_id for txn in txns]

    try:
        batch_features = store.get_customer_features_batch(customer_ids)
    except Exception:
        batch_features = {
            customer_id: None
            for customer_id in customer_ids
        }

    predictions = []

    for txn in txns:
        customer_features = batch_features.get(txn.customer_id)

        if customer_features is None:
            customer_features = {
                "transaction_count": 0,
                "avg_amount": 0.0,
            }

        merged_features = {
            **txn.model_dump(),
            **customer_features,
        }

        prediction = detector.predict(merged_features)

        predictions.append(
            FraudPrediction(
                transaction_id=txn.transaction_id,
                fraud_probability=prediction["fraud_probability"],
                is_fraud=prediction["is_fraud"],
                model_version=prediction["model_version"],
                latency_ms=0.0,
            )
        )

    total_latency_ms = (time.perf_counter() - start_time) * 1000
    per_item_latency_ms = total_latency_ms / len(txns) if txns else 0.0

    for prediction in predictions:
        prediction.latency_ms = round(per_item_latency_ms, 3)

    return predictions