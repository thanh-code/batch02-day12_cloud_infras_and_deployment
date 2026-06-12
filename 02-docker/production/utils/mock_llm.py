"""Mock LLM for the Docker production demo."""
import random
import time


RESPONSES = {
    "docker": "Docker packages an app and its dependencies into a portable container.",
    "microservices": "Microservices split a system into independently deployable services.",
    "default": "This is a mock response from the Docker production agent.",
}


def ask(question: str, delay: float = 0.05) -> str:
    time.sleep(delay)
    lowered = question.lower()
    for keyword, response in RESPONSES.items():
        if keyword in lowered:
            return response
    return random.choice(list(RESPONSES.values()))
