import os

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")


class Agent(BaseModel):
    name: str = "Agent"
    model: str = "gpt-4o-mini"
    instructions: str = "You are a helpful Agent"
    tools: list = []
