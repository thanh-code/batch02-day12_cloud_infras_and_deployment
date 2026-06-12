"""Local mock LLM so the final lab can run without external API keys."""
import random
import time


MOCK_RESPONSES = {
    "default": [
        "This is a mock AI response. In production, this would come from a real LLM provider.",
        "The production agent is online and ready to answer deployment questions.",
        "Your question was received by the cloud-ready AI agent.",
    ],
    "docker": [
        "Docker packages the app, dependencies, and runtime into a reproducible container.",
    ],
    "deploy": [
        "Deployment moves the agent from a local machine to a public cloud runtime such as Render.",
    ],
    "render": [
        "Render can deploy this Dockerized agent from render.yaml and connect it to Render Key Value.",
    ],
    "health": [
        "Health checks let the platform know the process is alive; readiness checks gate traffic.",
    ],
}


def ask(question: str, delay: float = 0.05) -> str:
    time.sleep(delay + random.uniform(0, 0.03))
    question_lower = question.lower()
    for keyword, responses in MOCK_RESPONSES.items():
        if keyword in question_lower:
            return random.choice(responses)
    return random.choice(MOCK_RESPONSES["default"])
