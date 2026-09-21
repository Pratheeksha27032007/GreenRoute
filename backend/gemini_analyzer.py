import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import Literal


load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


class TaskRequirements(BaseModel):
    task_type: str
    complexity: Literal["low", "medium", "high"]
    recommended_accuracy: int
    urgency: Literal["low", "normal", "high"]
    can_be_delayed: bool


def analyze_task(task):

    prompt = f"""
Analyze this AI task for a workflow scheduler:

{task}

Classify the task based on its complexity, required accuracy,
urgency, and whether execution can be delayed.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=TaskRequirements,
            thinking_config=types.ThinkingConfig(
                thinking_level="minimal"
            )
        )
    )

    return TaskRequirements.model_validate_json(response.text)