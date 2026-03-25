"""Mock AI service for demo mode.

Provides adaptive, topic-aware interview responses for the AI interview,
section generation, refinement, and comment assistance features. Used
automatically when no AI API credentials are configured.

The adaptive engine:
- Tracks which topics the user has already addressed
- Skips questions for covered topics
- Asks follow-up probes when answers are vague or too short
- Returns topic coverage metadata for the frontend progress indicator
"""

import json
import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Topic definitions per RFC type
# Each topic has: name, question, keywords that indicate coverage, and
# follow-up probes for vague answers.
# ---------------------------------------------------------------------------


@dataclass
class Topic:
    name: str
    question: str
    keywords: list[str]
    follow_ups: list[str] = field(default_factory=list)


_TOPICS: dict[str, list[Topic]] = {
    "infrastructure": [
        Topic(
            name="Current State",
            question="Can you describe the infrastructure component or system this RFC is about? What does it do today, and what needs to change?",
            keywords=["server", "cluster", "host", "vm", "instance", "container", "current", "today", "existing", "legacy", "running"],
            follow_ups=[
                "Can you be more specific about the current setup? What infrastructure components exist today?",
                "How many servers or instances are involved? What does the current topology look like?",
            ],
        ),
        Topic(
            name="Motivation",
            question="What's driving this change? Is it a scaling issue, a reliability concern, a migration, or something else?",
            keywords=["scale", "reliab", "migrat", "performance", "cost", "outage", "bottleneck", "growth", "demand", "capacity", "latency"],
            follow_ups=[
                "What's the business impact of not making this change? Have there been any incidents?",
                "How urgent is this? What happens if we wait 6 months?",
            ],
        ),
        Topic(
            name="Architecture",
            question="Let's talk about the proposed architecture. What compute, storage, and networking resources will be needed?",
            keywords=["compute", "storage", "network", "vpc", "subnet", "load balanc", "database", "cache", "cdn", "firewall", "kubernetes", "docker"],
            follow_ups=[
                "What about the networking layer? Are there VPCs, subnets, or load balancers involved?",
                "How will data be stored? What database or storage services are you planning?",
            ],
        ),
        Topic(
            name="Availability & DR",
            question="What are the availability and disaster recovery requirements? Multi-region, active-active, or active-passive?",
            keywords=["availab", "disaster", "recovery", "failover", "replica", "backup", "region", "active-active", "active-passive", "rto", "rpo", "uptime", "sla"],
            follow_ups=[
                "What's the target uptime? 99.9%? 99.99%? What's the acceptable recovery time?",
                "How will failover work? Automatic or manual? What's the recovery point objective?",
            ],
        ),
        Topic(
            name="Monitoring & SLAs",
            question="How will this change affect monitoring and alerting? Are there specific SLAs or SLOs that need to be maintained?",
            keywords=["monitor", "alert", "metric", "sla", "slo", "sli", "observab", "log", "trace", "dashboard", "pager", "on-call"],
            follow_ups=[
                "What metrics will you track to know this is healthy? Any specific thresholds?",
                "Who gets paged when something goes wrong? What's the alerting chain?",
            ],
        ),
        Topic(
            name="Rollback Strategy",
            question="What's the rollback strategy if something goes wrong during the migration or rollout?",
            keywords=["rollback", "revert", "fallback", "rollout", "canary", "blue-green", "phased", "cutover", "downtime"],
            follow_ups=[
                "Can you roll back instantly, or does it require a maintenance window?",
                "Will this be a big-bang cutover or a phased rollout?",
            ],
        ),
        Topic(
            name="Cost Impact",
            question="Are there cost implications? Have you estimated the infrastructure spend delta?",
            keywords=["cost", "budget", "spend", "saving", "price", "billing", "estimate", "roi", "tco"],
            follow_ups=[
                "Roughly what's the monthly cost difference? Is there a cost optimization opportunity?",
                "Has finance signed off on the budget for this?",
            ],
        ),
        Topic(
            name="Stakeholders",
            question="Who are the stakeholders that need to sign off on this? Any compliance or security reviews required?",
            keywords=["stakeholder", "sign-off", "approv", "complian", "security review", "audit", "team", "owner", "sponsor"],
            follow_ups=[
                "Are there any compliance frameworks that apply? SOC 2, HIPAA, PCI?",
                "Which teams need to review this before it can proceed?",
            ],
        ),
    ],
    "security": [
        Topic(
            name="Security Concern",
            question="What's the security concern or improvement this RFC addresses? Give me the high-level picture.",
            keywords=["vulnerab", "threat", "risk", "breach", "attack", "exploit", "patch", "harden", "secure", "protect"],
            follow_ups=[
                "Is this addressing a specific vulnerability, or is it a proactive improvement?",
                "Has there been an incident or audit finding that's driving this?",
            ],
        ),
        Topic(
            name="Threat Model",
            question="What's the threat model? Who are the potential adversaries and what are they after?",
            keywords=["threat model", "adversar", "attacker", "actor", "vector", "surface", "asset", "target", "insider", "external"],
            follow_ups=[
                "Are we worried about external attackers, insider threats, or both?",
                "What's the most valuable asset at risk? What's the worst-case scenario?",
            ],
        ),
        Topic(
            name="Authentication",
            question="How does authentication work today for the affected systems? What changes are you proposing?",
            keywords=["authen", "login", "sso", "oidc", "oauth", "mfa", "password", "credential", "identity", "token", "saml"],
            follow_ups=[
                "Is MFA enforced? What identity provider is in use?",
                "Are there service-to-service authentication needs as well?",
            ],
        ),
        Topic(
            name="Authorization",
            question="What about authorization? How are access controls structured, and what needs to change?",
            keywords=["authoriz", "rbac", "role", "permission", "access control", "privilege", "least privilege", "policy", "scope"],
            follow_ups=[
                "Is this role-based, attribute-based, or something else?",
                "Are you following the principle of least privilege? How granular are the controls?",
            ],
        ),
        Topic(
            name="Data Protection",
            question="What's the classification of the data involved, and what encryption is in place (at rest and in transit)?",
            keywords=["encrypt", "data class", "pii", "phi", "sensitive", "confidential", "tls", "ssl", "aes", "at rest", "in transit", "mask"],
            follow_ups=[
                "What encryption standards are used? TLS version? Key management approach?",
                "Is there any PII or PHI involved? How is it handled?",
            ],
        ),
        Topic(
            name="Compliance",
            question="Are there compliance requirements driving this? SOC 2, HIPAA, PCI-DSS, or internal policies?",
            keywords=["complian", "soc", "hipaa", "pci", "gdpr", "regulation", "framework", "standard", "audit", "certif"],
            follow_ups=[
                "Which specific controls or requirements does this address?",
                "When is the next audit? Is this a blocker for certification?",
            ],
        ),
        Topic(
            name="Audit & Monitoring",
            question="How will this be audited? What logging and monitoring changes are needed?",
            keywords=["audit", "log", "monitor", "siem", "alert", "detect", "incident", "forensic", "trace"],
            follow_ups=[
                "Are security events being sent to a SIEM? What's the retention policy?",
                "Is there an incident response plan that needs updating?",
            ],
        ),
        Topic(
            name="Rollout Plan",
            question="What's the rollout plan? Will this be phased, and how do you handle backward compatibility during transition?",
            keywords=["rollout", "phase", "migration", "backward", "compat", "transition", "timeline", "pilot"],
            follow_ups=[
                "How will you test this before production? Is there a staging environment?",
                "What's the rollback plan if the security change causes issues?",
            ],
        ),
    ],
    "architecture": [
        Topic(
            name="Current State & Vision",
            question="Tell me about the system or component this RFC covers. What's the current state and what's the vision?",
            keywords=["current", "today", "existing", "vision", "goal", "target", "future", "state", "system"],
            follow_ups=[
                "What specific pain points exist with the current architecture?",
                "What does the ideal end state look like?",
            ],
        ),
        Topic(
            name="Problem Statement",
            question="What are the key problems with the current architecture that this RFC aims to solve?",
            keywords=["problem", "issue", "challenge", "bottleneck", "limitation", "pain point", "technical debt", "coupling"],
            follow_ups=[
                "How are these problems impacting development velocity or reliability?",
                "Which problem is the most critical to solve first?",
            ],
        ),
        Topic(
            name="Proposed Architecture",
            question="Walk me through the proposed architecture at a high level. What are the major components and how do they interact?",
            keywords=["component", "service", "module", "layer", "microservice", "monolith", "event", "queue", "api gateway", "diagram"],
            follow_ups=[
                "How many services or components are involved? What's the communication pattern?",
                "Is this a microservices, modular monolith, or hybrid approach?",
            ],
        ),
        Topic(
            name="API Contracts",
            question="What are the API contracts between these components? Any breaking changes to existing consumers?",
            keywords=["api", "contract", "endpoint", "rest", "graphql", "grpc", "schema", "version", "breaking change", "consumer"],
            follow_ups=[
                "How will you version the APIs? What's the deprecation strategy?",
                "How many existing consumers need to be updated?",
            ],
        ),
        Topic(
            name="Data Model",
            question="How does data flow through the system? What's the data model look like?",
            keywords=["data", "model", "schema", "database", "table", "entity", "relation", "flow", "pipeline", "event sourcing"],
            follow_ups=[
                "Are there any data migration needs? How will existing data be handled?",
                "What's the consistency model? Strong consistency or eventual?",
            ],
        ),
        Topic(
            name="Scalability",
            question="What are the scalability requirements? Expected load, growth projections?",
            keywords=["scale", "load", "throughput", "latency", "performance", "concurrent", "rps", "growth", "capacity", "horizontal", "vertical"],
            follow_ups=[
                "What's the expected request volume? Any seasonal spikes?",
                "Where are the potential bottlenecks under load?",
            ],
        ),
        Topic(
            name="Technology Choices",
            question="What technologies are you proposing and why? What alternatives did you consider?",
            keywords=["technolog", "framework", "language", "tool", "library", "platform", "alternative", "comparison", "trade-off", "evaluation"],
            follow_ups=[
                "What criteria did you use to evaluate alternatives?",
                "Does the team have experience with the proposed tech stack?",
            ],
        ),
        Topic(
            name="Risks & Trade-offs",
            question="What are the biggest risks and trade-offs with this approach?",
            keywords=["risk", "trade-off", "concern", "downside", "complex", "debt", "maintenance", "mitigation"],
            follow_ups=[
                "What's the mitigation strategy for each risk?",
                "What's the worst case if a risk materializes?",
            ],
        ),
    ],
    "process": [
        Topic(
            name="Process Overview",
            question="What process are you looking to improve or introduce, and why now?",
            keywords=["process", "workflow", "procedure", "practice", "method", "approach", "initiative"],
            follow_ups=[
                "What triggered the need for this change? A specific incident or gradual pain?",
                "How long has the current process been in place?",
            ],
        ),
        Topic(
            name="Current Participants",
            question="Who are the people involved in this process today? Walk me through the current workflow.",
            keywords=["team", "role", "person", "department", "stakeholder", "responsible", "accountable", "workflow", "step"],
            follow_ups=[
                "How many people are involved end-to-end? Are there handoff points that cause delays?",
                "Is there a RACI matrix for the current process?",
            ],
        ),
        Topic(
            name="Pain Points",
            question="What are the biggest pain points? Where does the current process break down or slow things down?",
            keywords=["pain", "slow", "bottleneck", "error", "manual", "friction", "frustrat", "delay", "waste", "rework"],
            follow_ups=[
                "Can you quantify the impact? Hours lost per week, error rates, cycle time?",
                "What's the most frustrating part for the people doing the work?",
            ],
        ),
        Topic(
            name="Proposed Process",
            question="Describe the proposed new process. What does the ideal workflow look like?",
            keywords=["proposed", "new", "ideal", "improved", "automat", "streamline", "simplif", "redesign"],
            follow_ups=[
                "What specific steps change? Which stay the same?",
                "Is there any automation involved in the new process?",
            ],
        ),
        Topic(
            name="Success Metrics",
            question="How will you measure success? What metrics or KPIs will tell you this is working?",
            keywords=["metric", "kpi", "measure", "success", "indicator", "target", "goal", "benchmark", "improve"],
            follow_ups=[
                "What's the baseline today for these metrics?",
                "What's the target improvement? 50%? 2x?",
            ],
        ),
        Topic(
            name="Change Management",
            question="What training or change management is needed? How will people learn the new process?",
            keywords=["training", "change management", "adopt", "learn", "onboard", "document", "communicat", "resistance"],
            follow_ups=[
                "Are there people who might resist this change? How will you bring them along?",
                "What documentation or training materials are needed?",
            ],
        ),
        Topic(
            name="Rollout Plan",
            question="What's the rollout plan? Big bang or phased? Which teams go first?",
            keywords=["rollout", "phase", "pilot", "timeline", "schedule", "milestone", "launch", "deploy"],
            follow_ups=[
                "Is there a pilot group? How will you validate before rolling out broadly?",
                "What's the timeline? Weeks? Months?",
            ],
        ),
        Topic(
            name="Rollback & Contingency",
            question="What happens if the new process doesn't work? What's the contingency plan?",
            keywords=["rollback", "fallback", "contingency", "fail", "revert", "backup plan", "risk"],
            follow_ups=[
                "Can you revert to the old process if needed? How quickly?",
                "What are the warning signs that the new process isn't working?",
            ],
        ),
    ],
    "integration": [
        Topic(
            name="Systems & Business Need",
            question="What systems are being integrated, and what's the business need driving this?",
            keywords=["system", "application", "platform", "service", "connect", "integrate", "business", "need", "require"],
            follow_ups=[
                "What are the specific systems involved? Name them.",
                "What business process does this integration enable?",
            ],
        ),
        Topic(
            name="Data Specification",
            question="Describe the data that needs to flow between these systems. What format, frequency, and volume?",
            keywords=["data", "format", "json", "xml", "csv", "volume", "frequency", "batch", "real-time", "record", "field", "payload"],
            follow_ups=[
                "What's the expected volume? Records per day? MB per hour?",
                "Is this real-time, near-real-time, or batch?",
            ],
        ),
        Topic(
            name="Current State",
            question="How does the integration work today (if at all)? What's the current pain?",
            keywords=["current", "today", "existing", "manual", "workaround", "pain", "gap", "broken"],
            follow_ups=[
                "Is there any manual data transfer happening today?",
                "What breaks most often with the current approach?",
            ],
        ),
        Topic(
            name="Integration Pattern",
            question="What's the proposed integration pattern? API-based, event-driven, batch ETL, or something else?",
            keywords=["pattern", "api", "event", "message", "queue", "webhook", "polling", "etl", "elt", "stream", "kafka", "rabbit"],
            follow_ups=[
                "Why this pattern over alternatives? What constraints drove the choice?",
                "Will this be synchronous or asynchronous?",
            ],
        ),
        Topic(
            name="Error Handling",
            question="How will you handle errors, retries, and dead letters? What about data consistency?",
            keywords=["error", "retry", "dead letter", "failure", "exception", "consistency", "idempoten", "duplicate", "reconcil"],
            follow_ups=[
                "What happens when the target system is down? Is there a retry policy?",
                "How will you detect and handle duplicate records?",
            ],
        ),
        Topic(
            name="SLAs & Performance",
            question="What are the SLAs for this integration? How fast does data need to move?",
            keywords=["sla", "latency", "throughput", "performance", "speed", "delay", "timeout", "deadline"],
            follow_ups=[
                "What's the acceptable end-to-end latency?",
                "What happens if the SLA is breached? Is there an escalation path?",
            ],
        ),
        Topic(
            name="Monitoring",
            question="What monitoring and alerting will you put in place? How will you know when it's broken?",
            keywords=["monitor", "alert", "dashboard", "health check", "observab", "log", "metric", "incident"],
            follow_ups=[
                "Who gets notified when the integration fails?",
                "What dashboards or metrics will you track?",
            ],
        ),
        Topic(
            name="Security",
            question="Are there security considerations? How will authentication between systems work?",
            keywords=["security", "auth", "token", "certificate", "encrypt", "api key", "oauth", "credential", "secret"],
            follow_ups=[
                "How will credentials be managed? Rotated?",
                "Is data encrypted in transit between systems?",
            ],
        ),
    ],
    "data": [
        Topic(
            name="Data Domain",
            question="What data domain does this RFC cover, and what's changing?",
            keywords=["domain", "dataset", "data", "change", "scope", "area", "subject"],
            follow_ups=[
                "What's the scope? One dataset, a whole domain, or cross-domain?",
                "What specifically is changing about the data?",
            ],
        ),
        Topic(
            name="Data Sources",
            question="What are the data sources involved? Where does the data originate?",
            keywords=["source", "origin", "upstream", "feed", "input", "ingest", "produce", "generate"],
            follow_ups=[
                "How many sources are involved? Are they internal or external?",
                "How reliable are these sources? What's the data quality like?",
            ],
        ),
        Topic(
            name="Schema & Data Model",
            question="Describe the proposed schema or data model changes. What entities and relationships are involved?",
            keywords=["schema", "model", "entity", "table", "column", "field", "relation", "normali", "denormali"],
            follow_ups=[
                "Is this a new schema or changes to an existing one? Any breaking changes?",
                "How will existing data be migrated to the new schema?",
            ],
        ),
        Topic(
            name="Data Pipeline",
            question="What's the data pipeline look like? ETL, ELT, streaming, or a combination?",
            keywords=["pipeline", "etl", "elt", "stream", "transform", "load", "extract", "batch", "schedule", "orchestrat"],
            follow_ups=[
                "What tools or platforms will the pipeline use?",
                "How often does data need to be processed? Real-time or scheduled?",
            ],
        ),
        Topic(
            name="Data Quality",
            question="How will data quality be ensured? Validation rules, deduplication, reconciliation?",
            keywords=["quality", "valid", "deduplic", "reconcil", "clean", "accurate", "complete", "consistent"],
            follow_ups=[
                "What validation rules are needed? Who defines them?",
                "How will you detect and handle bad data?",
            ],
        ),
        Topic(
            name="Governance & Ownership",
            question="What about governance? Who owns this data, and what are the retention and access policies?",
            keywords=["governance", "owner", "steward", "retention", "access", "policy", "catalog", "lineage", "classif"],
            follow_ups=[
                "Is there a data catalog entry for this? What's the retention period?",
                "Who can access this data? Are there restrictions?",
            ],
        ),
        Topic(
            name="Analytics & Reporting",
            question="What are the analytics or reporting requirements downstream?",
            keywords=["analytics", "report", "dashboard", "bi", "insight", "visualization", "consumer", "downstream"],
            follow_ups=[
                "Who are the downstream consumers? What reports or dashboards use this data?",
                "Are there latency requirements for reporting?",
            ],
        ),
        Topic(
            name="Risks",
            question="What are the risks? Data loss scenarios, privacy concerns, compliance implications?",
            keywords=["risk", "loss", "privacy", "pii", "complian", "gdpr", "breach", "backup", "recovery"],
            follow_ups=[
                "Is there PII or sensitive data involved? How is it protected?",
                "What's the backup and recovery strategy for this data?",
            ],
        ),
    ],
    "other": [
        Topic(
            name="Problem Statement",
            question="Tell me more about what this RFC proposes. What's the problem you're solving?",
            keywords=["problem", "issue", "challenge", "gap", "need", "concern", "opportunity"],
            follow_ups=[
                "Who is affected by this problem? How big is the impact?",
                "How long has this been a problem?",
            ],
        ),
        Topic(
            name="Current State",
            question="What's the current state? How are things done today?",
            keywords=["current", "today", "existing", "status quo", "manual", "workaround"],
            follow_ups=[
                "What works well about the current approach? What doesn't?",
                "Is there a temporary workaround in place?",
            ],
        ),
        Topic(
            name="Proposed Solution",
            question="Describe your proposed solution at a high level. What changes?",
            keywords=["solution", "proposal", "approach", "plan", "design", "implement", "build", "change"],
            follow_ups=[
                "Can you break the solution into concrete steps?",
                "What does the end state look like?",
            ],
        ),
        Topic(
            name="Alternatives",
            question="What alternatives did you consider? Why is this approach better?",
            keywords=["alternative", "option", "compare", "versus", "trade-off", "instead", "other approach"],
            follow_ups=[
                "What was the second-best option? Why did you rule it out?",
                "What are the trade-offs with your chosen approach?",
            ],
        ),
        Topic(
            name="Risks",
            question="What are the risks? What could go wrong?",
            keywords=["risk", "concern", "failure", "worst case", "mitigat", "issue", "danger"],
            follow_ups=[
                "What's the worst-case scenario? How would you recover?",
                "What's your mitigation strategy for each risk?",
            ],
        ),
        Topic(
            name="Timeline & People",
            question="What's the timeline and who needs to be involved?",
            keywords=["timeline", "schedule", "deadline", "team", "resource", "people", "who", "when", "milestone"],
            follow_ups=[
                "What's the target completion date? Are there dependencies?",
                "How many people are needed? From which teams?",
            ],
        ),
        Topic(
            name="Success Criteria",
            question="How will you measure success? What does 'done' look like?",
            keywords=["success", "metric", "done", "complete", "criteria", "measure", "kpi", "outcome"],
            follow_ups=[
                "What specific metrics will you track?",
                "How will you know if this was worth doing?",
            ],
        ),
        Topic(
            name="Dependencies",
            question="Any dependencies or blockers that need to be resolved first?",
            keywords=["depend", "blocker", "prerequisite", "blocked", "waiting", "upstream", "need first"],
            follow_ups=[
                "Are there any external dependencies outside your team's control?",
                "What's the critical path?",
            ],
        ),
    ],
}

