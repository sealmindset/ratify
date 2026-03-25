"""Mock AI service for demo mode.

Provides realistic canned responses for the AI interview, section generation,
refinement, and comment assistance features. Used automatically when no AI
API credentials are configured.
"""

import json
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Interview question banks per RFC type
# Each bank is a list of (question, follow_up_context) tuples.
# The interviewer asks them in order, adapting the phrasing slightly.
# ---------------------------------------------------------------------------

_INTERVIEW_QUESTIONS: dict[str, list[str]] = {
    "infrastructure": [
        "Great, let's build this RFC together! First, can you describe the infrastructure component or system this RFC is about? What does it do today, and what needs to change?",
        "What's driving this change? Is it a scaling issue, a reliability concern, a migration, or something else?",
        "Let's talk about the current architecture. What compute, storage, and networking resources are involved today?",
        "What are the availability and DR requirements? Do you need multi-region, active-active, or is active-passive sufficient?",
        "How will this change affect monitoring and alerting? Are there specific SLAs or SLOs that need to be maintained?",
        "What's the rollback strategy if something goes wrong during the migration or rollout?",
        "Are there any cost implications? Have you estimated the infrastructure spend delta?",
        "Who are the stakeholders that need to sign off on this? Any compliance or security reviews required?",
    ],
    "security": [
        "Let's dive in! What's the security concern or improvement this RFC addresses? Give me the high-level picture.",
        "What's the threat model? Who are the potential adversaries and what are they after?",
        "How does authentication work today for the affected systems? What changes are you proposing?",
        "What about authorization? How are access controls structured, and what needs to change?",
        "Let's talk about data. What's the classification of the data involved, and what encryption is in place (at rest and in transit)?",
        "Are there compliance requirements driving this? SOC 2, HIPAA, PCI-DSS, or internal policies?",
        "How will this be audited? What logging and monitoring changes are needed?",
        "What's the rollout plan? Will this be phased, and how do you handle backward compatibility during transition?",
    ],
    "architecture": [
        "Exciting! Tell me about the system or component this RFC covers. What's the current state and what's the vision?",
        "What are the key problems with the current architecture that this RFC aims to solve?",
        "Walk me through the proposed architecture at a high level. What are the major components and how do they interact?",
        "What are the API contracts between these components? Any breaking changes to existing consumers?",
        "How does data flow through the system? What's the data model look like?",
        "What are the scalability requirements? Expected load, growth projections?",
        "What technologies are you proposing and why? What alternatives did you consider?",
        "What are the biggest risks and trade-offs with this approach?",
    ],
    "process": [
        "Let's map this out! What process are you looking to improve or introduce, and why now?",
        "Who are the people involved in this process today? Walk me through the current workflow.",
        "What are the biggest pain points? Where does the current process break down or slow things down?",
        "Describe the proposed new process. What does the ideal workflow look like?",
        "How will you measure success? What metrics or KPIs will tell you this is working?",
        "What training or change management is needed? How will people learn the new process?",
        "What's the rollout plan? Big bang or phased? Which teams go first?",
        "What happens if the new process doesn't work? What's the rollback plan?",
    ],
    "integration": [
        "Let's get into it! What systems are being integrated, and what's the business need driving this?",
        "Describe the data that needs to flow between these systems. What format, frequency, and volume?",
        "How does the integration work today (if at all)? What's the current pain?",
        "What's the proposed integration pattern? API-based, event-driven, batch ETL, or something else?",
        "How will you handle errors, retries, and dead letters? What about data consistency?",
        "What are the SLAs for this integration? How fast does data need to move?",
        "What monitoring and alerting will you put in place? How will you know when it's broken?",
        "Are there security considerations? How will authentication between systems work?",
    ],
    "data": [
        "Let's build this out! What data domain does this RFC cover, and what's changing?",
        "What are the data sources involved? Where does the data originate?",
        "Describe the proposed schema or data model changes. What entities and relationships are involved?",
        "What's the data pipeline look like? ETL, ELT, streaming, or a combination?",
        "How will data quality be ensured? Validation rules, deduplication, reconciliation?",
        "What about governance? Who owns this data, and what are the retention and access policies?",
        "What are the analytics or reporting requirements downstream?",
        "What are the risks? Data loss scenarios, privacy concerns, compliance implications?",
    ],
    "other": [
        "Sounds interesting! Tell me more about what this RFC proposes. What's the problem you're solving?",
        "What's the current state? How are things done today?",
        "Describe your proposed solution at a high level. What changes?",
        "What alternatives did you consider? Why is this approach better?",
        "What are the risks? What could go wrong?",
        "What's the timeline and who needs to be involved?",
        "How will you measure success? What does 'done' look like?",
        "Any dependencies or blockers that need to be resolved first?",
    ],
}

