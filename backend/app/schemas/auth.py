from pydantic import BaseModel


class UserInfo(BaseModel):
    """JWT payload schema -- matches token claims exactly."""

    sub: str
    user_id: str
    email: str
    name: str
    role_id: str
    role_name: str
    permissions: list[str]


class LogoutResponse(BaseModel):
    message: str
