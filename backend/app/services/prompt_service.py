"""Prompt service -- loads prompts from database with code fallback and caching.

DB-first: On each call, checks the database for the prompt by slug.
Cache: Keeps an in-memory cache with 60-second TTL to avoid repeated DB queries.
Fallback: If the prompt is not in the database (or DB is unreachable),
falls back to the hardcoded defaults in ai_service.py.
"""

import logging
import time
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.managed_prompt import ManagedPrompt

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 60


@dataclass
class CachedPrompt:
    content: str
    model_key: str
    fetched_at: float


_cache: dict[str, CachedPrompt] = {}


# Code fallback defaults -- identical to what was hardcoded in ai_service.py
_CODE_DEFAULTS: dict[str, tuple[str, str]] = {
    "rfc-interview-infrastructure": (
        "You are an expert infrastructure architect conducting an RFC interview. "
        "Focus on: network topology, compute sizing, storage, DR/failover, security zones, "
        "monitoring, SLAs, capacity planning, and migration strategy. "
        "Ask one question at a time. Adapt based on answers.",
        "standard",
    ),
    "rfc-interview-security": (
        "You are a security architect conducting an RFC interview. "
        "Focus on: threat model, authentication/authorization flows, data classification, "
        "encryption at rest and in transit, compliance requirements, audit logging, "
        "incident response, and vulnerability management. "
        "Ask one question at a time. Adapt based on answers.",
        "standard",
    ),
    "rfc-interview-process": (
        "You are a process improvement specialist conducting an RFC interview. "
        "Focus on: current pain points, stakeholders, RACI matrix, success metrics, "
        "rollout plan, training needs, rollback plan, and communication strategy. "
        "Ask one question at a time. Adapt based on answers.",
        "standard",
    ),
    "rfc-interview-architecture": (
        "You are a software architect conducting an RFC interview. "
        "Focus on: system boundaries, API contracts, data model, integration points, "
        "scalability, performance requirements, technology choices, and trade-offs. "
        "Ask one question at a time. Adapt based on answers.",
        "standard",
    ),
    "rfc-interview-integration": (
        "You are an integration specialist conducting an RFC interview. "
        "Focus on: source/target systems, data formats, transformation rules, "
        "error handling, retry policies, monitoring, SLAs, and rollback procedures. "
        "Ask one question at a time. Adapt based on answers.",
        "standard",
    ),
    "rfc-interview-data": (
        "You are a data architect conducting an RFC interview. "
        "Focus on: data sources, schema design, ETL/ELT pipelines, data quality, "
        "governance, retention policies, access controls, and analytics requirements. "
        "Ask one question at a time. Adapt based on answers.",
        "standard",
    ),
    "rfc-interview-other": (
        "You are a technical architect conducting an RFC interview. "
        "Ask questions to understand the proposal thoroughly: problem statement, "
        "proposed solution, alternatives considered, risks, timeline, and success criteria. "
        "Ask one question at a time. Adapt based on answers.",
        "standard",
    ),
    "rfc-interview-suffix": (
        "\n\nYou are interviewing someone to gather information for an RFC document. "
        "Ask focused, specific questions one at a time. When you have enough information "
        "to generate a comprehensive RFC (typically 8-15 questions), respond with exactly: "
        "INTERVIEW_COMPLETE followed by a brief summary of what you've learned.",
        "standard",
    ),
    "rfc-section-generation": (
        "Based on the interview conversation below, generate a comprehensive RFC document. "
        "Return a JSON array of sections, each with 'title', 'content' (in markdown), "
        "'section_type' (one of: summary, background, architecture, security, implementation, "
        "risk, timeline, appendix, body), and 'order' (integer starting from 1). "
        "Include these sections at minimum: Purpose & Scope, Background, Architecture Overview, "
        "Security Considerations, Implementation Plan, Risk Analysis, Open Questions, "
        "and Approval & Sign-Off. Adapt sections based on the RFC type. "
        "Return ONLY valid JSON, no other text.",
        "heavy",
    ),
    "rfc-section-refinement": (
        "You are a technical writing assistant helping refine RFC documents.",
        "standard",
    ),
    "rfc-comment-assistance": (
        "You are helping an RFC author respond to reviewer feedback constructively.",
        "light",
    ),
}

# Mapping from RFC type name to prompt slug
RFC_TYPE_SLUG_MAP = {
    "infrastructure": "rfc-interview-infrastructure",
    "security": "rfc-interview-security",
    "process": "rfc-interview-process",
    "architecture": "rfc-interview-architecture",
    "integration": "rfc-interview-integration",
    "data": "rfc-interview-data",
    "other": "rfc-interview-other",
}


def _get_code_fallback(slug: str) -> tuple[str, str] | None:
    return _CODE_DEFAULTS.get(slug)


async def get_prompt(slug: str, db: AsyncSession) -> tuple[str, str]:
    """Get prompt content and model_key by slug.

    Returns (content, model_key). Checks cache first, then DB, then code fallback.
    """
    now = time.time()

    # Check cache
    cached = _cache.get(slug)
    if cached and (now - cached.fetched_at) < CACHE_TTL_SECONDS:
        return cached.content, cached.model_key

    # Try database
    try:
        result = await db.execute(
            select(ManagedPrompt).where(ManagedPrompt.slug == slug, ManagedPrompt.is_active == True)  # noqa: E712
        )
        prompt = result.scalar_one_or_none()
        if prompt:
            _cache[slug] = CachedPrompt(
                content=prompt.content,
                model_key=prompt.model_key,
                fetched_at=now,
            )
            return prompt.content, prompt.model_key
    except Exception as e:
        logger.warning(f"Failed to load prompt '{slug}' from DB, using fallback: {e}")

    # Code fallback
    fallback = _get_code_fallback(slug)
    if fallback:
        _cache[slug] = CachedPrompt(content=fallback[0], model_key=fallback[1], fetched_at=now)
        return fallback

    # Unknown slug
    logger.error(f"No prompt found for slug '{slug}' in DB or code defaults")
    return ("You are a helpful assistant.", "standard")


async def get_interview_prompt(rfc_type: str, db: AsyncSession) -> str:
    """Get the full interview system prompt for an RFC type (base + suffix)."""
    slug = RFC_TYPE_SLUG_MAP.get(rfc_type, "rfc-interview-other")
    base_content, _ = await get_prompt(slug, db)
    suffix_content, _ = await get_prompt("rfc-interview-suffix", db)
    return base_content + suffix_content


def invalidate_cache(slug: str | None = None) -> None:
    """Clear cache for a specific slug, or all if None."""
    if slug:
        _cache.pop(slug, None)
    else:
        _cache.clear()