# Minimum answer length (characters) to consider an answer substantive
_MIN_SUBSTANTIVE_LENGTH = 50

# After all topics are covered, we send the completion signal
_COMPLETION_MESSAGE = (
    "INTERVIEW_COMPLETE\n\n"
    "Excellent! I've gathered everything I need. Here's a summary of what we covered:\n\n"
)


def _check_topic_coverage(text: str, topic: Topic) -> bool:
    """Check if the text addresses a topic by scanning for keywords."""
    lower = text.lower()
    matches = sum(1 for kw in topic.keywords if kw.lower() in lower)
    # Require at least 2 keyword matches for coverage
    return matches >= 2


def _is_vague_answer(text: str) -> bool:
    """Check if an answer is too short or vague to be substantive."""
    stripped = text.strip()
    if len(stripped) < _MIN_SUBSTANTIVE_LENGTH:
        return True
    # Check for very generic answers
    vague_patterns = [
        r"^(yes|no|maybe|sure|ok|okay|not sure|i think so|probably|idk|i don't know)\.?$",
        r"^(same as (before|above|usual)|nothing special|standard|typical|normal|default)\.?$",
    ]
    for pattern in vague_patterns:
        if re.match(pattern, stripped.lower()):
            return True
    return False


def _build_coverage_state(messages: list[dict], topics: list[Topic]) -> dict[str, bool]:
    """Build a dict of topic_name -> covered (bool) from all user messages."""
    coverage: dict[str, bool] = {t.name: False for t in topics}
    all_user_text = " ".join(m["content"] for m in messages if m["role"] == "user")

    for topic in topics:
        if _check_topic_coverage(all_user_text, topic):
            coverage[topic.name] = True
    return coverage


