from typing import Annotated, Union

import jwt
from fastapi import Cookie, HTTPException, status
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError

from core import security
from core.config import settings

# TokenDep2 = Annotated[str, Depends(APIKeyHeader(name="X-Auth"))]
TokenDep2 = Annotated[Union[str, None], Cookie()]


def get_current_user(access_token: TokenDep2) -> None:
    try:
        jwt.decode(access_token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from None
