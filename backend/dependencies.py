from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from supabase.lib.client_options import SyncClientOptions
from .config import get_settings, Settings

security = HTTPBearer()


def get_supabase_client(settings: Settings = Depends(get_settings)) -> Client:
    return create_client(settings.supabase_url, settings.supabase_anon_key)


def get_supabase_admin(settings: Settings = Depends(get_settings)) -> Client:
    key = settings.supabase_service_role_key or settings.supabase_anon_key
    return create_client(settings.supabase_url, key)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    settings: Settings = Depends(get_settings),
) -> dict:
    supabase = create_client(settings.supabase_url, settings.supabase_anon_key)
    try:
        response = supabase.auth.get_user(credentials.credentials)
        if not response or not response.user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return {"id": response.user.id, "email": response.user.email, "token": credentials.credentials}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


def get_supabase_for_user(
    user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> Client:
    """Return a Supabase client that can satisfy RLS for user-scoped routes."""
    if settings.supabase_service_role_key:
        return create_client(settings.supabase_url, settings.supabase_service_role_key)
    options = SyncClientOptions(headers={"Authorization": f"Bearer {user['token']}"})
    return create_client(settings.supabase_url, settings.supabase_anon_key, options=options)
