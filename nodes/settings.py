import os

from dotenv import load_dotenv

load_dotenv()

AGENT_TYPE: str = os.environ.get("AGENT_TYPE", "mock").lower()

GROQ_API_KEY: str | None = os.environ.get("GROQ_API_KEY")
HUGGINGFACE_API_TOKEN: str | None = os.environ.get("HUGGINGFACE_API_TOKEN")

SMOLAGENTS_MODEL_GROQ: str = os.environ.get("SMOLAGENTS_MODEL", "llama-3.3-70b-versatile")
SMOLAGENTS_MODEL_HF: str = os.environ.get("SMOLAGENTS_MODEL", "Qwen/Qwen2.5-72B-Instruct")
SMOLAGENTS_MODEL_OLLAMA: str = os.environ.get("SMOLAGENTS_MODEL", "qwen3:1.7b")

OLLAMA_BASE_URL: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
GROQ_BASE_URL: str = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

PYBULLET_GUI: bool = os.environ.get("PYBULLET_GUI", "0") == "1"

ROBOT_FIFO: str = os.environ.get("ROBOT_FIFO", "/tmp/dora-robot")
