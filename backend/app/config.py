from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OIDC
    OIDC_ISSUER_URL: str = "http://mock-oidc:10090"
    OIDC_CLIENT_ID: str = "mock-oidc-client"
    OIDC_CLIENT_SECRET: str = "mock-oidc-secret"
    # JWT
    JWT_SECRET: str = "change-me-in-production"
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://ratify:ratify@db:5432/ratify"
    # URLs
    FRONTEND_URL: str = "http://localhost:3100"
    BACKEND_URL: str = "http://localhost:8000"
    # Security
    ENFORCE_SECRETS: bool = False
    # Jira
    JIRA_BASE_URL: str = "http://mock-jira:8543"
    JIRA_AUTH_TOKEN: str = "mock-jira-token"
    # AI
    AI_PROVIDER: str = "anthropic_foundry"
    AI_MODEL_HEAVY: str = "claude-opus-4-6"
    AI_MODEL_STANDARD: str = "claude-sonnet-4-6"
    AI_MODEL_LIGHT: str = "claude-haiku-4-5"
    AZURE_AI_FOUNDRY_ENDPOINT: str = ""
    AZURE_AI_FOUNDRY_API_KEY: str = ""
    # AI Safety
    AI_RATE_LIMIT_REQUESTS_PER_MINUTE: int = 20
    AI_RATE_LIMIT_TOKENS_PER_MINUTE: int = 50000
    AI_MAX_PROMPT_CHARS: int = 100000
    # Activity Log
    LOG_BUFFER_SIZE: int = 10000

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
