import random

import locust

CUSTOMER_PHONE_NUMBERS = [
    "+989535399420",
    "+989354097915",
    "+989220966742",
    "+989832388980",
    "+989356916286",
    "+989740500163",
    "+989795247643",
    "+989247353531",
    "+989058336430",
    "+989127550483",
]


SELLER_PHONE_NUMBERS = [
    "+989097907343",
    "+989203016403",
    "+989004562348",
    "+989020026132",
    "+989058336430",
    "+989080879790",
]


class APITestUser(locust.HttpUser):
    wait_time = locust.between(0.01, 0.1)

    def on_start(self):
        self.phone_number = random.choice(SELLER_PHONE_NUMBERS)  # noqa: S311
        self.get_token()

    def get_token(self):
        response = self.client.post(
            "/api/v1/token/",
            json={"username": self.phone_number, "password": self.phone_number},
            name="/api/v1/token/",
        )
        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access")
            self.refresh_token = data.get("refresh")
            self.set_auth_header()
        else:
            response.failure("Login failed")

    def refresh_token_and_retry(self, method, url, **kwargs):
        refresh_response = self.client.post(
            "/api/v1/token/refresh/",
            json={"refresh": self.refresh_token},
            name="/api/v1/token/refresh/",
        )
        if refresh_response.status_code == 200:
            self.access_token = refresh_response.json().get("access")
            self.set_auth_header()
            return method(url, **kwargs)
        else:
            refresh_response.failure("Token refresh failed")
            self.get_token()
            return method(url, **kwargs)

    def set_auth_header(self):
        self.client.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def safe_get(self, url, **kwargs):
        response = self.client.get(url, **kwargs)
        if response.status_code == 401:
            return self.refresh_token_and_retry(self.client.get, url, **kwargs)
        return response

    def safe_post(self, url, **kwargs):
        response = self.client.post(url, **kwargs)
        if response.status_code == 401:
            return self.refresh_token_and_retry(self.client.post, url, **kwargs)
        return response

    @locust.task(2)
    def list_users(self):
        self.safe_get("/api/v1/users/", name="/api/v1/users/")

    @locust.task(2)
    def list_charges(self):
        self.safe_get("/api/v1/charges/", name="/api/v1/charges/")

    @locust.task(2)
    def list_transactions(self):
        self.safe_get("/api/v1/transactions/", name="/api/v1/transactions/")

    @locust.task(1)
    def create_charge(self):
        amount = random.randint(100_000, 1_000_000)  # noqa: S311
        self.safe_post(
            "/api/v1/charges/",
            json={"phone_number": self.phone_number, "amount": amount},
            name="/api/v1/charges/",
        )

    @locust.task(10)
    def create_user_transaction(self):
        receiver = random.choice(CUSTOMER_PHONE_NUMBERS)  # noqa: S311
        amount = random.randint(1, 10)  # noqa: S311
        self.safe_post(
            "/api/v1/transactions/",
            json={
                "seller_phone_number": self.phone_number,
                "receiver_phone_number": receiver,
                "amount": amount,
            },
            name="/api/v1/transactions/",
        )
