import hmac

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader


api_key_header = APIKeyHeader(
    name="X-API-Key",
    scheme_name="ApiKeyAuth",
    description="API access key configured by the service operator.",
    auto_error=False,
)


async def require_api_key(
    request: Request,
    api_key: str | None = Depends(api_key_header),
) -> None:
    configured_key = (
        request.app.state.settings.api_access_key
        .get_secret_value()
    )

    if not configured_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API access security is not configured.",
        )

    if (
        not api_key
        or not hmac.compare_digest(api_key, configured_key)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
