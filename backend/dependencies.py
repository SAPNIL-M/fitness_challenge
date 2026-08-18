from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from services.auth_service import decode_access_token, InvalidTokenError

# HTTPBearer is FastAPI's built-in security scheme for reading an
# "Authorization: Bearer <token>" header. Declaring it here also makes
# Swagger UI (/docs) show an "Authorize" button, letting you paste in
# a token and test protected routes directly from the browser.
bearer_scheme = HTTPBearer(
    scheme_name="AccessToken",
    description="Paste the accessToken returned from /register or /login.",
)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> int:
    """
    FastAPI dependency that verifies the request's access token and
    returns the authenticated user's id.

    Any route that includes this dependency requires a valid
    "Authorization: Bearer <token>" header — FastAPI rejects the
    request with 401 automatically if the header is missing entirely
    (that check happens inside HTTPBearer itself, before this function
    even runs). This function handles the case where a header *is*
    present but the token inside it is invalid or expired.

    Usage:
        async def endpoint(user_id: int = Depends(get_current_user_id)):
            # user_id is guaranteed to be a real, verified userId here
            ...

    Raises:
        HTTPException 401: If the token is missing, expired, malformed,
                           or has an invalid signature.
    """
    token = credentials.credentials

    try:
        return decode_access_token(token)
    except InvalidTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Unauthorized",
                "message": str(error),
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
