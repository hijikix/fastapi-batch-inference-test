import uuid

from locust import HttpUser, task


class LayoutUser(HttpUser):
    @task(0)
    def health(self) -> None:
        headers = {
            "Content-Type": "application/json",
        }
        data = {}
        self.client.post("/health", headers=headers, json=data)

    @task(0)
    def predict_one(self) -> None:
        headers = {
            "Content-Type": "application/json",
        }
        data = {"data": str(uuid.uuid4())}
        self.client.post("/predict_one", headers=headers, json=data)

    @task(1)
    def predict_batch(self) -> None:
        headers = {
            "Content-Type": "application/json",
        }
        data = {"data": str(uuid.uuid4())}
        self.client.post("/predict_batch", headers=headers, json=data)
