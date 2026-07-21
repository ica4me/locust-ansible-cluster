from __future__ import annotations

import random
import uuid

from locust import FastHttpUser, between, task

AUTH_URL = "https://auth.poc.dcloud.biz.id"
CATALOG_URL = "https://catalog.poc.dcloud.biz.id"
CART_URL = "https://cart.poc.dcloud.biz.id"
CHECKOUT_URL = "https://checkout.poc.dcloud.biz.id"
ORDER_URL = "https://order.poc.dcloud.biz.id"


class CommerceUser(FastHttpUser):
    host = AUTH_URL
    wait_time = between(0.2, 1.0)
    connection_timeout = 5.0
    network_timeout = 10.0

    def on_start(self) -> None:
        self.user_id = f"user-{uuid.uuid4().hex[:12]}"
        self.token = ""
        self.cart_id = f"cart-{uuid.uuid4().hex[:12]}"
        self.checkout_id = ""
        self.login()

    def headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "X-Test-Run": "dbalance-logrotate-poc",
            "X-User-ID": self.user_id,
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def login(self) -> None:
        with self.client.post(
            f"{AUTH_URL}/api/auth/login",
            json={"username": self.user_id, "password": "poc-password"},
            headers=self.headers(),
            name="AUTH POST /api/auth/login",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Login failed: HTTP {response.status_code}")
                return
            try:
                self.token = response.json().get("access_token", "")
            except ValueError:
                response.failure("Login response is not valid JSON")

    @task(45)
    def browse_catalog(self) -> None:
        with self.client.get(
            f"{CATALOG_URL}/api/catalog/products",
            headers=self.headers(),
            name="CATALOG GET /api/catalog/products",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Catalog failed: HTTP {response.status_code}")

    @task(20)
    def product_detail(self) -> None:
        product_id = random.choice([101, 102, 103, 104])
        with self.client.get(
            f"{CATALOG_URL}/api/catalog/products/{product_id}",
            headers=self.headers(),
            name="CATALOG GET /api/catalog/products/[id]",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Product detail failed: HTTP {response.status_code}")

    @task(15)
    def add_to_cart(self) -> None:
        with self.client.post(
            f"{CART_URL}/api/cart/items",
            json={
                "cart_id": self.cart_id,
                "product_id": random.choice([101, 102, 103, 104]),
                "quantity": random.randint(1, 3),
            },
            headers=self.headers(),
            name="CART POST /api/cart/items",
            catch_response=True,
        ) as response:
            if response.status_code not in (200, 201):
                response.failure(f"Add cart failed: HTTP {response.status_code}")

    @task(8)
    def checkout(self) -> None:
        with self.client.post(
            f"{CHECKOUT_URL}/api/checkout",
            json={"cart_id": self.cart_id, "user_id": self.user_id},
            headers=self.headers(),
            name="CHECKOUT POST /api/checkout",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Checkout failed: HTTP {response.status_code}")
                return
            try:
                self.checkout_id = response.json().get(
                    "checkout_id", f"checkout-{uuid.uuid4().hex[:12]}"
                )
            except ValueError:
                response.failure("Checkout response is not valid JSON")

    @task(7)
    def create_order(self) -> None:
        checkout_id = self.checkout_id or f"checkout-{uuid.uuid4().hex[:12]}"
        with self.client.post(
            f"{ORDER_URL}/api/orders",
            json={"checkout_id": checkout_id, "user_id": self.user_id},
            headers=self.headers(),
            name="ORDER POST /api/orders",
            catch_response=True,
        ) as response:
            if response.status_code not in (200, 201):
                response.failure(f"Create order failed: HTTP {response.status_code}")
