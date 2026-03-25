import json
import logging

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.prompt_service import get_prompt, get_interview_prompt, RFC_TYPE_SLUG_MAP

logger = logging.getLogger(__name__)


def _ai_configured() -> bool:
    """Return True if real AI credentials are present."""
    return bool(settings.AZURE_AI_FOUNDRY_ENDPOINT and settings.AZURE_AI_FOUNDRY_API_KEY)


def _get_api_url(model_key: str) -> tuple[str, dict[str, str], str]:
    """Return (url, headers, model_name) for the configured AI provider."""
    model_map = {
        "heavy": settings.AI_MODEL_HEAVY,
        "standard": settings.AI_MODEL_STANDARD,
        "light": settings.AI_MODEL_LIGHT,
    }
    model = model_map.get(model_key, settings.AI_MODEL_STANDARD)

    if settings.AI_PROVIDER == "anthropic_foundry":
        base = settings.AZURE_AI_FOUNDRY_ENDPOINT.rstrip("/")
        return (
            f"{base}/anthropic/v1/messages",
            {
                "api-key": settings.AZURE_AI_FOUNDRY_API_KEY,
                "Content-Type": "application/json",
            },
            model,
        )
    else:
        # Direct Anthropic fallback
        return (
            "https://api.anthropic.com/v1/messages",
            {
                "x-api-key": settings.AZURE_AI_FOUNDRY_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            model,
        )


async def chat(messages: list[dict], system: str, model_key: str = "standard") -> str:
    """Send a chat request to the AI provider."""
    url, headers, model = _get_api_url(model_key)

    payload = {
        "model": model,
        "max_tokens": 4096,
        "system": system,
        "messages": messages,
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            # Anthropic Messages API format
            return data["content"][0]["text"]
    except Exception as e:
        logger.error(f"AI service error: {e}")
        # Return a helpful fallback
        return (
            "I'm having trouble connecting to the AI service right now. "
            "Please check your AI provider configuration in the environment settings."
        )


async def interview_next(
    messages_json: str, rfc_type: str, user_message: str, db: AsyncSession
) -> tuple[str, str]:
    """Continue an interview conversation and return the AI's next question."""
    if not _ai_configured():
        from app.services.mock_ai_service import interview_next as mock_interview
        return await mock_interview(messages_json, rfc_type, user_message)

    messages = json.loads(messages_json) if messages_json else []
    messages.append({"role": "user", "content": user_message})

    system = await get_interview_prompt(rfc_type, db)

    response = await chat(messages, system, model_key="standard")
    messages.append({"role": "assistant", "content": response})
    return json.dumps(messages), response


async def generate_sections(
    messages_json: str, rfc_type: str, db: AsyncSession
) -> list[dict]:
    """Generate RFC sections from the interview conversation."""
    if not _ai_configured():
        from app.services.mock_ai_service import generate_sections as mock_gen
        return await mock_gen(messages_json, rfc_type)

    messages = json.loads(messages_json) if messages_json else []

    section_prompt, _ = await get_prompt("rfc-section-generation", db)
    messages.append({"role": "user", "content": section_prompt})

    slug = RFC_TYPE_SLUG_MAP.get(rfc_type, "rfc-interview-other")
    type_prompt, _ = await get_prompt(slug, db)
    response = await chat(messages, type_prompt, model_key="heavy")

    try:
        # Try to parse JSON from the response
        clean = response.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(clean)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse sections JSON: {response[:200]}")
        return [
            {
                "title": "Generated Content",
                "content": response,
                "section_type": "body",
                "order": 1,
            }
        ]


async def refine_section(
    section_content: str, instruction: str, db: AsyncSession
) -> str:
    """Refine an RFC section based on user instruction."""
    if not _ai_configured():
        from app.services.mock_ai_service import refine_section as mock_refine
        return await mock_refine(section_content, instruction)

    messages = [
        {
            "role": "user",
            "content": (
                f"Here is the current RFC section content:\n\n{section_content}\n\n"
                f"Please refine it based on this instruction: {instruction}\n\n"
                "Return only the updated content in markdown format."
            ),
        }
    ]
    system, model_key = await get_prompt("rfc-section-refinement", db)
    return await chat(messages, system, model_key=model_key)


async def assist_comment_response(
    comment_content: str, section_content: str | None, instruction: str | None,
    db: AsyncSession
) -> str:
    """Help the RFC author draft a response to a reviewer comment."""
    if not _ai_configured():
        from app.services.mock_ai_service import assist_comment_response as mock_assist
        return await mock_assist(comment_content, section_content, instruction)

    prompt = f"A reviewer left this comment on an RFC:\n\n{comment_content}\n\n"
    if section_content:
        prompt += f"The relevant section content is:\n\n{section_content}\n\n"
    if instruction:
        prompt += f"The author wants to: {instruction}\n\n"
    prompt += "Draft a thoughtful response that addresses the reviewer's concerns."

    messages = [{"role": "user", "content": prompt}]
    system, model_key = await get_prompt("rfc-comment-assistance", db)
    return await chat(messages, system, model_key=model_key)
