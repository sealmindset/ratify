"""Unit tests for the adaptive mock AI interview service."""

import json
import pytest

from app.services.mock_ai_service import (
    Topic,
    _build_coverage_state,
    _check_topic_coverage,
    _is_vague_answer,
    interview_next,
    generate_sections,
    refine_section,
    assist_comment_response,
)


class TestVagueAnswerDetection:
    def test_short_answer_is_vague(self):
        assert _is_vague_answer("yes") is True

    def test_not_sure_is_vague(self):
        assert _is_vague_answer("I'm not sure about that") is True

    def test_maybe_is_vague(self):
        assert _is_vague_answer("maybe") is True

    def test_substantive_answer_is_not_vague(self):
        answer = (
            "We currently have 3 servers running in AWS us-east-1, "
            "each with 8 cores and 32GB RAM. The primary bottleneck is disk I/O."
        )
        assert _is_vague_answer(answer) is False

    def test_empty_is_vague(self):
        assert _is_vague_answer("") is True

    def test_just_whitespace_is_vague(self):
        assert _is_vague_answer("   ") is True


class TestTopicCoverage:
    def test_no_keywords_no_coverage(self):
        topic = Topic(name="Test", question="q", keywords=["server", "cluster", "host"])
        assert _check_topic_coverage("hello world", topic) is False

    def test_one_keyword_not_enough(self):
        topic = Topic(name="Test", question="q", keywords=["server", "cluster", "host"])
        assert _check_topic_coverage("we have a server", topic) is False

    def test_two_keywords_is_covered(self):
        topic = Topic(name="Test", question="q", keywords=["server", "cluster", "host"])
        assert _check_topic_coverage("our server cluster handles 10k requests", topic) is True

    def test_case_insensitive(self):
        topic = Topic(name="Test", question="q", keywords=["server", "cluster"])
        assert _check_topic_coverage("Our SERVER CLUSTER is in AWS", topic) is True


class TestBuildCoverageState:
    def test_empty_messages_no_coverage(self):
        topics = [
            Topic(name="A", question="q1", keywords=["alpha", "beta"]),
            Topic(name="B", question="q2", keywords=["gamma", "delta"]),
        ]
        covered = _build_coverage_state([], topics)
        assert all(v is False for v in covered.values())

    def test_user_messages_drive_coverage(self):
        topics = [
            Topic(name="Infra", question="q1", keywords=["server", "cluster", "host"]),
            Topic(name="Cost", question="q2", keywords=["budget", "cost", "spend"]),
        ]
        messages = [
            {"role": "assistant", "content": "Tell me about your infrastructure"},
            {"role": "user", "content": "We have a server cluster with 5 hosts"},
        ]
        covered = _build_coverage_state(messages, topics)
        assert covered["Infra"] is True
        assert covered["Cost"] is False


class TestInterviewNext:
    @pytest.mark.asyncio
    async def test_first_message_returns_greeting(self):
        messages_json, response, covered, total, current = await interview_next(
            "[]", "architecture", "I want to create an RFC about microservices."
        )
        messages = json.loads(messages_json)
        # User message + assistant response
        assert len(messages) >= 2
        assert messages[-1]["role"] == "assistant"
        assert total == 8
        assert isinstance(covered, list)
        assert current is not None

    @pytest.mark.asyncio
    async def test_subsequent_message_advances(self):
        # Start the interview
        messages_json, _, _, _, _ = await interview_next(
            "[]", "infrastructure", "I want to discuss infrastructure changes."
        )
        # Continue with a substantive answer
        messages_json2, response2, covered2, total2, current2 = await interview_next(
            messages_json, "infrastructure",
            "We have a legacy server cluster with 20 VMs running on-premises. "
            "The current setup is 5 years old."
        )
        messages2 = json.loads(messages_json2)
        assert messages2[-1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_vague_answer_gets_followup(self):
        # Start interview
        messages_json, _, _, _, _ = await interview_next(
            "[]", "security", "I want to discuss a security concern."
        )
        # Give a vague answer
        messages_json2, response2, _, _, _ = await interview_next(
            messages_json, "security", "yes"
        )
        assert response2  # Should have content

    @pytest.mark.asyncio
    async def test_all_rfc_types_work(self):
        for rfc_type in ["infrastructure", "security", "process", "architecture", "integration", "data", "other"]:
            messages_json, response, covered, total, current = await interview_next(
                "[]", rfc_type, f"I want to discuss a {rfc_type} topic."
            )
            assert total == 8
            assert response
            assert current


class TestGenerateSections:
    @pytest.mark.asyncio
    async def test_returns_valid_sections(self):
        messages = json.dumps([
            {"role": "assistant", "content": "Tell me about the architecture"},
            {"role": "user", "content": "We want a microservices approach with API gateway"},
        ])
        sections = await generate_sections(messages, "architecture")
        assert isinstance(sections, list)
        assert len(sections) > 0
        for section in sections:
            assert "title" in section
            assert "content" in section
            assert "section_type" in section
            assert "order" in section


class TestRefineSection:
    @pytest.mark.asyncio
    async def test_returns_refined_text(self):
        result = await refine_section("This is rough content", "Make it more formal")
        assert isinstance(result, str)
        assert len(result) > 0


class TestAssistComment:
    @pytest.mark.asyncio
    async def test_returns_suggestion(self):
        result = await assist_comment_response("This approach has a security flaw", None, None)
        assert isinstance(result, str)
        assert len(result) > 0
