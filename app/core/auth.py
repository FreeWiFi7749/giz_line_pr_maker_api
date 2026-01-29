from typing import Optional

import httpx
from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt

from app.core.config import get_settings


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    settings = get_settings()

    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
        )

    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return True


async def verify_cf_access(
    cf_access_jwt_assertion: Optional[str] = Header(None, alias="Cf-Access-Jwt-Assertion"),
) -> dict:
    settings = get_settings()

    if not settings.cf_access_team_domain or not settings.cf_access_audience:
        return {"email": "dev@localhost", "sub": "dev"}

    if not cf_access_jwt_assertion:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cloudflare Access token is required",
        )

    try:
        certs_url = f"https://{settings.cf_access_team_domain}/cdn-cgi/access/certs"
        async with httpx.AsyncClient() as client:
            response = await client.get(certs_url)
            response.raise_for_status()
            certs = response.json()

        public_keys = certs.get("public_certs", [])
        if not public_keys:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No public keys found",
            )

        payload = None
        for key_data in public_keys:
            try:
                payload = jwt.decode(
                    cf_access_jwt_assertion,
                    key_data["cert"],
                    algorithms=["RS256"],
                    audience=settings.cf_access_audience,
                )
                break
            except JWTError:
                continue

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Cloudflare Access token",
            )

        return payload

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify Cloudflare Access token: {str(e)}",
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )


def get_api_key_dependency():
    return Depends(verify_api_key)


def get_cf_access_dependency():
    return Depends(verify_cf_access)
