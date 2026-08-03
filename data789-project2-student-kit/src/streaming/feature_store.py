"""
Feature Store (Redis) — YOU IMPLEMENT THE MARKED METHODS.

Contract (the provided tests in tests/test_feature_store.py depend on this):
  key layout     : "features:{customer_id}"  ->  JSON string of a features dict
  TTL            : every write expires after ttl_seconds
  batch retrieval: one round-trip (pipeline / MGET), not a loop of GETs

This is a graded deliverable (Redis Feature Store, 12 pts). The connection
setup is provided; the read/write logic is yours.
"""
from __future__ import annotations

import json
import os
from typing import Optional

import redis


class FeatureStore:
    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        password: str | None = None,
        ttl_seconds: int | None = None,
    ):
        self.ttl_seconds = ttl_seconds or int(os.getenv("FEATURE_TTL_SECONDS", "172800"))
        self.client = redis.Redis(
            host=host or os.getenv("REDIS_HOST", "localhost"),
            port=port or int(os.getenv("REDIS_PORT", "6379")),
            password=password or os.getenv("REDIS_PASSWORD") or None,
            decode_responses=True,
        )

    @staticmethod
    def _key(customer_id: str) -> str:
        return f"features:{customer_id}"

        # --- IMPLEMENT ---------------------------------------------------------
    def store_customer_features(self, customer_id: str, features: dict) -> None:
        """Serialize features to JSON and store them with an expiration."""
        key = self._key(customer_id)
        value = json.dumps(features)

        self.client.set(
            key,
            value,
            ex=self.ttl_seconds,
        )

    def get_customer_features(self, customer_id: str) -> Optional[dict]:
        """Return the customer's features, or None if the key is absent."""
        value = self.client.get(self._key(customer_id))

        if value is None:
            return None

        return json.loads(value)

    def get_customer_features_batch(self, customer_ids: list[str]) -> dict:
        """Retrieve several customers in one Redis round-trip."""
        keys = [self._key(customer_id) for customer_id in customer_ids]
        values = self.client.mget(keys)

        return {
            customer_id: json.loads(value) if value is not None else None
            for customer_id, value in zip(customer_ids, values)
        }
    # -----------------------------------------------------------------------

    def ttl(self, customer_id: str) -> int:
        """Remaining TTL in seconds (used by tests). -2 = no key, -1 = no expiry."""
        return self.client.ttl(self._key(customer_id))