# After all questions are asked, we send the completion signal
_COMPLETION_MESSAGE = (
    "INTERVIEW_COMPLETE\n\n"
    "Excellent! I've gathered everything I need. Here's a summary of what we covered:\n\n"
    "- **Problem statement** and motivation for the change\n"
    "- **Current state** and what needs to improve\n"
    "- **Proposed solution** with technical details\n"
    "- **Risks, trade-offs, and mitigation strategies**\n"
    "- **Rollout plan** and success criteria\n\n"
    "I'm now generating your RFC sections based on our conversation..."
)


def _get_question_index(messages: list[dict]) -> int:
    """Count how many assistant messages have been sent (= question index)."""
    return sum(1 for m in messages if m["role"] == "assistant")


async def interview_next(messages_json: str, rfc_type: str, user_message: str) -> tuple[str, str]:
    """Return the next interview question or completion signal."""
    messages = json.loads(messages_json) if messages_json else []
    messages.append({"role": "user", "content": user_message})

    questions = _INTERVIEW_QUESTIONS.get(rfc_type, _INTERVIEW_QUESTIONS["other"])
    q_index = _get_question_index(messages)

    if q_index >= len(questions):
        # Interview complete
        response = _COMPLETION_MESSAGE
    else:
        response = questions[q_index]

    messages.append({"role": "assistant", "content": response})
    return json.dumps(messages), response


async def generate_sections(messages_json: str, rfc_type: str) -> list[dict]:
    """Generate realistic RFC sections from the interview conversation."""
    messages = json.loads(messages_json) if messages_json else []

    # Extract the title from the first user message
    title_hint = "the proposed changes"
    for m in messages:
        if m["role"] == "user" and "titled" in m["content"]:
            try:
                title_hint = m["content"].split("titled '")[1].split("'")[0]
            except (IndexError, KeyError):
                pass
            break

    # Collect user answers for context
    user_answers = [m["content"] for m in messages if m["role"] == "user"]
    # Use the first substantive answer as the problem statement
    problem = user_answers[1] if len(user_answers) > 1 else "Address critical gaps in the current system."
    solution = user_answers[2] if len(user_answers) > 2 else "Implement a modernized approach with best practices."

    sections = [
        {
            "title": "Purpose & Scope",
            "content": (
                f"## Purpose & Scope\n\n"
                f"This RFC proposes {title_hint.lower() if not title_hint[0].islower() else title_hint}. "
                f"The scope covers the end-to-end design, implementation plan, and rollout strategy.\n\n"
                f"### Problem Statement\n\n{problem}\n\n"
                f"### Goals\n\n"
                f"- Deliver a production-ready solution that addresses the identified gaps\n"
                f"- Minimize disruption to existing workflows during transition\n"
                f"- Establish clear metrics for measuring success"
            ),
            "section_type": "summary",
            "order": 1,
        },
        {
            "title": "Background",
            "content": (
                f"## Background\n\n"
                f"The current system has served us well but faces growing challenges. "
                f"As the organization scales, several limitations have become apparent:\n\n"
                f"- **Scalability constraints** that limit growth\n"
                f"- **Operational complexity** that increases toil\n"
                f"- **Technical debt** accumulated over multiple iterations\n\n"
                f"This RFC addresses these challenges with a structured approach."
            ),
            "section_type": "background",
            "order": 2,
        },
        {
            "title": "Architecture Overview",
            "content": (
                f"## Architecture Overview\n\n"
                f"### Proposed Solution\n\n{solution}\n\n"
                f"### Key Components\n\n"
                f"1. **Core Service Layer** -- Handles business logic and orchestration\n"
                f"2. **Data Layer** -- Manages persistence, caching, and data access patterns\n"
                f"3. **Integration Layer** -- Connects with external systems via well-defined contracts\n"
                f"4. **Observability** -- Logging, metrics, tracing, and alerting\n\n"
                f"### Data Flow\n\n"
                f"```\n"
                f"Client -> API Gateway -> Service Layer -> Data Layer -> Database\n"
                f"                                      -> Integration Layer -> External Systems\n"
                f"```"
            ),
            "section_type": "architecture",
            "order": 3,
        },
        {
            "title": "Security Considerations",
            "content": (
                f"## Security Considerations\n\n"
                f"- **Authentication**: All access via OIDC/OAuth 2.0 with MFA enforcement\n"
                f"- **Authorization**: Role-based access control with principle of least privilege\n"
                f"- **Data Protection**: TLS 1.3 in transit, AES-256 at rest\n"
                f"- **Audit Logging**: All state-changing operations logged with user context\n"
                f"- **Secrets Management**: All credentials in vault, rotated on schedule\n"
                f"- **Network Security**: Service mesh with mTLS between internal services"
            ),
            "section_type": "security",
            "order": 4,
        },
        {
            "title": "Implementation Plan",
            "content": (
                f"## Implementation Plan\n\n"
                f"### Phase 1: Foundation (Weeks 1-2)\n"
                f"- Set up infrastructure and CI/CD pipeline\n"
                f"- Implement core data model and migrations\n"
                f"- Establish observability baseline\n\n"
                f"### Phase 2: Core Features (Weeks 3-4)\n"
                f"- Build service layer with full test coverage\n"
                f"- Implement integration contracts\n"
                f"- Deploy to staging environment\n\n"
                f"### Phase 3: Hardening (Week 5)\n"
                f"- Load testing and performance optimization\n"
                f"- Security review and penetration testing\n"
                f"- Documentation and runbook creation\n\n"
                f"### Phase 4: Rollout (Week 6)\n"
                f"- Canary deployment to 10% of traffic\n"
                f"- Monitor for 48 hours, expand to 50%, then 100%\n"
                f"- Decommission legacy components"
            ),
            "section_type": "implementation",
            "order": 5,
        },
        {
            "title": "Risk Analysis",
            "content": (
                f"## Risk Analysis\n\n"
                f"| Risk | Impact | Likelihood | Mitigation |\n"
                f"|------|--------|-----------|------------|\n"
                f"| Data migration failure | High | Low | Dry-run migrations, automated rollback |\n"
                f"| Performance degradation | Medium | Medium | Load testing, canary deployment |\n"
                f"| Integration breaking changes | High | Low | Contract testing, versioned APIs |\n"
                f"| Team knowledge gaps | Medium | Medium | Pairing sessions, documentation |\n"
                f"| Timeline slip | Medium | Medium | Weekly checkpoints, MVP scope defined |"
            ),
            "section_type": "risk",
            "order": 6,
        },
        {
            "title": "Open Questions",
            "content": (
                f"## Open Questions\n\n"
                f"1. What is the acceptable downtime window for the migration cutover?\n"
                f"2. Are there upstream dependencies that need to be coordinated?\n"
                f"3. What is the budget allocation for additional infrastructure?\n"
                f"4. Do we need to maintain backward compatibility during the transition period?"
            ),
            "section_type": "body",
            "order": 7,
        },
        {
            "title": "Approval & Sign-Off",
            "content": (
                f"## Approval & Sign-Off\n\n"
                f"This RFC requires sign-off from the following teams:\n\n"
                f"- [ ] **Architecture** -- Design review and approval\n"
                f"- [ ] **Security** -- Security review and threat assessment\n"
                f"- [ ] **Engineering** -- Implementation feasibility and timeline\n"
                f"- [ ] **Operations** -- Operational readiness and runbook review"
            ),
            "section_type": "body",
            "order": 8,
        },
    ]

    logger.info(f"Mock AI generated {len(sections)} sections for RFC type '{rfc_type}'")
    return sections


