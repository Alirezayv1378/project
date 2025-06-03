import os
import random

import locust

DJANGO_MANAGE = "docker-compose exec -i django-core python manage.py"

USERNAME = os.getenv("SUPER_ADMIN_USERNAME")
PASSWORD = os.getenv("SUPER_ADMIN_PASSWORD")

CUSTOMER_PHONE_NUMBERS = [
    "+989615990477",
    "+989493662581",
    "+989912988480",
    "+989377852994",
    "+989293210064",
    "+989601223192",
    "+989851881970",
    "+989619369189",
    "+989689272678",
    "+989889558497",
]

SELLER_PHONE_NUMBERS = ["+989486018480", "+989892512433"]


class APITestUser(locust.HttpUser):
    wait_time = locust.between(1, 3)

    def on_start(self):
        token = self.client.post("/api/v1/api-token-auth/", json={"username": USERNAME, "password": PASSWORD})
        self.client.headers = {"Authorization": f"Token {token.json()['token']}", "Content-Type": "application/json"}

    @locust.task(2)
    def list_users(self):
        self.client.get("/api/v1/users/")

    @locust.task(2)
    def list_charges(self):
        self.client.get("/api/v1/charges/")

    @locust.task(2)
    def list_transactions(self):
        self.client.get("/api/v1/transactions/")

    @locust.task(1)
    def create_charge(self):
        phone_number = random.choice(SELLER_PHONE_NUMBERS)  # noqa: S311
        amount = random.randint(100_000, 1_000_000)  # noqa: S311

        self.client.post(
            "/api/v1/charges/",
            json={
                "phone_number": phone_number,
                "amount": amount,
            },
        )

    @locust.task(10)
    def create_user_transaction(self):
        seller = random.choice(SELLER_PHONE_NUMBERS)  # noqa: S311
        receiver = random.choice(CUSTOMER_PHONE_NUMBERS)  # noqa: S311
        amount = random.randint(1, 10)  # noqa: S311

        self.client.post(
            "/api/v1/transactions/",
            json={
                "seller_phone_number": seller,
                "receiver_phone_number": receiver,
                "amount": amount,
            },
        )