async def interview_next(
    messages_json: str, rfc_type: str, user_message: str
) -> tuple[str, str, list[str], int, str | None]:
    """Return (updated_messages, response, topics_covered, topics_total, current_topic).

    The adaptive engine:
    1. Checks if the user's latest answer is vague -> ask a follow-up probe
    2. Scans all user text to determine which topics are already covered
    3. Picks the next uncovered topic
    4. If all topics covered -> send completion signal
    """
    messages = json.loads(messages_json) if messages_json else []
    messages.append({"role": "user", "content": user_message})

    topics = _TOPICS.get(rfc_type, _TOPICS["other"])
    coverage = _build_coverage_state(messages, topics)
    covered_names = [name for name, covered in coverage.items() if covered]
    topics_total = len(topics)

    # Check if the last user answer was vague and we should probe deeper
    # (only if we've already asked at least one question)
    assistant_count = sum(1 for m in messages if m["role"] == "assistant")
    if assistant_count > 0 and _is_vague_answer(user_message):
        # Find the current topic (the last one we asked about)
        last_topic = _find_last_asked_topic(messages, topics)
        if last_topic and last_topic.follow_ups:
            # Pick a follow-up we haven't used yet
            used_follow_ups = {m["content"] for m in messages if m["role"] == "assistant"}
            for fu in last_topic.follow_ups:
                if fu not in used_follow_ups:
                    response = f"I'd like to dig a bit deeper on that. {fu}"
                    messages.append({"role": "assistant", "content": response})
                    return (
                        json.dumps(messages),
                        response,
                        covered_names,
                        topics_total,
                        last_topic.name,
                    )

    # Find next uncovered topic
    next_topic = None
    for topic in topics:
        if not coverage[topic.name]:
            next_topic = topic
            break

    if next_topic is None:
        # All topics covered -- complete the interview
        summary_bullets = "\n".join(f"- **{name}**" for name in coverage)
        response = _COMPLETION_MESSAGE + summary_bullets + (
            "\n\nI'm now generating your RFC sections based on our conversation..."
        )
        messages.append({"role": "assistant", "content": response})
        return (
            json.dumps(messages),
            response,
            covered_names,
            topics_total,
            None,
        )

    # Ask the next topic question with a natural transition
    if assistant_count == 0:
        # First question -- add a warm intro
        response = f"Great, let's build this RFC together! {next_topic.question}"
    else:
        transitions = [
            "Good, that's helpful.",
            "Thanks, I've noted that.",
            "Got it.",
            "That makes sense.",
            "Understood.",
            "Great context.",
        ]
        # Deterministic transition based on question index
        transition = transitions[assistant_count % len(transitions)]
        response = f"{transition} {next_topic.question}"

    messages.append({"role": "assistant", "content": response})
    return (
        json.dumps(messages),
        response,
        covered_names,
        topics_total,
        next_topic.name,
    )


def _find_last_asked_topic(messages: list[dict], topics: list[Topic]) -> Topic | None:
    """Find which topic the last assistant message was about."""
    assistant_msgs = [m for m in messages if m["role"] == "assistant"]
    if not assistant_msgs:
        return None
    last_msg = assistant_msgs[-1]["content"].lower()
    for topic in topics:
        if topic.question.lower()[:40] in last_msg:
            return topic
        # Also check follow-ups
        for fu in topic.follow_ups:
            if fu.lower()[:40] in last_msg:
                return topic
    return None


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
