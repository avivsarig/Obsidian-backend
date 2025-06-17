from fastapi import Request

from app.src.core.auth.exceptions import AuthenticationRequiredError


async def require_api_key(request: Request) -> str:
    if not getattr(request.state, "authenticated", False):
        raise AuthenticationRequiredError("Request not authenticated")

    api_key = getattr(request.state, "api_key", None)
    if not isinstance(api_key, str):
        raise AuthenticationRequiredError("Invalid API key in request state")

    return api_key
