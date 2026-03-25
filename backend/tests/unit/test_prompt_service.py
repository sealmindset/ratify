"""Unit tests for the prompt service (cache, fallback, RFC type mapping)."""

import pytest

from app.services.prompt_service import (
    RFC_TYPE_SLUG_MAP,
    _CODE_DEFAULTS,
    _get_code_fallback,
    invalidate_cache,
    _cache,
)


class TestCodeDefaults:
    def test_all_rfc_types_have_defaults(self):
        for rfc_type, slug in RFC_TYPE_SLUG_MAP.items():
            fallback = _get_code_fallback(slug)
            assert fallback is not None, f"Missing default for {rfc_type} -> {slug}"
            content, model_key = fallback
            assert len(content) > 50, f"Default for {slug} is too short"
            assert model_key in ("standard", "heavy", "light")

    def test_suffix_exists(self):
        fallback = _get_code_fallback("rfc-interview-suffix")
        assert fallback is not None
        content, _ = fallback
        assert "INTERVIEW_COMPLETE" in content

    def test_section_generation_exists(self):
        fallback = _get_code_fallback("rfc-section-generation")
        assert fallback is not None
        _, model_key = fallback
        assert model_key == "heavy"

    def test_unknown_slug_returns_none(self):
        assert _get_code_fallback("nonexistent-slug") is None

    def test_all_interview_prompts_have_topics(self):
        for slug in RFC_TYPE_SLUG_MAP.values():
            content, _ = _CODE_DEFAULTS[slug]
            assert "TOPICS TO COVER" in content, f"{slug} missing TOPICS TO COVER"
            assert "ADAPTIVE RULES" in content, f"{slug} missing ADAPTIVE RULES"

    def test_all_interview_prompts_have_8_topics(self):
        for slug in RFC_TYPE_SLUG_MAP.values():
            content, _ = _CODE_DEFAULTS[slug]
            # Count numbered topic lines (1. through 8.)
            topic_count = sum(1 for i in range(1, 9) if f"{i}." in content)
            assert topic_count == 8, f"{slug} has {topic_count} topics, expected 8"


class TestRFCTypeMapping:
    def test_all_seven_types_mapped(self):
        expected_types = {"infrastructure", "security", "process", "architecture", "integration", "data", "other"}
        assert set(RFC_TYPE_SLUG_MAP.keys()) == expected_types

    def test_slugs_follow_naming_convention(self):
        for rfc_type, slug in RFC_TYPE_SLUG_MAP.items():
            assert slug == f"rfc-interview-{rfc_type}"


class TestCache:
    def test_invalidate_specific_slug(self):
        from app.services.prompt_service import CachedPrompt
        import time
        _cache["test-slug"] = CachedPrompt(content="test", model_key="standard", fetched_at=time.time())
        invalidate_cache("test-slug")
        assert "test-slug" not in _cache

    def test_invalidate_all(self):
        from app.services.prompt_service import CachedPrompt
        import time
        _cache["a"] = CachedPrompt(content="a", model_key="standard", fetched_at=time.time())
        _cache["b"] = CachedPrompt(content="b", model_key="standard", fetched_at=time.time())
        invalidate_cache()
        assert len(_cache) == 0

    def test_invalidate_nonexistent_slug_no_error(self):
        invalidate_cache("does-not-exist")
