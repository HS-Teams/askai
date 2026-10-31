"""HTTP metadata client used by the Ollama speech provider."""

import requests


class OllamaClient:
    def __init__(self, base_url: str, timeout: float):
        self.base_url, self.timeout = base_url, timeout

    def request(self, endpoint: str, payload: dict | None = None) -> dict:
        try:
            response = requests.request(
                "GET" if payload is None else "POST",
                f"{self.base_url}/api/{endpoint}",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            result = response.json()
        except requests.ConnectionError as error:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.base_url}. Start `ollama serve`."
            ) from error
        except requests.HTTPError as error:
            raise RuntimeError(f"Ollama {endpoint}: {error.response.text}") from error
        except (requests.RequestException, ValueError) as error:
            raise RuntimeError(f"Ollama {endpoint} failed: {error}") from error
        if "error" in result:
            raise RuntimeError(f"Ollama {endpoint}: {result['error']}")
        return result

    def show(self, model: str) -> dict:
        return self.request("show", {"model": model})
