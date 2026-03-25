import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.middleware.permissions import require_permission
from app.models.managed_prompt import ManagedPrompt, ManagedPromptVersion
from app.schemas.auth import UserInfo
from app.schemas.prompt import (
    PromptDetailOut,
    PromptOut,
    PromptTestRequest,
    PromptTestResponse,
    PromptUpdate,
    PromptVersionOut,
)
from app.services.prompt_service import invalidate_cache

router = APIRouter(prefix="/api/admin/prompts", tags=["prompts"])


def _prompt_to_out(prompt: ManagedPrompt) -> PromptOut:
    return PromptOut(
        id=prompt.id,
        slug=prompt.slug,
        name=prompt.name,
        content=prompt.content,
        category=prompt.category,
        model_key=prompt.model_key,
        version=prompt.version,
        is_active=prompt.is_active,
        updated_by_name=prompt.updater.display_name if prompt.updater else None,
        created_at=prompt.created_at,
        updated_at=prompt.updated_at,
    )


def _version_to_out(v: ManagedPromptVersion) -> PromptVersionOut:
    return PromptVersionOut(
        id=v.id,
        version=v.version,
        content=v.content,
        change_summary=v.change_summary,
        changed_by_name=v.changer.display_name if v.changer else None,
        created_at=v.created_at,
    )


@router.get("/", response_model=list[PromptOut])
async def list_prompts(
    current_user: UserInfo = Depends(require_permission("admin.prompts", "read")),
    db: AsyncSession = Depends(get_db),
):
    """List all managed prompts."""
    result = await db.execute(
        select(ManagedPrompt).order_by(ManagedPrompt.category, ManagedPrompt.name)
    )
    return [_prompt_to_out(p) for p in result.scalars().all()]


@router.get("/{slug}", response_model=PromptDetailOut)
async def get_prompt(
    slug: str,
    current_user: UserInfo = Depends(require_permission("admin.prompts", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Get a prompt with its version history."""
    result = await db.execute(
        select(ManagedPrompt)
        .options(selectinload(ManagedPrompt.versions))
        .where(ManagedPrompt.slug == slug)
    )
    prompt = result.scalar_one_or_none()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    out = PromptDetailOut(
        **_prompt_to_out(prompt).model_dump(),
        versions=[_version_to_out(v) for v in prompt.versions],
    )
    return out


@router.put("/{slug}", response_model=PromptOut)
async def update_prompt(
    slug: str,
    data: PromptUpdate,
    current_user: UserInfo = Depends(require_permission("admin.prompts", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Update a prompt. Creates a new version in history."""
    result = await db.execute(
        select(ManagedPrompt).where(ManagedPrompt.slug == slug)
    )
    prompt = result.scalar_one_or_none()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Create version snapshot
    new_version = prompt.version + 1
    version = ManagedPromptVersion(
        prompt_id=prompt.id,
        content=data.content,
        version=new_version,
        change_summary=data.change_summary,
        changed_by=uuid.UUID(current_user.user_id),
    )
    db.add(version)

    # Update the prompt
    prompt.content = data.content
    prompt.version = new_version
    prompt.updated_by = uuid.UUID(current_user.user_id)

    await db.commit()
    await db.refresh(prompt)

    # Invalidate cache so next AI call picks up the new content
    invalidate_cache(slug)

    return _prompt_to_out(prompt)


@router.post("/{slug}/restore/{version_id}", response_model=PromptOut)
async def restore_prompt_version(
    slug: str,
    version_id: uuid.UUID,
    current_user: UserInfo = Depends(require_permission("admin.prompts", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Restore a prompt to a previous version."""
    result = await db.execute(
        select(ManagedPrompt).where(ManagedPrompt.slug == slug)
    )
    prompt = result.scalar_one_or_none()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    version_result = await db.execute(
        select(ManagedPromptVersion).where(
            ManagedPromptVersion.id == version_id,
            ManagedPromptVersion.prompt_id == prompt.id,
        )
    )
    old_version = version_result.scalar_one_or_none()
    if not old_version:
        raise HTTPException(status_code=404, detail="Version not found")

    # Create a new version recording the restore
    new_version_num = prompt.version + 1
    restore_version = ManagedPromptVersion(
        prompt_id=prompt.id,
        content=old_version.content,
        version=new_version_num,
        change_summary=f"Restored to version {old_version.version}",
        changed_by=uuid.UUID(current_user.user_id),
    )
    db.add(restore_version)

    prompt.content = old_version.content
    prompt.version = new_version_num
    prompt.updated_by = uuid.UUID(current_user.user_id)

    await db.commit()
    await db.refresh(prompt)

    invalidate_cache(slug)
    return _prompt_to_out(prompt)


@router.post("/{slug}/test", response_model=PromptTestResponse)
async def test_prompt(
    slug: str,
    data: PromptTestRequest,
    current_user: UserInfo = Depends(require_permission("admin.prompts", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Test a prompt with sample input (preview only, does not save)."""
    # Rough token estimate: ~4 chars per token
    token_estimate = len(data.content) // 4 + len(data.sample_input) // 4

    # Build a preview of what the AI would see
    preview = (
        f"=== SYSTEM PROMPT ===\n{data.content}\n\n"
        f"=== USER INPUT ===\n{data.sample_input}\n\n"
        f"=== ESTIMATED TOKENS ===\n{token_estimate}"
    )

    return PromptTestResponse(preview=preview, token_estimate=token_estimate)