async def refine_section(section_content: str, instruction: str) -> str:
    """Return a mock-refined version of a section."""
    return (
        f"{section_content}\n\n"
        f"---\n"
        f"*Refined based on feedback: {instruction}*\n\n"
        f"**Additional detail added by AI refinement:**\n\n"
        f"The above section has been expanded to address the requested changes. "
        f"Key improvements include more specific technical details, clearer success "
        f"criteria, and additional context for stakeholders.\n\n"
        f"*Note: This refinement was generated in demo mode. "
        f"Connect an AI provider for full AI-powered refinement.*"
    )


async def assist_comment_response(
    comment_content: str, section_content: str | None, instruction: str | None
) -> str:
    """Return a mock comment response suggestion."""
    response = (
        f"Thank you for this feedback. You raise an important point.\n\n"
    )

    if instruction:
        response += f"Regarding your suggestion to {instruction.lower()}, "
    else:
        response += "Regarding your comment, "

    response += (
        f"I've reviewed the relevant section and agree this warrants attention. "
        f"Here's my proposed approach:\n\n"
        f"1. **Acknowledge the concern** -- The current design does have this gap\n"
        f"2. **Proposed update** -- I'll revise the section to address this specifically\n"
        f"3. **Follow-up** -- Let's sync on whether the updated section meets your expectations\n\n"
        f"I'll update the RFC with these changes in the next revision."
    )

    if not section_content:
        response += (
            "\n\n*Note: This response was generated in demo mode. "
            "Connect an AI provider for context-aware responses.*"
        )

    return response
