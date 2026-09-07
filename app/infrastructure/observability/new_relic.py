import requests

from app.core.settings import settings


class NewRelicLogClient:
    def __init__(self) -> None:
        self.url = settings.new_relic_log_url

        self.headers = {
            "Api-Key": settings.NEW_RELIC_LICENSE_KEY,
            "Content-Type": "application/json",
        }

    def send(self, log: dict) -> None:
        response = requests.post(
            self.url,
            headers=self.headers,
            json=log,
            timeout=10,
        )

        response.raise_for_status()


new_relic_log_client = NewRelicLogClient()


